"""Repository hygiene audit: tracked files that look temporary, debug, scratch, drafts or internal notes, big or
empty files, and reports whose date is older than the newest run. Nothing is moved or deleted; a person decides.

    python scripts/governance/hygiene_audit.py   # docs/governance/repository_hygiene_report.md
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

from secret_scan import tracked

REPORT = ROOT / "docs" / "governance" / "repository_hygiene_report.md"
# What a file's path says about it: (kind, pattern on the path, what a person checks)
NAME_RULES = [
    ("temporary", re.compile(r"(?i)(^|/)(tmp|temp)[_./-]|\.tmp$|\.bak$|~$|\.orig$|\.swp$"), "delete if unused"),
    ("debug", re.compile(r"(?i)(^|/)debug[_./-]|_debug\.|\.log$"), "delete or move out of git"),
    ("scratch", re.compile(r"(?i)(^|/)(scratch|playground|untitled)[^/]*"), "delete if unused"),
    ("copy", re.compile(r"(?i)( - copy|\(\d\)|_copy\.|_old\.|_new\.)"), "keep one version"),
    ("internal note", re.compile(r"(?i)(^|/)(notes?|todo|wip)[_.-][^/]*$"), "move to docs/plans/local/ if private"),
    ("draft or archive", re.compile(r"(?i)(^|/)(drafts?|archive)/|_draft\."), "kept on purpose? say so in its folder README"),
]
DATED = re.compile(r"^# .*\((20\d\d-\d\d-\d\d)\)", re.MULTILINE)
BIG = 5_000_000


def audit() -> dict[str, list[tuple[str, str]]]:
    """Findings by kind: (path, detail). A file can appear under more than one kind."""
    found: dict[str, list[tuple[str, str]]] = defaultdict(list)
    dates: dict[str, str] = {}
    for f in tracked():
        p = ROOT / f
        if not p.is_file():
            continue
        for kind, rule, todo in NAME_RULES:
            if rule.search(f) and not f.endswith("README.md"):
                found[kind].append((f, todo))
        size = p.stat().st_size
        if size >= BIG:
            found["big file"].append((f, f"{size / 1e6:.1f} MB"))
        if size == 0 and not f.endswith((".gitkeep", "__init__.py", "py.typed")):
            found["empty file"].append((f, "0 bytes"))
        if f.endswith(".md") and f.startswith(("docs/audits/", "docs/governance/")):
            m = DATED.search(p.read_text(encoding="utf-8", errors="replace")[:400])
            if m:
                dates[f] = m.group(1)
    if dates:
        newest = max(dates.values())
        for f, d in sorted(dates.items()):
            if d < newest:
                found["stale report"].append((f, f"dated {d}; newest report {newest}: rerun or mark as a snapshot"))
    return found


def main() -> None:
    found = audit()
    files = len(tracked())
    lines = [f"# Repository hygiene ({date.today().isoformat()})", "",
             (f"`scripts/governance/hygiene_audit.py` read the names, sizes and report dates of the {files:,} tracked "
              "files. **Nothing was moved or deleted:** each row is for a person to keep, move or remove."), "",
             "| Kind | Files |", "|---|---:|"]
    kinds = [k for k, _, _ in NAME_RULES] + ["big file", "empty file", "stale report"]
    lines += [f"| {k} | {len(found.get(k, []))} |" for k in kinds]
    for k in kinds:
        rows = found.get(k, [])
        lines += ["", f"## {k[0].upper() + k[1:]}", ""]
        if not rows:
            lines += ["None."]
            continue
        groups: dict[str, list[str]] = defaultdict(list)
        for f, detail in rows:
            groups["/".join(f.split("/")[:4]) if k == "draft or archive" else f].append(detail)
        if k == "draft or archive":
            lines += [f"- `{g}`: a draft" if g.endswith(".md") else f"- `{g}/`: {len(v)} files"
                      for g, v in sorted(groups.items())]
        else:
            lines += [f"- `{g}`: {v[0]}" for g, v in sorted(groups.items())]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"hygiene: {files} files, " + ", ".join(f"{k} {len(v)}" for k, v in found.items()))


if __name__ == "__main__":
    main()
