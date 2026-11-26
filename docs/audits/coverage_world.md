# World coverage (audit, 2026-11-25)

Which parts of the world EverFlavor covers, which it lacks, and where the next dishes should come from. Built by `scripts/knowledge/coverage_audit.py`; the data is in `data/knowledge/coverage/`. Nothing was added to the app.

**How to read it.** "Dishes" are the dishes in our knowledge notebook listed for the country (from its Wikipedia cuisine list). "Missing" are dishes Wikidata files under a dish family with this country of origin that we do not have: a lower bound, since many dishes are in no family on Wikidata. "Share" is dishes / (dishes + missing). Coverage: **high** = 50+ dishes and share 60%+, **medium** = 15+ dishes and share 40%+, **low** = fewer, **recipes only** = recipes but no dish knowledge, **absent** = neither.

## By zone

| Zone | Countries | In the tree | With dishes | Dishes | Recipes | Ready to add | To review |
|---|---:|---:|---:|---:|---:|---:|---:|
| [Europe](coverage_europe.md) | 52 | 44 | 43 | 1610 | 50,001 | 686 | 53 |
| [Asia](coverage_asia.md) | 33 | 30 | 29 | 1295 | 19,708 | 408 | 2 |
| [Africa](coverage_africa.md) | 55 | 48 | 34 | 187 | 756 | 15 | 0 |
| [the Americas and the Caribbean](coverage_americas.md) | 57 | 41 | 36 | 943 | 148,888 | 221 | 7 |
| [Oceania](coverage_oceania.md) | 27 | 21 | 8 | 86 | 3,142 | 5 | 0 |
| [the Middle East and North Africa](coverage_middle_east.md) | 24 | 24 | 21 | 365 | 3,530 | 75 | 0 |

## Over-represented

Where most of the recipes are (share of all recipes with a known country) and the dishes behind them:

| Country | Recipes | Share of recipes | Dishes | Share of dishes |
|---|---:|---:|---:|---:|
| United States | 131,095 | 58% | 395 | 9% |
| Italy | 24,910 | 11% | 350 | 8% |
| Mexico | 11,490 | 5% | 131 | 3% |
| France | 8,520 | 4% | 138 | 3% |
| India | 7,312 | 3% | 117 | 3% |
| China | 5,878 | 3% | 216 | 5% |
| Canada | 4,577 | 2% | 92 | 2% |
| United Kingdom | 4,553 | 2% | 86 | 2% |
| Greece | 4,334 | 2% | 90 | 2% |
| Australia | 2,758 | 1% | 60 | 1% |

## Under-represented

- **Recipes but no dish knowledge** (3): Cayman Islands (7), Aruba (6), Namibia (4).
- **Absent, 20 million people or more** (1; population from Wikidata): Burkina Faso.
- **Absent in all**: 81 countries and territories with neither dishes nor recipes (`missing_countries.json`).

## The expansion backlog

3,441 dishes Wikidata lists in a family that we do not have: **1,410 ready**, **171 to review** and **1,860 blocked** (no country of origin), by the rules in [publishing_rules.md](publishing_rules.md). Every one would be a knowledge-only dish: none comes with a recipe.

## If EverFlavor adds 500 dishes next

A fixed rule, not a taste: ready dishes only; countries in priority order (tier 1 first); within a country, dishes whose family EverFlavor already has first (they join the graph at once), then those with a Wikipedia article; at most 40 from one country; then one country after another. The list is `data/knowledge/coverage/next_500.json` (500 dishes).

| Zone | Dishes |
|---|---:|
| Europe | 229 |
| Asia | 127 |
| the Americas and the Caribbean | 77 |
| the Middle East and North Africa | 47 |
| Africa | 15 |
| Oceania | 5 |

