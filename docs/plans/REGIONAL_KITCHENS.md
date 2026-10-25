# Regional Kitchens

Which kitchens EverFlavor shows for which recipes, which come next, and a brief for each so the team's art tool
draws them in the concept sheet's style. Part of version 0.6.0 ([planner](README.md)).

## Rules for every kitchen

1. **Accurate, not a costume party.** Objects people in that country really cook with (a wok, a tagine, a comal),
   in a home kitchen, not a theme restaurant. No flags, no landmarks pasted on, no stereotypes.
2. **The chef wears everyday kitchen clothes** (a cap, an apron, a jacket, a djellaba, a headband) and smiles.
   Traditional dress only where cooks really wear it.
3. **Checked by someone from that food culture** before the kitchen leaves draft.
4. **Same title everywhere:** the page's sign always says "EverFlavor Kitchen"; the kitchen changes, the brand does not.
5. **Data first:** build kitchens in the order of how many recipes they would open.

## The recipes, by country

These counts are from 0.5.1; the current counts per country, and the country labels' known problems, are in
[CUISINE_REGIONS.md](CUISINE_REGIONS.md). Which kitchen each country opens is set in the app (`COUNTRY_KITCHENS`).

Recipes per country of origin in the processed data (labeled by the source, or predicted at 70%+ confidence;
all splits). The five cuisine families are the ones the main README names.

| Family | Countries with the most recipes |
|---|---|
| Asian | India 6,659 · China 5,191 · Thailand 2,179 · Japan 2,007 · South Korea 570 · Vietnam 481 |
| African | Morocco 1,460 · South Africa 579 · Egypt 196 · Ethiopia 78 · Nigeria 32 |
| European | Italy 18,041 · France 7,422 · United Kingdom 4,121 · Greece 3,533 · Spain 1,670 · Germany 1,320 |
| Latin American | Mexico 12,635 · Cuba 373 · Brazil 314 · Argentina 108 · Peru 97 · Puerto Rico 71 |
| Middle Eastern | Lebanon 567 · Turkey 450 · Iran 415 · Saudi Arabia 69 · Iraq 66 · Palestine 50 |

## Built (code-drawn drafts, 0.5.1)

| Kitchen | Opens for | Chef |
|---|---|---|
| Japanese | Settings (Japan) | Hachimaki headband, navy samue jacket |
| Chinese | Asian recipes | White cook's cap, white jacket with a mandarin collar and knotted buttons |
| Mediterranean | European recipes | Classic toque and neckerchief |
| Mexican | Latin American recipes | Red bandana, embroidered shirt |
| Middle Eastern | Middle Eastern recipes | Keffiyeh with agal, white thobe |
| Moroccan | African recipes | Bare head, cream djellaba with embroidery |

Drawings: [design/pixel-art/cuisine_kitchens.py](../../design/pixel-art/cuisine_kitchens.py); previews in
`design/pixel-art/previews/`. The team's detailed versions replace them once they are in `design/pixel-art/originals/`.

## Planned (0.6.0 and later), in order

| Priority | Kitchen | Why now | Opens for |
|---|---|---|---|
| 1 | **Indian** | The biggest Asian country in the data (6,659) | India |
| 2 | **Italian** | The biggest country overall (18,041); today it shares Mediterranean | Italy |
| 3 | **French** | 7,422 recipes | France |
| 4 | **Thai** | 2,179 | Thailand |
| 5 | **British** | 4,121 | United Kingdom |
| 6 | **Korean** | 570, and a distinct kitchen (onggi jars, kimchi fridge) | South Korea |
| 7 | **South African** | The second African country (579) | South Africa |
| 8 | **Ethiopian, West African** | Few recipes now (78, 32), but distinct; worth it when more African data arrives | Ethiopia, Nigeria, Ghana |
| 9 | **Caribbean, Brazilian, Peruvian** | Latin America beyond Mexico (373, 314, 97) | Cuba and Puerto Rico, Brazil, Peru |
| 10 | **Vietnamese, Turkish, Persian** | Split out of Asian and Middle Eastern when the country-level kitchens exist | Vietnam, Turkey, Iran |

## Choosing the kitchen

Today each **cuisine family** opens one kitchen (Asian → Chinese). That is wrong for many recipes: an Indian
curry opens the Chinese kitchen. Options:

| Option | Pros | Cons |
|---|---|---|
| **A. Family → one kitchen** (now) | Simple; works with the Cuisine menu as it is | Inaccurate inside big families (Asian: India, China, Japan, Thailand) |
| **B. Country of the results** (recommended for 0.6) | Accurate: the kitchen of the country most of the shown recipes come from; uses `origin_country`, already in the data | 21% of recipes have no country; predicted countries are right about 89% of the time, so some kitchens will be wrong; needs the page to keep its results while the kitchen changes |
| **C. A Country menu under Cuisine** | Accurate and clear; the user chooses | One more control; countries without a kitchen need a family default |
| **D. One kitchen per recipe card** (a small kitchen badge) | Every recipe shows its own place | Busy; the background still has to pick one |

Plan: **B with C as the fallback**. Recipes whose country is predicted (not labeled) say "probably Moroccan", as the
privacy and ethics notes require, and the kitchen follows only labeled countries or confident predictions.

## Art brief (for the team's art tool)

Use the same style as the concept sheet: detailed 16-bit pixel art, warm light, a home kitchen seen straight on,
landscape 16:9, **no text, no title sign, no people, no buttons** (the page adds those). Keep the middle and the
lower third calm (the page's panels go there). One chef per kitchen, head and shoulders, smiling, on a
transparent background, in the same style.

| Kitchen | Must have | Avoid |
|---|---|---|
| Indian | Pressure cooker, tawa, steel masala dabba (round spice box), brass and steel pots, a stone mortar (sil batta), curry leaves, a window with a jali screen | Snake charmers, elephants, temples |
| Italian | Pasta drying on a rack, a moka pot, tomatoes, a wheel of cheese, olive oil, terracotta floor, a window on a courtyard | The Leaning Tower, gondolas |
| French | Copper pans, a baguette, a cheese board, herbs de Provence, a zinc counter or a bistro window | The Eiffel Tower, berets |
| Thai | Mortar and pestle (krok), sticky-rice baskets, lemongrass, chilies, a wok, a gas burner, fish sauce | Elephants, temples |
| British | An Aga-style range, a teapot and tea tin, a Victoria sponge, a window with rain | Guards, red phone boxes |
| Korean | Onggi jars, a kimchi fridge, a stone pot (dolsot), a rice cooker, gochujang | |
| South African | A braai (grill) outside the window, a potjie pot, rooibos, chakalaka | Safari animals |
| Ethiopian | A mitad for injera, a jebena coffee pot, berbere, a mesob basket | |
| West African | A big pot of jollof, a mortar for pounding yam (fufu), palm oil, plantains | Masks |
| Caribbean | A dutch pot, scotch bonnets, plantains, a window on palms | |
| Brazilian | Feijoada pot, cheese bread (pão de queijo), a coffee filter, cassava | Carnival costumes |
| Peruvian | Ají peppers, corn of many colours, potatoes, a clay pot | Llamas in the kitchen |

Chef notes: everyday cook's clothes. For example an apron and a cotton cap for India, a short cap and white jacket
for France, an apron for Korea.
