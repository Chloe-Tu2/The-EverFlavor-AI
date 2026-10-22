# Draft: Cuisine Kitchens

Kitchens for the cuisine families in the recipe data: four recreated from the team's concept art (2026-10-18), plus
Chinese (Asian recipes come mostly from India, then China) and Moroccan (the biggest African country in the data).
Which kitchens come next: [docs/plans/REGIONAL_KITCHENS.md](../../../../docs/plans/REGIONAL_KITCHENS.md). Drawn in code in [../../cuisine_kitchens.py](../../cuisine_kitchens.py), so anyone can change a color or move
a jar and redraw with `python design/pixel-art/make_pixel_art.py`.

**Title:** every kitchen keeps the app's own name, **EverFlavor Kitchen**. The concepts used other names
(The Jade Wok, The Golden Hearth, The Joyful Kitchen, The Saffron Market, Ever American Kitchen), which would make
the app look like four different products.

| Kitchen | Cuisine family | From the concept | Chef |
|---|---|---|---|
| Japanese | Settings (Japan) | Wood beams, shoji window, soy and sake bottles, donabe pot, rice sack, wok, bonsai | Hachimaki headband, navy samue jacket |
| Mediterranean | European | Stone walls, olive oil and spice jars, garlic braid, copper pans, window on green hills, basil | The classic toque and red neckerchief |
| Mexican | Latin American | Papel picado, clay ollas on blue shelves, corn, chilies, beans, talavera tiles, painted window with cactus | Red bandana, embroidered shirt |
| Middle Eastern | Middle Eastern | Tiled arches, spice jars, brass dallah coffee pots, grain sacks, flatbread, arched window at sunset, palm | Keffiyeh with agal, white thobe |
| Chinese | Asian | Moon window with a lattice, red lantern, bamboo steamers, wok over a flame, cleaver on a round block, tea set, bok choy (not in the concept sheet) | White cook's cap, mandarin-collar jacket |
| Moroccan | African | Zellige tiles, horseshoe arch, painted tagines, spice cones, brass lantern, mint tea, preserved lemons, khobz (not in the concept sheet) | Bare head, embroidered djellaba |

| Japanese | Mediterranean |
|---|---|
| ![Japanese kitchen](mockup_japanese.png) | ![Mediterranean kitchen](mockup_mediterranean.png) |
| **Mexican** | **Middle Eastern** |
| ![Mexican kitchen](mockup_mexican.png) | ![Middle Eastern kitchen](mockup_middle_eastern.png) |
| **Chinese** | **Moroccan** |
| ![Chinese kitchen](mockup_chinese.png) | ![Moroccan kitchen](mockup_moroccan.png) |

The scenes on their own (before the page is drawn over them):

| Japanese | Mediterranean | Mexican |
|---|---|---|
| ![Japanese](../../previews/kitchen_japanese_x4.png) | ![Mediterranean](../../previews/kitchen_mediterranean_x4.png) | ![Mexican](../../previews/kitchen_mexican_x4.png) |
| **Middle Eastern** | **Chinese** | **Moroccan** |
| ![Middle Eastern](../../previews/kitchen_middle_eastern_x4.png) | ![Chinese](../../previews/kitchen_chinese_x4.png) | ![Moroccan](../../previews/kitchen_moroccan_x4.png) |

## In the app (draft)

- Settings lists the cuisine kitchens next to Classic, Morning, Night and Basil.
- **Match the kitchen to the cuisine** (Settings, on by default): Asian recipes open the Chinese kitchen, African the
  Moroccan, European the Mediterranean, Latin American the Mexican, Middle Eastern its own. Japanese is in Settings.
- Every piece on the shelves and counters reacts to a tap, like the classic kitchen.

## To redraw before this leaves draft

1. **Middle Eastern window:** the pointed arch reads as a house roof; draw a real horseshoe or pointed arch.
2. **More of the kitchen in view:** done in 0.5.1 (the concept sheet's layout: the chef in the sidebar, the kitchen
   open under the title).
3. **Detail:** the concepts have richer texture (wood grain, brick, glazed pots). Twice the resolution
   (480 x 270, see `design/PLAN.md`) would leave room for it.
4. **The chefs' faces** share the classic chef's features; each could get its own face and smile.
5. **Respect check:** have someone from each food culture look at their kitchen and chef before it goes public.