By country: China 15, France 15, Germany 15, India 15, Italy 15, Japan 15, Spain 15, United Kingdom 15, United States 15, Turkey 15, Philippines 15, Netherlands 14, Switzerland 14, Iran 14, Indonesia 14, Canada 14, Sweden 14, Belgium 14, Denmark 14, Mexico 13, Argentina 10, Peru 10, Austria 9, Finland 9, Poland 9, South Korea 9, Greece 8, Ireland 8, Nigeria 8, Taiwan 7, Brazil 6, Russia 6, Thailand 6, Czech Republic 5, Pakistan 5, Portugal 5, Sri Lanka 5, Vietnam 5, Australia 4, Chile 4, Georgia 4, Hungary 4, Romania 4, Israel 3, Malaysia 3, Norway 3, Slovakia 3, Uganda 3, Armenia 2, Bulgaria 2, Cambodia 2, Colombia 2, Egypt 2, Iceland 2, Iraq 2, Moldova 2, Myanmar 2, Slovenia 2, Afghanistan 1, Algeria 1, Azerbaijan 1, Bangladesh 1, Bhutan 1, Croatia 1, Cyprus 1, Ghana 1, Guam 1, Jamaica 1, Jordan 1, Kazakhstan 1, Kenya 1, Laos 1, Lithuania 1, Mongolia 1, Nepal 1, North Korea 1, Paraguay 1, Singapore 1, South Africa 1, Syria 1, Tanzania 1, Tunisia 1, Venezuela 1.

Why so few from Africa and Oceania: Wikidata files few of their dishes under a family with a country of origin, so they have few ready dishes. Growing them needs a new source (their Wikipedia cuisine lists, as notebook 11 reads for 54 countries today), not a guess.

## Priority tiers

- **Tier 1:** in the place tree and 20+ ready dishes, or 200+ recipes with fewer than 15 dishes.
- **Tier 2:** 5+ dishes ready or to review, or 50+ recipes with fewer than 5 dishes.
- **Tier 3:** any other gap.

Cultural importance is not scored: no source we use measures it, and we do not guess it.

| Tier | Country | Zone | Coverage | Why |
|---|---:|---:|---:|---:|
| 1 | United Kingdom | Europe | low | 176 dishes ready to add; 1 to review |
| 1 | United States | North America | high | 153 dishes ready to add |
| 1 | Japan | Asia | medium | 138 dishes ready to add |
| 1 | France | Europe | medium | 136 dishes ready to add; 46 to review |
| 1 | China | Asia | high | 98 dishes ready to add; 1 to review |
| 1 | Italy | Europe | high | 85 dishes ready to add; 1 to review |
| 1 | India | Asia | high | 64 dishes ready to add |
| 1 | Spain | Europe | medium | 57 dishes ready to add; 1 to review |
| 1 | Germany | Europe | high | 40 dishes ready to add |
| 1 | Turkey | Middle East & North Africa | high | 31 dishes ready to add |
| 1 | Philippines | Asia | high | 30 dishes ready to add |
| 1 | Netherlands | Europe | medium | 29 dishes ready to add; 1 to review |
| 1 | Switzerland | Europe | medium | 27 dishes ready to add; 2 to review |
| 1 | Iran | Middle East & North Africa | medium | 26 dishes ready to add |
| 1 | Indonesia | Asia | high | 25 dishes ready to add |
| 1 | Canada | North America | high | 20 dishes ready to add |
| 1 | Sweden | Europe | medium | 20 dishes ready to add |
| 2 | Belgium | Europe | medium | 18 dishes ready to add |
| 2 | Denmark | Europe | medium | 14 dishes ready to add |
| 2 | Mexico | Latin America | high | 13 dishes ready to add; 2 to review |
| 2 | Peru | Latin America | medium | 10 dishes ready to add; 1 to review |
| 2 | Argentina | Latin America | low | 10 dishes ready to add |
| 2 | South Korea | Asia | high | 9 dishes ready to add |
| 2 | Poland | Europe | high | 9 dishes ready to add |
| 2 | Finland | Europe | medium | 9 dishes ready to add |
| 2 | Austria | Europe | medium | 9 dishes ready to add |
| 2 | Greece | Europe | high | 8 dishes ready to add |
| 2 | Ireland | Europe | medium | 8 dishes ready to add |
| 2 | Nigeria | Africa | high | 8 dishes ready to add |
| 2 | Taiwan | Asia | medium | 7 dishes ready to add |
| 2 | Thailand | Asia | high | 6 dishes ready to add |
| 2 | Russia | Europe | high | 6 dishes ready to add |
| 2 | Brazil | Latin America | high | 6 dishes ready to add |
| 2 | Vietnam | Asia | high | 5 dishes ready to add; 1 to review |
| 2 | Portugal | Europe | high | 5 dishes ready to add |
| 2 | Czech Republic | Europe | low | 5 dishes ready to add |
| 2 | Pakistan | Asia | low | 5 dishes ready to add |
| 2 | Sri Lanka | Asia | low | 5 dishes ready to add |
| 2 | Saudi Arabia | Middle East & North Africa | low |  |
