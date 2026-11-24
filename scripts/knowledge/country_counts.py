"""How many countries does EverFlavor cover? Two counts side by side, and how the number grew sprint by sprint.

    python scripts/knowledge/country_counts.py   # after culinary_coverage.py

- Our coverage count: Unicode CLDR countries and territories of 100,000 people or more (review item 21). It
  includes territories with their own food (Puerto Rico, Guam, Réunion) and leaves out small states.
- The usual count: the 193 UN member states and the 2 observer states (Palestine, Vatican City), 195 in all,
  from Wikidata (member of the United Nations, a sovereign state).

Writes docs/audits/country_counts.md. Audit only: nothing is changed.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

from enrichment_impact import at_ref
from quality_reports import read, save_md, table

KNOW = ROOT / "data" / "knowledge"
# The atlas sprints' merge commits on main (before = the last commit before sprint 1)
MILESTONES = [("before the atlas sprints (v0.7.2)", "d14d0fd"), ("sprint 1: Africa, Pacific, Caribbean", "4382d63"),
              ("sprint 2: Oceania and Indigenous foods", "67a406e"), ("sprint 3: coverage recovery", "0820fb0"),
              ("sprint 4: coverage recovery", "bfbc07b"), ("now (latest run)", None)]


def dish_countries(ref: str | None) -> set[str]:
    return {d["country"] for line in at_ref(ref, "data/knowledge/dishes.jsonl").splitlines() if line.strip()
            for d in [json.loads(line)] if d.get("kind") == "dish"}


def main() -> None:
    cov = read(KNOW / "atlas" / "culinary_coverage.json")
    un = cov["un_states"]
    ours = [c for c in cov["countries"] if c["counted"]]
    have = dish_countries(None)
    our_names = {c["country"] for c in ours}
    members = set(un["member_states"])
    observers = ["Palestine", "Vatican City"]
    standard = members | set(observers)

    lines = [f"# Country counts ({date.today().isoformat()})", "",
             ("How many countries EverFlavor covers depends on what counts as a country. Coverage uses one list (our "
              "count); most atlases use the UN's (the usual count). Both are shown so the numbers can be checked. "
              "From `scripts/knowledge/country_counts.py`; numbers update on every run. **Audit only.**"), "",
             "## The two counts", ""]
    lines += table(["Count", "What it includes", "Places", "With a dish"], [
        ["Our coverage count", "Unicode CLDR countries and territories of 100,000 people or more", len(ours),
         sum(c["country"] in have for c in ours)],
        ["UN member states", "the 193 members", un["members"], un["members_with_a_dish"]],
        ["UN members and observers", "the usual 195: members, Palestine and Vatican City",
         un["members"] + un["observers"], un["members_with_a_dish"] + un["observers_with_a_dish"]]])
    lines += ["", ("Other common totals: 197 (also Kosovo, the Cook Islands and Niue, without Palestine), 198 (also "
                   "Taiwan), 199 (also Western Sahara). The counting rule is review item 21 in "
                   "[needs_human_review.md](../governance/needs_human_review.md)."), ""]

    only_ours = sorted(our_names - standard)
    only_un = sorted(standard - our_names)
    lines += ["## Where the two lists differ", "",
              f"**In our count, not among the 195 ({len(only_ours)}):** territories and partly recognised places (marked when "
              "they have no dish): " +(", ".join(f"{c}{' (no dish)' if c not in have else ''}" for c in only_ours) or "none") + ".",
              "",
              f"**Among the 195, not in our count ({len(only_un)}):** states under 100,000 people (marked when they "
              "have a dish). "
              + (", ".join(f"{c}{' (has a dish)' if c in have else ''}" for c in only_un) or "None") + ".", ""]

    lines += ["## UN member states with no dish yet", "",
              f"{len(un['members_without_a_dish'])} of {un['members']}: " + ", ".join(un["members_without_a_dish"])
              + ".", "", "## How the count grew", ""]
    rows = []
    for label, ref in MILESTONES:
        got = dish_countries(ref)
        rows.append([label, f"`{ref}`" if ref else "working tree", len(got), len(got & members),
                     sum(c["country"] in got for c in ours)])
    lines += table(["When", "Commit", "Countries with a dish (any)", "UN members with a dish",
                    "In our coverage count"], rows)
    lines += ["", ("Sprint 1 read the cuisine pages of 74 more countries; sprint 2 their paragraph links and 'Cuisine "
                   "of X' titles; sprint 3 the cuisine pages of 69 more; sprint 4 the Wikipedia categories of the weak "
                   "and uncovered countries. Each sprint's report is in [sprints/](sprints/).")]
    save_md("country_counts.md", lines)
    print({r[0]: r[2:] for r in rows})


if __name__ == "__main__":
    main()
