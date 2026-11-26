# Coverage evidence tiers

Proposed by med27-coder, 2026-11-25: how strong the evidence must be before a dish counts for a country. **Status:
proposed, not applied.** The column "today" says what the fetch does now (`scripts/knowledge/fetch_knowledge.py`,
`scripts/knowledge/dish_origins.py`); where a tier would change it, the change waits for a person.

| Tier | Meaning | Evidence | Today |
|---|---|---|---|
| 1 | strongest; accepted | Wikidata's country of origin (P495); the dish's own intro names the country ("Mansaf is the national dish of Jordan"); several independent sources agree | used: either one keeps a dish found only in a category or a paragraph (`claims_country`); P495 also adds countries under the [multi-origin dish policy](multi_origin_dish_policy.md) |
| 2 | accepted unless contradicted | a cuisine page lists the dish; a country cuisine category; a regional cuisine page | a list or table row on a cuisine page sets the country; a region page sets it even against Wikidata's origin (item 25, open); a category alone is **stricter** than this tier today: kept only with tier 1 evidence |
| 3 | a person reviews | "part of X cuisine" (Wikidata P2012), a shared cuisine affiliation, a Food Graph relation | not used to add or place a dish; P2012 only links a dish to a Wikidata region (item 33); using it as evidence is item 36 |
| 4 | a person only | disputed origins, political disputes, shared ownership, indirect references | sent to a person: disputed places (item 33, rule 4), drops in `shared_dish_origins.csv`, Taiwan (item 31) |
| 5 | never usable | AI inference, similarity, a nearby cuisine, unsourced statements | never used |

A tier 2 source contradicted by a tier 1 source gives way to it, except where a person has decided otherwise
(item 25). Moving the category rule down to tier 2, or using tier 3 evidence, is a change to the coverage rule
and needs a review item first.
