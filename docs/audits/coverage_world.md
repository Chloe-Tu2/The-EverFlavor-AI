# World coverage (audit, 2026-11-22)

Which parts of the world EverFlavor covers, which it lacks, and where the next dishes should come from. Built by `scripts/knowledge/coverage_audit.py`; the data is in `data/knowledge/coverage/`. Nothing was added to the app.

**How to read it.** "Dishes" are the dishes in our knowledge notebook listed for the country (from its Wikipedia cuisine list). "Missing" are dishes Wikidata files under a dish family with this country of origin that we do not have: a lower bound, since many dishes are in no family on Wikidata. "Share" is dishes / (dishes + missing). Coverage: **high** = 50+ dishes and share 60%+, **medium** = 15+ dishes and share 40%+, **low** = fewer, **recipes only** = recipes but no dish knowledge, **absent** = neither.

## By zone

| Zone | Countries | In the tree | With dishes | Dishes | Recipes | Ready to add | To review |
|---|---:|---:|---:|---:|---:|---:|---:|
| [Europe](coverage_europe.md) | 52 | 28 | 20 | 1185 | 50,001 | 693 | 131 |
| [Asia](coverage_asia.md) | 34 | 16 | 11 | 994 | 19,708 | 416 | 42 |
| [Africa](coverage_africa.md) | 55 | 9 | 2 | 38 | 756 | 23 | 22 |
| [the Americas and the Caribbean](coverage_americas.md) | 57 | 22 | 10 | 760 | 148,888 | 234 | 28 |
| [Oceania](coverage_oceania.md) | 27 | 2 | 2 | 59 | 3,142 | 6 | 4 |
| [the Middle East and North Africa](coverage_middle_east.md) | 23 | 15 | 8 | 165 | 3,530 | 87 | 20 |

## Over-represented

Where most of the recipes are (share of all recipes with a known country) and the dishes behind them:

| Country | Recipes | Share of recipes | Dishes | Share of dishes |
|---|---:|---:|---:|---:|
| United States | 131,095 | 58% | 367 | 11% |
| Italy | 24,910 | 11% | 326 | 10% |
| Mexico | 11,490 | 5% | 110 | 3% |
| France | 8,520 | 4% | 84 | 3% |
| India | 7,312 | 3% | 102 | 3% |
| China | 5,878 | 3% | 178 | 6% |
| Canada | 4,577 | 2% | 88 | 3% |
| United Kingdom | 4,553 | 2% | 67 | 2% |
| Greece | 4,334 | 2% | 88 | 3% |
| Australia | 2,758 | 1% | 58 | 2% |

## Under-represented

- **Recipes but no dish knowledge** (39): Puerto Rico (71), Costa Rica (43), Venezuela (42), Ecuador (35), Iceland (34), Nepal (33), Nigeria (32), Guatemala (24), Laos (18), Libya (17), Dominica (15), Sudan (12), Albania (11), Algeria (11), Angola (10), Honduras (10), Somalia (9), Croatia (8), Afghanistan (7), Bulgaria (7), Cayman Islands (7), Congo (7), Tunisia (7), Uruguay (7), Aruba (6), Barbados (6), Botswana (6), Ukraine (6), Syria (5), Taiwan (5), Kenya (4), Namibia (4), Slovakia (4), Andorra (3), Antigua and Barbuda (3), Armenia (3), Bangladesh (3), Estonia (3), Azerbaijan (2).
- **Absent, 20 million people or more** (17; population from Wikidata): Democratic Republic of the Congo, Tanzania, Myanmar, Uganda, Uzbekistan, Ghana, Madagascar, Ivory Coast, Mozambique, Cameroon, Yemen, North Korea, Burkina Faso, Mali, Niger, Sri Lanka, Kazakhstan.
- **Absent in all**: 163 countries and territories with neither dishes nor recipes (`missing_countries.json`).

## The expansion backlog

