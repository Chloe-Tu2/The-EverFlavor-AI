# Multi-origin dish policy

Decided by med27-coder, 2026-11-24 (answers review item 32). Many dishes belong to more than one country: Mansaf,
Shiro, Kalduny, Doro wat, and many Balkan, Levantine, Central Asian, Caribbean and West African dishes. The atlas
records the traditions as they are, instead of forcing one owner per dish.

## The rules

1. **Several origins.** The atlas may record several countries of origin for a dish. A valid origin is never
   dropped only because another valid origin exists.
2. **Representation for each.** A dish counts toward the representation of every country with sourced evidence.
   Mansaf (Wikidata: Jordan) counts for Jordan; Shiro (Wikidata: Ethiopia and Eritrea) counts for both.
3. **Source-backed only.** Allowed evidence: Wikidata's country of origin, the dish article's own introduction,
   or an explicit statement in a cited source. Not allowed: being near a country on a cuisine page, a model's
   guess, or regional similarity.
4. **Display.** A dish page may list all its origin countries; each country page may show the same dish when it
   is sourced.
5. **People decide disputes.** Conflicting source claims, disputed cultural ownership and political disputes go
   to a person, as review items.
6. **Coverage counting.** A multi-origin dish counts toward every valid origin country's coverage and
   representation, so a country is not left empty when there is strong evidence.

## How the code applies it

- `scripts/knowledge/dish_origins.py` (`countries_of`) is the one place the rule lives. The coverage, country
  score, country count and impact scripts all use it.
- A dish counts for its listing country (its `country` field, set by the keep rule reviewed in items 23 to 30)
  and for every other country Wikidata gives as its country of origin, when that country is a country in the
  place tree.
- Never mapped: historical states, regions and sub-national names (Ottoman Empire, Levant, Scotland, Korea,
  Hong Kong). Mapping them would be inference. Only plain label differences are aliased (People's Republic of
  China to China, Republic of the Congo to Congo).
- A culinary region (a dish's `region`) stays with the listing country.
- Every added country is a row in `data/knowledge/review/shared_dish_origins.csv`. A person can write `drop`
  in `verdict` (with their name in `reviewer`); the dish then stops counting there. Rows that give a country its
  first dish come first. The summary is [multi_origin_dishes.md](../audits/multi_origin_dishes.md).

## Not done yet

- **Intro evidence:** an added country from the dish's own intro (rule 3) is not read yet; only Wikidata's origin.
- **The app:** it still shows one country per dish. Showing every origin country (rule 4) is the next step.
- **Listing countries without evidence:** a listing country with no Wikidata origin or intro naming it (Shiro
  under India, from the List of Indian dishes) is not changed by this policy. Those cases stay with item 25.
