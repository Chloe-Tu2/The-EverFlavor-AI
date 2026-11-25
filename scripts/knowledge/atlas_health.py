"""Atlas health, every run: the five measures, the atlas debt per country and region, and release readiness.
Audit only: it reads the latest audit files, changes nothing and marks nothing reviewed.

    python scripts/knowledge/atlas_health.py   # last in the audit chain (after walter_gaps.py, review_impact.py)

Atlas debt is like technical debt, for the atlas: for each country with a dish, one point for each gap
  - only one dish
  - no photo (no verified dish photo and no cuisine photo that passes the rules)
  - no story (no dish with a History or Origin sentence)
  - no dish family
  - no culinary region data (no dish with a culinary region)
  - weak Walter coverage (its dishes answer fewer than 3 of Walter's five questions on average)
Reducing it is often worth more than the next dish. Release readiness reads the gate tables in the planner
(docs/plans/README.md) and the 1.0 targets in atlas_metrics.json.
Writes docs/audits/atlas_health.md and data/knowledge/atlas/atlas_debt.json.
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

from quality_reports import read, save_md, table

KNOW = ROOT / "data" / "knowledge"
PLANNER = ROOT / "docs" / "plans" / "README.md"
DEBTS = ["one dish only", "no photo", "no story", "no family", "no culinary region", "weak Walter"]
LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")   # a Markdown link, kept as its text
TARGETS_1_0 ={"world culinary coverage (%)": 60, "Africa coverage (%)": 50, "Oceania coverage (%)": 35}


def country_debt() -> list[dict]:
    scores = [c for c in read(KNOW / "atlas" / "country_scores.json")["countries"] if c["covered"]]
    walter = {c["country"]: c["score"] for c in read(KNOW / "quality" / "walter_country_scores.json")["countries"]}
    media = read(KNOW / "media" / "country_media_coverage.json")["countries"]
    cuisine = {i["country"] for i in read(KNOW / "media" / "cuisine_image_queue.json")["images"] if i["passes"] == "yes"}
    regions: dict[str, int] = defaultdict(int)
    for line in (KNOW / "dishes.jsonl").open(encoding="utf-8"):
        d = json.loads(line)
        if d.get("kind") == "dish" and (d.get("region") or d.get("regions")):
            regions[d["country"]] += 1
    out = []
    for c in scores:
        name = c["country"]
        gaps = {"one dish only": c["dishes"] == 1,
                "no photo": not media.get(name, {}).get("verified") and name not in cuisine,
                "no story": c["representation_parts"]["stories"] == 0,
                "no family": c["representation_parts"]["families"] == 0,
                "no culinary region": regions.get(name, 0) == 0,
                "weak Walter": walter.get(name, 0) < 3}
        out.append({"country": name, "continent": c["continent"], "subregion": c["subregion"],
                    "dishes": c["dishes"], "debt": sum(gaps.values()), "gaps": [g for g in DEBTS if gaps[g]]})
    return sorted(out, key=lambda r: (-r["debt"], r["dishes"], r["country"]))


def gate_rows(heading: str) -> list[dict]:
    """The condition table that follows a bold version heading in the planner."""
    text = PLANNER.read_text(encoding="utf-8")
    start = text.find(heading)
    if start < 0:
        return []
    rows = []
    for line in text[start:].splitlines()[1:]:
        if line.startswith("**"):
            break
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 4 and cells[0] not in ("Area", "---"):
            rows.append({"area": cells[0], "condition": cells[1], "who": cells[2], "state": cells[3]})
    return rows


def readiness(r: dict) -> str:
    state = r["state"].lower()
    if re.match(r"met\b", state):
        return "done"
    if "after the above" in state:
        return "last step"
    if "waiting" in state or "built" in state or r["who"].lower().startswith("person"):
        return "waiting on a person"
    return "open for Claude"


def main() -> None:
    metrics = read(KNOW / "atlas" / "atlas_metrics.json")
    debt = country_debt()
    total = sum(r["debt"] for r in debt)
    per_gap = {g: sum(g in r["gaps"] for r in debt) for g in DEBTS}
    by_region: dict[str, list[int]] = defaultdict(list)
    for r in debt:
        by_region[f"{r['continent']} / {r['subregion']}"].append(r["debt"])
    regions = sorted(((k, len(v), sum(v), sum(v) / len(v)) for k, v in by_region.items()), key=lambda x: -x[3])
    review_items = sum(1 for line in (ROOT / "docs" / "governance" / "needs_human_review.md").open(encoding="utf-8")
                       if re.match(r"\| \d+ \|", line))
    (KNOW / "atlas" / "atlas_debt.json").write_text(json.dumps(
        {"by": "scripts/knowledge/atlas_health.py", "built_on": date.today().isoformat(), "debts": DEBTS,
         "total": total, "per_gap": per_gap, "countries": debt}, ensure_ascii=False, indent=1), encoding="utf-8")

    today = date.today().isoformat()
    lines = [f"# Atlas health ({today})", "",
             ("The five measures, the atlas debt and release readiness, from `scripts/knowledge/atlas_health.py` "
              f"(metrics built {metrics['generated_at']}). **Audit only.** What to review first: "
              "[review_impact.md](review_impact.md)."), "", "## The five measures", ""]
    for area in ("coverage", "representation", "enrichment", "preservation"):
        lines.append(f"- **{area.capitalize()}:** " + "; ".join(f"{k} {v:,}" if isinstance(v, int) else f"{k} {v}"
                                                               for k, v in metrics[area].items()))
    lines += [(f"- **Governance:** {review_items} review items logged in "
               "[needs_human_review.md](../governance/needs_human_review.md); none closed by Claude."), "",
              "## Atlas debt", "",
              (f"{total} debt points across {len(debt)} countries with a dish (at most {len(DEBTS)} each). One point "
               "per gap: " + ", ".join(DEBTS) + ". Lowering it is the goal, more than adding dishes. "
               "Most countries have no culinary region data only because the place tree has few culinary regions "
               "below country level yet; that gap needs a source for regions first."), ""]
    lines += table(["Gap", "Countries"], [[g, per_gap[g]] for g in DEBTS])
    lines += ["", "### Regions with the most debt per country", ""]
    lines += table(["Region", "Countries", "Debt", "Per country"],
                   [[k, n, s, f"{a:.1f}"] for k, n, s, a in regions[:12]])
    lines += ["", "### Countries with the most debt", "",
              "The full list: `data/knowledge/atlas/atlas_debt.json`.", ""]
    lines += table(["Country", "Dishes", "Debt", "Gaps"],
                   [[r["country"], r["dishes"], r["debt"], ", ".join(r["gaps"])] for r in debt[:30]])
    ready: list[str] = []
    waiting: list[str] = []
    for version, heading in (("0.8.0", "**0.8.0 beta"), ("0.9.0", "**0.9.0 beta")):
        rows = gate_rows(heading)
        count: dict[str, int] = defaultdict(int)
        for r in rows:
            r["condition"] = LINK.sub(r"\1", r["condition"].split(";")[0])
            count[readiness(r)] += 1
            if readiness(r) == "waiting on a person":
                waiting.append(version + ": " + r["condition"])
        ready += [f"### {version}: {count['done']} of {len(rows)} conditions done", ""]
        ready += table(["Area", "Condition", "Readiness"], [[r["area"], r["condition"], readiness(r)] for r in rows])
        ready.append("")
    targets: list[list[object]] = [[k, f">= {t}%", f"{metrics['coverage'][k]}%",
                                    "done" if metrics["coverage"][k] >= t else "open"] for k, t in TARGETS_1_0.items()]
    ready += ["### 1.0.0: coverage targets", ""]
    ready += table(["Target", "Goal", "Now", "Readiness"], targets)
    ready += ["", ("Risks: most open 0.8 and 0.9 conditions wait on people; review time, not data, sets the pace. "
                   "Every other 1.0 target (pages complete, Walter reviewed, no open critical item) waits on the "
                   "reviews above.")]
    lines += ["", "## Release readiness", "", *ready]
    save_md("atlas_health.md", lines)
    save_md("release_readiness.md", [f"# Release readiness ({today})", "",
                                     ("Done, waiting on a person, open for Claude, per release gate in the planner. "
                                      "From `scripts/knowledge/atlas_health.py`."), "", *ready])
    snapshot = {"date": today, "atlas_debt": total, **{f"debt: {g}": n for g, n in per_gap.items()},
                **{k: v for k, v in metrics["coverage"].items() if isinstance(v, (int, float))},
                "review items": review_items}
    previous = record(snapshot)
    handoff(snapshot, previous, waiting, debt, per_gap)
    print(f"debt {total} over {len(debt)} countries; {per_gap}")


HISTORY = KNOW / "atlas" / "atlas_health_history.jsonl"
LOWER_IS_BETTER = ("atlas_debt", "debt: ")
CLAUDE_GAPS = ["no culinary region", "no story", "no family", "weak Walter", "one dish only"]   # photos need a person


def record(snapshot: dict) -> dict:
    """Keep one snapshot per day in the history; return the latest one from an earlier day ({} if none)."""
    old = [json.loads(line) for line in HISTORY.open(encoding="utf-8")] if HISTORY.exists() else []
    old = [s for s in old if s["date"] != snapshot["date"]]
    HISTORY.write_text("".join(json.dumps(s, ensure_ascii=False) + "\n" for s in [*old, snapshot]), encoding="utf-8")
    return old[-1] if old else {}


def handoff(now: dict, before: dict, waiting: list[str], debt: list[dict], per_gap: dict[str, int]) -> None:
    """docs/audits/curator_handoff.md: what improved, regressed, is blocked, needs a person, and what is next."""
    better, worse = [], []
    for k, v in now.items():
        if k == "date" or k not in before or v == before[k]:
            continue
        lower = k.startswith(LOWER_IS_BETTER)
        (better if (v < before[k]) == lower else worse).append(f"{k}: {before[k]} -> {v}")
    impact = (ROOT / "docs" / "audits" / "review_impact.md")
    people = [line.split("|")[2].strip() for line in impact.read_text(encoding="utf-8").splitlines()
              if re.match(r"\| \d+ \|", line)][:3] if impact.exists() else []
    gap = max(CLAUDE_GAPS, key=lambda g: per_gap[g])
    worst = [r["country"] for r in debt if gap in r["gaps"]][:8]
    since = f"since {before['date']}" if before else "first snapshot, nothing to compare yet"
    lines = [f"# Curator handoff ({now['date']})", "",
             ("Read this first in a new session, then [atlas_health.md](atlas_health.md) and "
              "[review_impact.md](review_impact.md). From `scripts/knowledge/atlas_health.py`; the history is in "
              "`data/knowledge/atlas/atlas_health_history.jsonl`. **Audit only.**"), "",
             f"## What improved ({since})", "", *([f"- {x}" for x in better] or ["- nothing measured changed"]), "",
             "## What regressed", "", *([f"- {x}" for x in worse] or ["- nothing"]), "",
             "## What is blocked (waiting on a person)", "", *[f"- {x}" for x in waiting], "",
             "## What needs a person first", "", *[f"- {x}" for x in people], "",
             "## What should happen next (Claude)", "",
             (f"- Quality campaign with the most countries Claude can work on alone: **{gap}** ({per_gap[gap]} "
              f"countries; first {', '.join(worst)})."),
             "- Coverage campaigns in the planner's order, as far as their review items allow.",
             "- End the session by rerunning the audit chain so this page is current."]
    save_md("curator_handoff.md", lines)


if __name__ == "__main__":
    main()
