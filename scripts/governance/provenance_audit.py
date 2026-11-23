"""Data provenance audit: does every tracked data file in data/knowledge/ and data/reference/ say where it comes
from, under which licence, and when it was made or retrieved?

A JSON file can say it itself (keys such as `source`, `sources`, `about`, `licence`, `retrieved`, `built_on`); a
CSV or Markdown file cannot, so it counts as documented when a README of its folder (or a parent folder) or
`docs/sources.md` names it. Nothing is changed; gaps go in the report for a person.

    python scripts/governance/provenance_audit.py   # docs/governance/data_provenance_report.md
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

from secret_scan import tracked

REPORT = ROOT / "docs" / "governance" / "data_provenance_report.md"
FOLDERS = ("data/knowledge/", "data/reference/")
SOURCE_KEYS = {"source", "sources", "about", "by"}
LICENCE = re.compile(r"(?i)licen[cs]e|cc0|cc by|public domain|odbl|unicode license|wikidata|wikipedia")
DATE_KEYS = {"retrieved", "built_on", "retrieved_date", "queried", "date", "built"}
DATE = re.compile(r"\b20\d\d-\d\d-\d\d\b")
# The stricter fields: a version (of the file or the upstream release) and what credit the licence asks for
VERSION = re.compile(r"(?i)\bversion\b|\bv\d+(\.\d+)*\b|\brelease\b|\bsnapshot\b|\bdump\b|\b20\d\d-\d\d-\d\d\b")
ATTRIBUTION = re.compile(r"(?i)credit|attribut|cc by|by-sa|cc0|public domain|no credit")


def strict(text: str) -> dict[str, bool]:
    """Licence, version and attribution as the text about one file states them."""
    return {"licence_named": bool(LICENCE.search(text)), "version": bool(VERSION.search(text)),
            "attribution": bool(ATTRIBUTION.search(text))}


def doc_lines(name: str, docs: dict[str, str]) -> str:
    """Every line of the docs that names the file."""
    return "\n".join(line for text in docs.values() for line in text.splitlines() if name in line)


def json_fields(path: Path) -> dict[str, bool]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"source": False, "licence": False, "date": False}
    if not isinstance(data, dict):
        return {"source": False, "licence": False, "date": False}
    head = {k: v for k, v in data.items() if not isinstance(v, (list, dict)) or k in SOURCE_KEYS | DATE_KEYS}
    text = json.dumps(head, ensure_ascii=False)
    return {"source": bool(SOURCE_KEYS & set(data)), "licence": bool(LICENCE.search(text)),
            "date": bool(DATE_KEYS & set(data)) or bool(DATE.search(text))}


def head_text(path: Path) -> str:
    """The top-level text fields of a JSON file (not its rows)."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    if not isinstance(data, dict):
        return ""
    return json.dumps({k: v for k, v in data.items() if not isinstance(v, list) and k not in {"dishes", "countries"}},
                      ensure_ascii=False)[:20000]


def documented(path: str, docs: dict[str, str]) -> bool:
    name = Path(path).name
    parents = [str(Path(path).parent / "README.md").replace("\\", "/")]
    parents += [str(p / "README.md").replace("\\", "/") for p in Path(path).parents]
    return any(name in docs.get(d, "") for d in [*parents, "docs/sources.md"])


def audit() -> list[dict]:
    """One row per tracked data file: what it records about itself, whether a doc names it, and if that is enough."""
    files = [f for f in tracked() if f.startswith(FOLDERS) and not f.endswith("README.md")]
    docs = {f: (ROOT / f).read_text(encoding="utf-8", errors="replace") for f in tracked()
            if f.endswith("README.md") or f == "docs/sources.md"}
    rows = []
    for f in sorted(files):
        p = ROOT / f
        named = documented(f, docs)
        about = doc_lines(p.name, docs)
        if p.suffix == ".json":
            got = json_fields(p)
            ok = (got["source"] and got["date"]) or named
            about += "\n" + head_text(p)
        else:
            got = {"source": named, "licence": named, "date": named}
            ok = named
            about += "\n" + p.read_text(encoding="utf-8", errors="replace")[:3000]
        about += "\n" + doc_lines(f"{p.parent.name}/", docs)
        rows.append({"file": f, **got, "named_in_docs": named, "ok": ok, **strict(about)})
    return rows


def main() -> None:
    rows = audit()
    gaps = [r for r in rows if not r["ok"]]
    mark = {True: "yes", False: "**no**"}
    lines = [f"# Data provenance ({date.today().isoformat()})", "",
             (f"`scripts/governance/provenance_audit.py` checked {len(rows)} tracked data files in "
              f"{' and '.join(f'`{d}`' for d in FOLDERS)}: does each say its source, licence and date, in the file "
              "(JSON) or in a README or `docs/sources.md` that names it? "
              f"**{len(rows) - len(gaps)} do; {len(gaps)} need a person.** Nothing was changed."), "",
             "## Files that need their provenance written down", ""]
    lines += ([f"- `{r['file']}`" for r in gaps] or ["None."])
    strict_keys = {"licence_named": "a licence named", "version": "a version or release date",
                   "attribution": "the credit its licence asks for"}
    lines += ["", "## The stricter check: licence, version and attribution, file by file", "",
              ("Each file, or a docs line that names it, should also state its licence, a version (of the file or the "
               "upstream release) and the credit the licence asks for (CC0 and public domain ask none). A file can be "
               "documented above and still miss these, because its folder README covers it as a group. "
               "**Flagged, not repaired:** a person writes the missing fields."), "",
              "| Field | Files that state it | Missing |", "|---|---:|---:|"]
    lines += [f"| {d} | {sum(r[k] for r in rows)} | {sum(not r[k] for r in rows)} |" for k, d in strict_keys.items()]
    lines += ["", "## Every file", "",
              "| File | Source in file | Licence | Date | Named in docs | Documented | Licence named | Version | Attribution |",
              "|---|---|---|---|---|---|---|---|---|"]
    lines += [f"| `{r['file']}` | {mark[r['source']]} | {mark[r['licence']]} | {mark[r['date']]} | "
              f"{mark[r['named_in_docs']]} | {mark[r['ok']]} | {mark[r['licence_named']]} | {mark[r['version']]} | "
              f"{mark[r['attribution']]} |" for r in rows]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"provenance: {len(rows)} files, {len(gaps)} gaps; strict missing: "
          + ", ".join(f"{k} {sum(not r[k] for r in rows)}" for k in strict_keys))


if __name__ == "__main__":
    main()
