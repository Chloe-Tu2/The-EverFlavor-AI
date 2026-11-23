"""Did a fetch improve the atlas? Compares the knowledge files at a git ref (before) with the working tree (now):
countries, dishes, stories, fun facts, families, country pages, Indigenous traditions and world coverage.
Audit only: nothing is changed.

    python scripts/knowledge/enrichment_impact.py [--before d14d0fd] [--label "before the atlas sprints"]

Writes docs/audits/enrichment_impact.md.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

from quality_reports import save_md, table

KNOW = "data/knowledge"
# The last commit before the atlas sprints (PR 43, v0.7.2): the default baseline
BASELINE = "d14d0fd"
GIT = shutil.which("git") or "git"


def at_ref(ref: str | None, path: str) -> str:
    """A file's text at a git ref, or in the working tree when ref is None; "" when it does not exist."""
    if ref is None:
        file = ROOT / path
        return file.read_text(encoding="utf-8") if file.exists() else ""
    done = subprocess.run([GIT, "show", f"{ref}:{path}"], cwd=ROOT, capture_output=True, check=False)  # noqa: S603
    return done.stdout.decode("utf-8") if done.returncode == 0 else ""


def country_pages(ref: str | None) -> int:
    if ref is None:
        return len([p for p in (ROOT / KNOW / "dishes").glob("*.md") if p.name != "README.md"])
    done = subprocess.run([GIT, "ls-tree", "--name-only", f"{ref}:{KNOW}/dishes"], cwd=ROOT,  # noqa: S603
                          capture_output=True,
                          text=True, check=False)
    return len([n for n in done.stdout.split() if n.endswith(".md") and n != "README.md"])


def measure(dishes: list[dict], families: dict, coverage: dict, pages: int, quality: dict) -> dict[str, float]:
    """The atlas numbers for one snapshot."""
    real = [d for d in dishes if d.get("kind") == "dish"]
    per_country = Counter(d["country"] for d in real)
    linked = set(families.get("dish_families", {}))
    tiers = Counter(d.get("tier") for d in quality.get("dishes", []))
    return {
        **{f"{c} coverage (%)": v.get("coverage", 0.0) for c, v in sorted(coverage.get("continents", {}).items())},
        "countries with a story": len({d["country"] for d in real if d.get("story_candidates")}),
        "rich dishes": tiers["rich"], "fair dishes": tiers["fair"], "thin dishes": tiers["thin"],
        "entries (dishes, foods and drinks)": len(dishes),
        "dishes": len(real),
        "countries with a dish": len(per_country),
        "countries with three dishes or more": sum(n >= 3 for n in per_country.values()),
        "country pages": pages,
        "entries with a story (History or Origin sentences)": sum(bool(d.get("story_candidates")) for d in dishes),
        "entries with a fun-fact candidate": sum(bool(d.get("fun_fact_candidates")) for d in dishes),
        "entries with a Wikidata origin": sum(bool(d.get("origin")) for d in dishes),
        "entries with a culinary region": sum(bool(d.get("region")) for d in dishes),
        "dish families and categories": len(families.get("families", [])),
        "entries linked to a family": sum(d.get("qid") in linked for d in dishes),
        "entries with an Indigenous tradition": sum(bool(d.get("traditions")) for d in dishes),
        "Indigenous traditions tracked": len({t for d in dishes for t in d.get("traditions", [])}),
        "world culinary coverage (%)": coverage.get("world", {}).get("coverage", 0.0),
    }


def snapshot(ref: str | None) -> dict[str, float]:
    dishes = [json.loads(line) for line in at_ref(ref, f"{KNOW}/dishes.jsonl").splitlines() if line.strip()]
    families = json.loads(at_ref(ref, f"{KNOW}/dish_families.json") or "{}")
    coverage = json.loads(at_ref(ref, f"{KNOW}/atlas/culinary_coverage.json") or "{}")
    quality = json.loads(at_ref(ref, f"{KNOW}/quality/dish_quality.json") or "{}")
    return measure(dishes, families, coverage, country_pages(ref), quality)


# The four atlas KPIs (med27-coder, 2026-11-23) and preservation; dish counts are secondary
SECTIONS = {
    "coverage": ["world culinary coverage (%)", "Africa coverage (%)", "Americas coverage (%)", "Asia coverage (%)",
                 "Europe coverage (%)", "Oceania coverage (%)", "countries with a dish", "country pages"],
    "representation": ["dish families and categories", "countries with three dishes or more",
                       "countries with a story", "Indigenous traditions tracked"],
    "enrichment": ["entries with a story (History or Origin sentences)", "entries with a Wikidata origin",
                   "entries linked to a family", "entries with a culinary region", "rich dishes", "fair dishes",
                   "thin dishes"],
    "preservation": ["entries with an Indigenous tradition", "Indigenous traditions tracked"],
}


