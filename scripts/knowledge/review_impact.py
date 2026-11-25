"""Which person decisions unblock the most: every open review item and review sheet, with what it unblocks
(coverage, countries, Walter, images, region pages, a release gate), so review time goes where it counts.
A suggested order only: it answers nothing and marks nothing reviewed.

    python scripts/knowledge/review_impact.py   # after empty_country_packets.py and walter_gaps.py

Counts are read from the latest audit files. Writes docs/audits/review_impact.md.
"""
from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KNOW = ROOT / "data" / "knowledge"
GATE_WEIGHT = {"debt": 4, "0.8": 3, "0.9": 2, "1.0": 1, "": 0}   # debt first while the rule is on (scoreboard)


def rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def pending(path: Path, column: str = "verdict") -> int:
    return sum(not r.get(column, "").strip() for r in rows(path))


def main() -> None:
    packets = rows(KNOW / "review" / "empty_country_packets.csv")
    packet_countries = len({r["country"] for r in packets})
    regions = len(list((KNOW / "atlas" / "regions").glob("*.json")))
    graph = json.loads((KNOW / "quality" / "food_graph_validation.json").read_text(encoding="utf-8"))
    outside = len(graph["dishes_listed_outside_their_origin"])
    review = KNOW / "review"
    # (what, gate, unblocks, size, minutes a person needs, roughly)
    items = [
        ("Item 32: multi-origin dish policy (one rule for shared dishes)", "1.0",
         f"coverage: up to {packet_countries} empty UN members gain a dish ({len(packets)} dishes)", 30),
        ("Item 21: coverage counting rule and weights", "0.8", "coverage shown in the app (a 0.8 condition)", 15),
        ("Items 24, 28, 29, 30: sprint moves, country scores, sprint 4 entries", "0.8",
         "one 0.8 condition; about 25 named dishes to confirm", 45),
        ("Photo contact sheets 37 to 108", "0.8", "about 203 dishes get a photo (a 0.8 condition)", 90),
        ("Cuisine photo fallbacks", "0.8",
         (f"{pending(review / 'cuisine_images.csv')} of {len(rows(review / 'cuisine_images.csv'))} rows open; "
          "a fallback photo for every dish of a country (a 0.8 condition); start with the 'likely wrong' rows"), 40),
        ("Item 25: region pages against Wikidata's origin", "1.0",
         f"246 region-page dishes ({outside} graph entries sit outside their origin in all); country pages, Walter's origin answer",
         30),
        ("Item 26 and the Indigenous tag sheet", "0.9",
         f"{pending(review / 'indigenous_tags.csv')} tags open; Indigenous knowledge in the app (a 0.9 condition)", 60),
        ("Item 27: representative dishes on region pages", "0.9",
         f"{regions} region pages shown in the app (a 0.9 condition)", 15),
        ("Fact review sheet (focus_review_priority.csv order)", "0.9",
         f"{pending(review / 'focus_review.csv')} rows open; 100 reviewed facts are a 0.9 condition", 120),
        ("Item 33 follow-up: the disputed regions and a check of the linked ones", "debt",
         "regional data for the countries the linked Wikidata regions reach", 20),
        ("Item 22: place-tree placements of 59 countries", "1.0", "region pages and coverage by region", 20),
        ("Item 31: Taiwan, Hong Kong and Macau", "1.0", "1 country node; the counting rule's wording", 5),
    ]
    ranked = sorted(items, key=lambda x: (-GATE_WEIGHT[x[1]], x[3]))
    lines = [f"# Review impact ({date.today().isoformat()})", "",
             ("What each open person decision unblocks, release gates first and the quickest first within a gate. "
              "From `scripts/knowledge/review_impact.py`; the minutes are rough guesses. **A suggested order only:** "
              "nothing is answered or marked reviewed. The items are in "
              "[needs_human_review.md](../governance/needs_human_review.md)."), "",
             "| Order | Decision | Gate | Unblocks | Minutes, roughly |", "|---:|---|---|---|---:|"]
    lines += [f"| {i} | {what} | {gate or 'none'} | {unblocks} | {mins} |"
              for i, (what, gate, unblocks, mins) in enumerate(ranked, start=1)]
    (ROOT / "docs" / "audits" / "review_impact.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(ranked)} decisions ranked; {sum(m for *_, m in ranked)} minutes in all, roughly")


if __name__ == "__main__":
    main()