3,689 dishes Wikidata lists in a family that we do not have: **1,459 ready**, **357 to review** and **1,873 blocked** (no country of origin), by the rules in [publishing_rules.md](publishing_rules.md). Every one would be a knowledge-only dish: none comes with a recipe.

## If EverFlavor adds 500 dishes next

A fixed rule, not a taste: ready dishes only; countries in priority order (tier 1 first); within a country, dishes whose family EverFlavor already has first (they join the graph at once), then those with a Wikipedia article; at most 40 from one country; then one country after another. The list is `data/knowledge/coverage/next_500.json` (500 dishes).

| Zone | Dishes |
|---|---:|
| Europe | 219 |
| Asia | 120 |
| the Americas and the Caribbean | 85 |
| the Middle East and North Africa | 53 |
| Africa | 17 |
| Oceania | 6 |

By country: China 12, France 12, Germany 12, India 12, Italy 12, Japan 12, Spain 12, United Kingdom 12, United States 12, Turkey 12, Philippines 12, Switzerland 12, Netherlands 12, Iran 12, Indonesia 12, Canada 12, Sweden 12, Belgium 12, Nigeria 12, Mexico 11, Denmark 11, Bulgaria 11, Poland 11, Taiwan 11, Argentina 10, Finland 10, Peru 10, Austria 9, South Korea 9, Greece 8, Ireland 8, Russia 8, Cambodia 7, Thailand 7, Algeria 6, Iceland 6, Venezuela 6, Afghanistan 5, Armenia 5, Australia 5, Azerbaijan 5, Brazil 5, Pakistan 5, Portugal 5, Tunisia 5, Ukraine 5, Vietnam 5, Chile 4, Croatia 4, Czech Republic 4, Hungary 4, Bangladesh 3, Colombia 3, Egypt 3, Laos 3, Malaysia 3, Norway 3, Slovakia 3, Uruguay 3, Puerto Rico 2, Ecuador 2, Guatemala 2, Iraq 2, Kenya 2, Nepal 2, Somalia 2, Syria 2, New Zealand 1, Barbados 1, Estonia 1, Honduras 1, Jamaica 1, Libya 1, South Africa 1.

Why so few from Africa and Oceania: Wikidata files few of their dishes under a family with a country of origin, so they have few ready dishes. Growing them needs a new source (their Wikipedia cuisine lists, as notebook 11 reads for 54 countries today), not a guess.

## Priority tiers

- **Tier 1:** in the place tree and 20+ ready dishes, or 200+ recipes with fewer than 15 dishes.
- **Tier 2:** 5+ dishes ready or to review, or 50+ recipes with fewer than 5 dishes.
- **Tier 3:** any other gap.

Cultural importance is not scored: no source we use measures it, and we do not guess it.

