# Indigenous foods: the review rubric

Written 2026-11-23 for sprint 2 (Oceania and Indigenous foods), from med27-coder's rules. A person applies it to
every tag in `data/knowledge/atlas/indigenous_traditions.json` before the app shows it.

## What the code already does

`scripts/knowledge/fetch_knowledge.py` (`INDIGENOUS_PAGES`, `traditions`) tags a dish or food with a tradition
only when rules 2 and 3 both hold. Every tag starts as `"reviewed": false`.

## The rules

1. **The tradition is named and identifiable.** Tracked now: Māori, Aboriginal Australian, Native American, Inuit,
   Sámi, Ainu, Mapuche, Native Hawaiian, Chamorro. A new one needs its own Wikipedia page and a person's yes.
2. **The tradition's page lists the food.** The food is linked from that page (a list, a table or a paragraph).
3. **The food's own page names the people.** Its Wikipedia intro says "Māori", "Inuit", "Ainu" and so on.
4. **No guessing.** A country is never a tradition: a New Zealand dish is not Māori because it is from New Zealand.
   No AI model adds, changes or explains a tag.
5. **A person reviews every tag.** It stays `"reviewed": false` until then. Check that:
   - the intro calls the food the people's own, not only eaten by them or sold near them;
   - the words are not about something else ("Hawaiian pizza" is not Native Hawaiian);
   - the community's own name is used, as the source spells it.

## What the app may say

Only what the sources say: "This dish is associated with Māori food traditions (Wikipedia: Māori cuisine)". No fun
facts, history or sacred and ceremonial uses beyond the source sentences, and none of those before review.

## The knowledge objects

Each tradition in `indigenous_traditions.json` has its people, its country (or "several"), its source page, and
its foods with their country and `reviewed` flag. Built by `scripts/knowledge/culinary_coverage.py`.
