"""Secret scan: every file git tracks, read for API keys, tokens, passwords and connection strings.

The pre-commit hook and .gitignore stop secret *files* (.env, key files, user data); this reads what is *inside*
the tracked files. A finding is shown redacted (its first 4 characters and its length), never in full. A known
false positive goes in config/secret_scan_allow.txt (file path, the rule, and why), never silently skipped.

    python scripts/governance/secret_scan.py            # exit 1 when anything is found
    python scripts/governance/secret_scan.py --report   # also writes docs/governance/secret_scan_report.md

CI runs it on every push and pull request (.github/workflows/security.yml), and so does the test suite.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ALLOW = ROOT / "config" / "secret_scan_allow.txt"
REPORT = ROOT / "docs" / "governance" / "secret_scan_report.md"
MAX_BYTES = 5_000_000          # bigger tracked files are data tables, scanned only by their names
BINARY = {".parquet", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".gz", ".pkl", ".joblib",
          ".npy", ".ttf", ".woff", ".woff2", ".mp3", ".wav", ".mp4"}

# (rule, pattern): well-known key shapes first, then assignments of a long literal to a secret-sounding name
RULES = [
    ("Anthropic API key", r"sk-ant-[A-Za-z0-9_\-]{20,}"),
    ("OpenAI API key", r"sk-(?:proj-|svcacct-)?[A-Za-z0-9_\-]{32,}"),
    ("Google API key", r"AIza[0-9A-Za-z_\-]{35}"),
    ("AWS access key id", r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    ("AWS secret access key", r"(?i)aws_secret_access_key\s*[=:]\s*['\"]?[A-Za-z0-9/+]{40}"),
    ("Azure storage key", r"(?i)AccountKey=[A-Za-z0-9+/]{60,}={0,2}"),
    ("GitHub token", r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b|\bgithub_pat_[A-Za-z0-9_]{60,}"),
    ("Slack token", r"\bxox[abprs]-[A-Za-z0-9-]{10,}"),
    ("Hugging Face token", r"\bhf_[A-Za-z0-9]{34}\b"),
    ("Kaggle key", r"(?i)\"key\"\s*:\s*\"[0-9a-f]{32}\""),
    ("private key", r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"),
    ("JWT", r"\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"),
    ("password in a connection string", r"\b[a-z][a-z0-9+.\-]*://[^\s:/@'\"]+:[^\s:/@'\"]{3,}@[^\s'\"]+"),
    ("secret assigned in code", (r"(?i)\b[\w-]*(?:api[_-]?key|secret|password|passwd|token|client[_-]?secret|"
                                r"cookie)[\w-]*\s*[=:]\s*['\"][^'\"\s]{16,}['\"]")),
]
COMPILED = [(name, re.compile(rx)) for name, rx in RULES]
# Values that are clearly placeholders, not secrets
PLACEHOLDER = re.compile(r"(?i)(your[_-]?|example|placeholder|xxxx|\.\.\.|<[^>]+>|\$\{|os\.environ|getenv|"
                         r"redacted|dummy|changeme|test[_-]?key|fake)")


def tracked() -> list[str]:
    git = shutil.which("git") or "git"
    out = subprocess.run([git, "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True)  # noqa: S603
    return [p for p in out.stdout.decode("utf-8", "replace").split("\0") if p]


def allowed() -> set[tuple[str, str]]:
    if not ALLOW.exists():
        return set()
    rows = set()
    for line in ALLOW.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            path, rule, *_ = [x.strip() for x in line.split("|")]
            rows.add((path, rule))
    return rows


def redact(value: str) -> str:
    return f"{value[:4]}... ({len(value)} characters)"


def scan_text(text: str) -> list[tuple[str, int, str]]:
    """(rule, line number, redacted value) for every match in one file's text that is not a placeholder."""
    found = []
    for n, line in enumerate(text.splitlines(), 1):
        for name, rx in COMPILED:
            for m in rx.finditer(line):
                if not PLACEHOLDER.search(m.group(0)):
                    found.append((name, n, redact(m.group(0))))
    return found


def scan() -> tuple[list[dict], int]:
    skip, findings, files = allowed(), [], 0
    for path in tracked():
        p = ROOT / path
        if p.suffix.lower() in BINARY or not p.is_file() or p.stat().st_size > MAX_BYTES:
            continue
        files += 1
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for rule, line, value in scan_text(text):
            if (path, rule) not in skip:
                findings.append({"file": path, "line": line, "rule": rule, "value": value})
    return findings, files


def write_report(findings: list[dict], files: int) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# Secret scan ({date.today().isoformat()})", "",
             (f"`scripts/governance/secret_scan.py` read {files:,} tracked text files for {len(RULES)} kinds of secret "
              "(API keys for Anthropic, OpenAI, Google, AWS, Azure, GitHub, Slack, Hugging Face and Kaggle, private "
              "keys, JWTs, passwords in connection strings, and long values assigned to names like `api_key`, "
              "`secret`, `password`, `token` or `cookie`). Values are shown redacted."), "",
             f"**Result: {len(findings)} finding{'s' if len(findings) != 1 else ''}.**", ""]
    if findings:
        lines += ["| File | Line | Kind | Value (redacted) |", "|---|---:|---|---|"]
        lines += [f"| `{f['file']}` | {f['line']} | {f['rule']} | `{f['value']}` |" for f in findings]
    allow = sorted(allowed())
    lines += ["", "## Allowed (known false positives)", "",
              (f"{len(allow)} entries in `config/secret_scan_allow.txt`, each with its reason."
               if allow else "None.")]
    lines += ["", "## What else guards secrets", "",
              "- `.gitignore` keeps `config/.env`, key files, `data/user/` and `logs/` out of git.",
              "- The git pre-commit hook (`.claude/hooks/precommit_secrets.py`) refuses a commit that stages them.",
              "- This scan runs in CI on every push and pull request and fails the run on any finding."]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    findings, files = scan()
    if "--report" in sys.argv:
        write_report(findings, files)
    for f in findings:
        print(f"{f['file']}:{f['line']}: {f['rule']}: {f['value']}")
    print(f"secret scan: {files} files, {len(findings)} findings")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