| Tier | Country | Zone | Coverage | Why |
|---|---:|---:|---:|---:|
| 1 | United Kingdom | Europe | low | 171 dishes ready to add; 1 to review |
| 1 | United States | North America | high | 148 dishes ready to add |
| 1 | Japan | Asia | medium | 139 dishes ready to add |
| 1 | France | Europe | low | 133 dishes ready to add; 46 to review |
| 1 | China | Asia | high | 98 dishes ready to add; 1 to review |
| 1 | Italy | Europe | high | 78 dishes ready to add; 1 to review |
| 1 | India | Asia | high | 65 dishes ready to add |
| 1 | Spain | Europe | medium | 59 dishes ready to add; 1 to review |
| 1 | Germany | Europe | high | 40 dishes ready to add |
| 1 | Turkey | Middle East & North Africa | high | 32 dishes ready to add |
| 1 | Switzerland | Europe | medium | 30 dishes ready to add; 2 to review |
| 1 | Philippines | Asia | high | 30 dishes ready to add |
| 1 | Netherlands | Europe | medium | 29 dishes ready to add; 1 to review |
| 1 | Iran | Middle East & North Africa | low | 26 dishes ready to add; 432 recipes but 11 dishes |
| 1 | Indonesia | Asia | high | 24 dishes ready to add |
| 1 | Canada | North America | high | 20 dishes ready to add |
| 1 | Sweden | Europe | medium | 20 dishes ready to add |
| 1 | New Zealand | Oceania | low | 1 dishes ready to add; 384 recipes but 1 dishes |
| 2 | Belgium | Europe | medium | 18 dishes ready to add |
| 2 | Nigeria | Africa | recipes only | 18 dishes ready to add |
| 2 | Mexico | Latin America | high | 16 dishes ready to add; 2 to review |
| 2 | Denmark | Europe | medium | 14 dishes ready to add |
| 2 | Bulgaria | Europe | recipes only | 12 dishes ready to add |
| 2 | Poland | Europe | high | 11 dishes ready to add |
| 2 | Taiwan | Asia | recipes only | 11 dishes ready to add |
| 2 | Peru | Latin America | medium | 10 dishes ready to add; 1 to review |
| 2 | Finland | Europe | medium | 10 dishes ready to add |
| 2 | Argentina | Latin America | low | 10 dishes ready to add |
| 2 | South Korea | Asia | high | 9 dishes ready to add |
| 2 | Austria | Europe | low | 9 dishes ready to add |
| 2 | Greece | Europe | high | 8 dishes ready to add |
| 2 | Ireland | Europe | medium | 8 dishes ready to add |
| 2 | Russia | Europe | medium | 8 dishes ready to add |
| 2 | Thailand | Asia | high | 7 dishes ready to add |
| 2 | Cambodia | Asia | low | 7 dishes ready to add |
| 2 | Venezuela | Latin America | recipes only | 6 dishes ready to add |
| 2 | Iceland | Europe | recipes only | 6 dishes ready to add |
| 2 | Algeria | Middle East & North Africa | recipes only | 6 dishes ready to add |
| 2 | Vietnam | Asia | high | 5 dishes ready to add; 1 to review |
| 2 | Australia | Oceania | high | 5 dishes ready to add |
| 2 | Portugal | Europe | high | 5 dishes ready to add |
| 2 | Brazil | Latin America | high | 5 dishes ready to add |
| 2 | Pakistan | Asia | low | 5 dishes ready to add |
| 2 | Afghanistan | Asia | recipes only | 5 dishes ready to add |
| 2 | Tunisia | Middle East & North Africa | recipes only | 5 dishes ready to add |
| 2 | Ukraine | Europe | recipes only | 5 dishes ready to add |
| 2 | Armenia | Middle East & North Africa | recipes only | 5 dishes ready to add |
| 2 | Azerbaijan | Middle East & North Africa | recipes only | 5 dishes ready to add |
| 2 | Puerto Rico | Caribbean | recipes only | 2 dishes ready to add |
| 2 | Romania | not in the tree | absent | 20 to review; not in the place tree |
| 2 | Georgia | not in the tree | absent | 19 to review; not in the place tree |
| 2 | Slovenia | not in the tree | absent | 11 to review; not in the place tree |
| 2 | Myanmar | not in the tree | absent | 9 to review; not in the place tree |
| 2 | Serbia | not in the tree | absent | 8 to review; not in the place tree |
| 2 | Ghana | not in the tree | absent | 7 to review; not in the place tree |
| 2 | Sri Lanka | not in the tree | absent | 7 to review; not in the place tree |
| 2 | Yemen | not in the tree | absent | 7 to review; not in the place tree |
| 2 | Israel | not in the tree | absent | 6 to review; not in the place tree |
| 2 | Kazakhstan | not in the tree | absent | 5 to review; not in the place tree |
| 2 | Paraguay | not in the tree | absent | 5 to review; not in the place tree |
| 2 | Trinidad and Tobago | not in the tree | absent | 5 to review; not in the place tree |
| 2 | Saudi Arabia | Middle East & North Africa | low |  |