def write_metrics(before: dict[str, float], now: dict[str, float], ref: str) -> None:
    """data/knowledge/atlas/atlas_metrics.json: the KPIs now, and recovery (before -> now) for each."""
    out = {"by": "scripts/knowledge/enrichment_impact.py", "generated_at": date.today().isoformat(),
           "baseline": ref, **{s: {k: now[k] for k in keys} for s, keys in SECTIONS.items()},
           "recovery": {k: {"before": before[k], "now": now[k]} for k in now},
           "not_measured_yet": ["countries with images", "dishes with related dishes", "variants"]}
    (ROOT / KNOW / "atlas" / "atlas_metrics.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                                              encoding="utf-8")


def change(before: float, now: float) -> str:
    diff = round(now - before, 1)
    if not before:
        return f"+{diff:g}" if diff else "0"
    return f"{diff:+g} ({100 * (now - before) / before:+.1f}%)"


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--before", default=BASELINE, help="git ref of the baseline (default: before the sprints)")
    parser.add_argument("--label", default="before the atlas sprints (v0.7.2, PR 43)")
    args = parser.parse_args()
    before, now = snapshot(args.before), snapshot(None)
    lines = [f"# Enrichment impact ({date.today().isoformat()})", "",
             (f"Did the fetches improve the atlas? `scripts/knowledge/enrichment_impact.py` compares the knowledge "
              f"files at `{args.before}` ({args.label}) with today's. A dish with a country, a family and a story "
              "explains more than five names: the rows below count those, not only dishes. **Audit only.**"), ""]
    lines += table(["Measure", "Before", "Now", "Change"],
                   [[k, f"{before[k]:,g}", f"{now[k]:,g}", change(before[k], now[k])] for k in now])
    save_md("enrichment_impact.md", lines)
    write_metrics(before, now, args.before)
    write_chart(before, now)
    update_readme(before, now)


START, END = "<!-- ATLAS_DASHBOARD_START -->", "<!-- ATLAS_DASHBOARD_END -->"
RECOVERY = ["world culinary coverage (%)", "Africa coverage (%)", "Oceania coverage (%)", "countries with a dish",
            "country pages"]


def dashboard(before: dict[str, float], now: dict[str, float]) -> list[str]:
    """The README block: coverage, representation, enrichment, recovery (generated; never edit by hand)."""
    def rows(keys: list[str]) -> list[list[object]]:
        return [[k[0].upper() + k[1:], f"{now[k]:,g}"] for k in keys]
    out = ["## Atlas progress", "",
           (f"Generated by `scripts/knowledge/enrichment_impact.py` on {date.today().isoformat()} from the latest "
            "full run; do not edit by hand. Coverage, not dish count, is the headline "
            "([world_culinary_coverage.md](docs/audits/world_culinary_coverage.md)); before and after: "
            "[enrichment_impact.md](docs/audits/enrichment_impact.md)."), "", "### Coverage", ""]
    out += table(["Measure", "Now"], rows(SECTIONS["coverage"]))
    out += ["", "### Representation", ""]
    out += table(["Measure", "Now"], rows(SECTIONS["representation"]))
    out += ["", "### Enrichment", ""]
    out += table(["Measure", "Now"], rows(SECTIONS["enrichment"] + ["entries with an Indigenous tradition"]))
    out += ["", "### Recovery since the atlas sprints began", ""]
    out += table(["Measure", "Before", "Now"], [[k[0].upper() + k[1:], f"{before[k]:,g}", f"{now[k]:,g}"]
                                               for k in RECOVERY])
    out += ["", "![Coverage recovery](docs/art/coverage_recovery.svg)"]
    return out


def update_readme(before: dict[str, float], now: dict[str, float]) -> None:
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    if START not in text or END not in text:
        print("README has no dashboard markers; skipped")
        return
    head, rest = text.split(START, 1)
    tail = rest.split(END, 1)[1]
    readme.write_text(head + START + "\n\n" + "\n".join(dashboard(before, now)) + "\n\n" + END + tail,
                      encoding="utf-8", newline="\n")


def write_chart(before: dict[str, float], now: dict[str, float]) -> None:
    """docs/art/coverage_recovery.svg: before (grey) and now (the app's warm accent) for the recovery measures,
    each bar scaled to its own larger value, with the numbers written on it (not colour alone)."""
    width, bar, gap = 640, 14, 46
    parts = [(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{gap * len(RECOVERY) + 20}" '
              'font-family="sans-serif" font-size="12"><rect width="100%" height="100%" fill="#ffffff"/>')]
    for i, k in enumerate(RECOVERY):
        y, top = 20 + i * gap, max(before[k], now[k]) or 1
        parts.append(f'<text x="8" y="{y}" fill="#222222">{k[0].upper() + k[1:]}</text>')
        for j, (value, colour, label) in enumerate([(before[k], "#9e9e9e", "before"), (now[k], "#c8553d", "now")]):
            w = 380 * value / top
            parts.append(f'<rect x="200" y="{y - 10 + j * (bar + 2)}" width="{w:.1f}" height="{bar}" fill="{colour}"/>')
            parts.append(f'<text x="{206 + w:.1f}" y="{y + j * (bar + 2)}" fill="#222222">{label} {value:,g}</text>')
    parts.append("</svg>")
    (ROOT / "docs" / "art" / "coverage_recovery.svg").write_text("\n".join(parts) + "\n", encoding="utf-8")
    print({k: (before[k], now[k]) for k in now})


if __name__ == "__main__":
    main()
