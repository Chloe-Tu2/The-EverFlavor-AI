# Publishing rules for new dishes (proposed, 2026-11-21)

How a dish enters EverFlavor. No dish is added automatically: the coverage audit only sorts candidates, and a
person adds them. Proposed by Claude (AI) from the team's brief; the team approves or changes these rules, and the
decision goes in `docs/flag_review/flag_policies.csv` like every other judgment call.

## The rules every new dish must pass

1. **It exists in a source.** Wikidata, Wikipedia or a licensed dataset we already use. The dish's Wikidata item
   (QID) is its id. No dish is written from memory or by an AI model.
2. **The licence fits.** Wikidata facts are CC0; Wikipedia text is CC BY-SA 4.0 and is credited "Wikipedia
   contributors" with the article link. Sources whose licence is unclear (TheMealDB photos) are not used.
3. **It has a place in the tree.** At least World > zone > country (`data/reference/food_taxonomy.csv`). A
   country that is not in the tree yet is added first, as its own reviewed change.
4. **It has a country.** The country of origin from Wikidata (P495), or the country of the cuisine list it comes
   from. A region, city or former state (Korea, the Ottoman Empire, Bavaria) needs a person to place it.
5. **It has a family, or "unknown".** The Wikidata family from notebook 15 when there is one; "unknown" is
   allowed. A family is never guessed.
6. **Provenance is recorded.** Every source with its link, licence and retrieval date, as `dishes.jsonl` and
   `expansion_backlog.json` already record them.
7. **A recipe is never invented.** A dish without a recipe in our data is published as a **knowledge-only dish**:
   its facts, family and places, no recipe.

## The approval states

`data/knowledge/coverage/expansion_backlog.json` gives every candidate one of three states:

| State | Means | Rule |
|---|---|---|
| `ready` | Can be added after a quick look | Has a country in the place tree, a family and an English Wikipedia article; in 3 families at most |
| `needs_review` | A person decides first | The country is not in the tree, or is not one of today's countries; no Wikipedia article; or in more than 3 families |
| `blocked` | Not published | No country of origin on Wikidata (rule 4) |

"Ready" is the audit's sorting, not a publication: the dish still goes into the knowledge notebook the way its
other dishes did (its Wikipedia intro and Wikidata facts, as `scripts/knowledge/fetch_knowledge.py` collects
them; today that script reads whole cuisine lists, so taking single dishes is a change to make first), and its
facts stay `reviewed: false` until a person tidies them.

## The steps

1. Pick from `next_500.json` (or the backlog) by country.
2. Check the dish's Wikidata item and article (rules 1, 2, 4 and 5).
3. Add its country to the place tree if needed (rule 3).
4. Add it to the knowledge notebook; rerun notebook 15 and the coverage audit, so the numbers move.
5. Record who checked it (`reviewed_by`).
