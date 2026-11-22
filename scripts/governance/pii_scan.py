"""PII scan: the tracked text files (docs, data, notebooks, reports, code) read for e-mail addresses, phone numbers,
street addresses and GPS coordinates, and the folders that must never be tracked checked to be empty in git.

Most hits need a person's judgment, not a deletion: a shop's public phone from OpenStreetMap or an author named
for a photo credit is allowed; a private person's address is not. So this writes a report and changes nothing.

    python scripts/governance/pii_scan.py    # docs/governance/pii_audit_report.md

Values are masked in the report (an e-mail keeps its first letter and its domain).
"""
from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

from secret_scan import BINARY, MAX_BYTES, tracked

REPORT = ROOT / "docs" / "governance" / "pii_audit_report.md"
RULES = [
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("phone number", re.compile(r"(?<![\w.])(?:\+\d{1,3}[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?![\w.])")),
    ("street address", re.compile(r"\b\d{2,5} [A-Z][a-z]+(?: [A-Z][a-z]+)? (?:St|Street|Ave|Avenue|Rd|Road|Blvd|"
                                  r"Boulevard|Dr|Drive|Ln|Lane|Way|Pkwy|Parkway)\b")),
    ("GPS coordinates", re.compile(r"(?<![\d.])-?\d{1,2}\.\d{4,},\s*-?\d{1,3}\.\d{4,}(?![\d.])")),
]
# Addresses that are not a person's: GitHub's no-reply form, reserved example domains, the licence's own contact
NOT_PERSONAL = re.compile(r"(?i)@users\.noreply\.github\.com$|@(?:[\w-]+\.)*(?:example|test|invalid|localhost)"
                          r"(?:\.\w+)?$|^noreply@|^git@github\.com$|@anthropic\.com$")
NEVER_TRACKED = ("data/user/", "logs/", "config/.env")   # config/.env.example, the template, is meant to be tracked


def mask(kind: str, value: str) -> str:
    if kind == "email":
        user, _, domain = value.partition("@")
        return f"{user[:1]}***@{domain}"
    return value[:3] + "*" * max(0, len(value) - 3)


def scan_text(text: str) -> list[tuple[str, str]]:
    """(kind, value) for every hit that is not a known non-personal address."""
    out = []
    for kind, rx in RULES:
        for m in rx.finditer(text):
            if kind == "email" and NOT_PERSONAL.search(m.group(0)):
                continue
            out.append((kind, m.group(0)))
    return out


def area(path: str) -> str:
    top = path.split("/")[0]
    return {"docs": "docs", "data": "data", "notebooks": "notebooks", "src": "code", "app": "code",
            "scripts": "code", "tests": "tests"}.get(top, "other")


def main() -> None:
    files = tracked()
    hits: dict[str, Counter] = defaultdict(Counter)
    examples: dict[tuple[str, str], set[str]] = defaultdict(set)
    scanned = 0
    for path in files:
        p = ROOT / path
        if p.suffix.lower() in BINARY or not p.is_file() or p.stat().st_size > MAX_BYTES:
            continue
        scanned += 1
        for kind, value in scan_text(p.read_text(encoding="utf-8", errors="replace")):
            hits[path][kind] += 1
            if len(examples[(path, kind)]) < 3:
                examples[(path, kind)].add(mask(kind, value))
    never = [f for f in files if f.startswith(NEVER_TRACKED) and not f.endswith(".env.example")]
    by_kind = Counter()
    for c in hits.values():
        by_kind.update(c)
    lines = [f"# PII audit ({date.today().isoformat()})", "",
             (f"`scripts/governance/pii_scan.py` read {scanned:,} tracked text files for e-mail addresses, phone "
              "numbers, street addresses and GPS coordinates. Values are masked. Nothing was changed: each hit "
              "below needs a person to decide whether it is public (a shop's listed phone, a credited author) or "
              "personal. Binary tables (parquet) are not read here; their columns are described in "
              "`docs/data_dictionary.md`."), "",
             "## Folders that must never be in git", "",
             (f"Tracked files under {', '.join(f'`{n}`' for n in NEVER_TRACKED)}: "
              + (", ".join(never) if never else "none.")), "",
             "## Hits by kind", ""]
    lines += [f"- {k}: {n:,}" for k, n in by_kind.most_common()] or ["None."]
    lines += ["", "## Hits by file (for review)", "",
              "| File | Area | Kind | Hits | Examples (masked) |", "|---|---|---|---:|---|"]
    for path in sorted(hits, key=lambda p: -sum(hits[p].values())):
        for kind, n in hits[path].most_common():
            ex = ", ".join(f"`{e}`" for e in sorted(examples[(path, kind)]))
            lines.append(f"| `{path}` | {area(path)} | {kind} | {n:,} | {ex} |")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"pii scan: {scanned} files; {dict(by_kind)}; never-tracked files in git: {len(never)}")


if __name__ == "__main__":
    main()
