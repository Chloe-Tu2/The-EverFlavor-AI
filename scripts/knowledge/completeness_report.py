"""The dish completeness report: how many dishes are rich, fair or thin today, how many would move up once the
approved images are fetched and pass the photo check, and what still keeps the rest from rich.

    python scripts/knowledge/completeness_report.py   # docs/audits/dish_completeness_report.md

Reads the completeness score (`quality_reports.py`, the team's weights), the media audit and the approved image
queue (`image_queue.py`). A projection, not a change: no image is fetched and no score is written back.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

from quality_reports import PARTS  # each part's meaning and the source that fills it

KNOW = ROOT / "data" / "knowledge"
DOC = ROOT / "docs" / "audits" / "dish_completeness_report.md"
DISH_PHOTO = 0.9      # a Commons photo of the dish itself counts 90% of the image weight (media_audit levels)


def tier(score: float, tiers: dict[str, int]) -> str:
    return next(name for name, low in sorted(tiers.items(), key=lambda x: -x[1]) if score >= low)


def main() -> None:
    quality = json.loads((KNOW / "quality" / "dish_quality.json").read_text(encoding="utf-8"))
    media = {d["dish_id"]: d for d in json.loads((KNOW / "media" / "dish_media_audit.json").read_text(
        encoding="utf-8"))["dishes"]}
    queue = json.loads((KNOW / "media" / "approved_image_queue.json").read_text(encoding="utf-8"))
    approved = {d["dish_id"] for d in queue["dishes"]}
    tiers, weight = dict(quality["tiers"]), quality["weights"]["image"]
    dishes = quality["dishes"]
    now = Counter(d["tier"] for d in dishes)
    after, moved = Counter(), []
    for d in dishes:
        score = d["score"]
        if d["qid"] in approved:
            current = media.get(d["qid"], {}).get("coverage_score", 0) / 100
            score = round(d["score"] + weight * (max(current, DISH_PHOTO) - current))
        t = tier(score, tiers)
        after[t] += 1
        if t != d["tier"]:
            moved.append((d["name"], d["country"], d["tier"], t, d["score"], score))
    short = [d for d in dishes if d["tier"] != "rich"]
    missing = Counter(p for d in short for p in d["missing"])
    n = len(dishes)
    lines = [f"# Dish completeness ({date.today().isoformat()})", "",
             (f"How complete our {n:,} dishes are, by the completeness score (0-100, the team's weights; full detail "
              "per part in [dish_quality_report.md](dish_quality_report.md)), and what would move them up. Nothing "
              "here changes a dish: the second column is a projection."), "",
             "| Tier | Today | With the approved images | Change |", "|---|---:|---:|---:|"]
    lines += [f"| {t} (from {tiers[t]}) | {now[t]:,} ({now[t] / n:.0%}) | {after[t]:,} ({after[t] / n:.0%}) | "
              f"{after[t] - now[t]:+,} |" for t in sorted(tiers, key=lambda t: -tiers[t])]
    up = Counter((m[2], m[3]) for m in moved)
    lines += ["", "## The approved images", "",
              (f"{queue['approved']:,} of {queue['asked']:,} Wikidata images pass the photo pipeline's licence and "
               "credit rules (`data/knowledge/media/approved_image_queue.json`; see "
               "[image_coverage_report.md](image_coverage_report.md)). Fetched and checked by eye, each would show "
               f"a photo of the dish itself ({DISH_PHOTO:.0%} of the image weight) instead of a family photo or the "
               f"placeholder. {len(moved):,} dishes would change tier:"), ""]
    lines += [f"- {a} to {b}: {c:,}" for (a, b), c in up.most_common()]
    rich = [f"{m[0]} ({m[4]} to {m[5]})" for m in sorted(moved, key=lambda m: (-m[5], m[0])) if m[3] == "rich"]
    lines += ["", f"Examples of dishes that would become rich: {', '.join(rich[:15])}.", "",
              "## What keeps the others from rich", "",
              f"Of the {len(short):,} dishes below rich, the parts they lack most (a dish can lack several):", "",
              "| Part | Dishes without it | Where it would come from |", "|---|---:|---|"]
    lines += [f"| {PARTS.get(p, (p, ''))[0]} | {c:,} | {PARTS.get(p, ('', ''))[1]} |"
              for p, c in missing.most_common()]
    lines += ["", ("Every source in the last column is one we already use. A part with no source on our side "
                   "(Wikidata itself, a licensed recipe, a person's pronunciation) stays missing rather than "
                   "written by us.")]
    DOC.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"now {dict(now)}; with approved images {dict(after)}; {len(moved)} move")


if __name__ == "__main__":
    main()
