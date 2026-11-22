# The waiter's knowledge coverage (2026-11-22)

What the waiter can tell about each dish, all of it copied from Wikipedia (credited) and Wikidata, never written by a model.

| What | Dishes | Share |
|---|---:|---:|
| at least one fun fact | 1,848 | 58% |
| three fun facts (what he shows first) | 401 | 13% |
| a story (history, origin, culture) | 1,587 | 50% |
| read more: its own article | 3,201 | 100% |
| read more: its cuisine or region page | 3,038 | 95% |
| read more: books, UNESCO, Wikidata | 3,201 | 100% |
| graph lines: 3 or more | 1,130 | 35% |
| facts checked by a person | 0 | 0% |

## Remediation plan

1. **Review.** No dish's facts are checked by a person yet; the review sheet (`data/knowledge/review/focus_review.csv`, 260 rows) has 0 decisions. Its keep / fix / drop verdicts are the first step before the chat in 0.8.0 shows facts.
2. **Stories** for 1,614 dishes: `fetch_knowledge.py --stories` reads their articles' History and Origin sections; where an article has none, there is none to show.
3. **Three facts** are there for 401 dishes; the rest show fewer, never filler.
4. **Graph lines:** a dish with only its place gets more lines when notebook 15 finds its family.
