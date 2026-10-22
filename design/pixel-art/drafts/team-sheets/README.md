# Team concept sheets: one per kitchen

The second Saffron Market sheet (`../../references/concepts/middle_eastern_v2_colorful.png`) is the format every
kitchen should follow: the kitchen on top, and under it the kitchen's own **chefs**, its own **title sign** for the
app page, and its **props**, each drawn on its own. The sign as a separate piece fixes the phone problem (a title
painted into the room is cropped away on a phone); the chefs give each kitchen its own guide.

`python design/pixel-art/cut_sheet.py` cuts a sheet's pieces into transparent PNGs here (one folder per sheet,
with `sheet.png` showing them all). Done so far: [middle_eastern_v2/](middle_eastern_v2/sheet.png) (17 pieces).

## The format (copy it for every kitchen)

| Part | What to draw | How the app uses it |
|---|---|---|
| Kitchen | The full room, 16:9, the colorful look of the Saffron Market sheet; leave the wall where a sign would hang empty | The background |
| Chefs | Four people in the kitchen's clothing, two women and two men, full body, facing us: holding a dish, holding a spoon, holding a pot, arms crossed | The chef guide: dish = happy (greeting, a safe recipe), spoon = thinking (nothing found yet), pot = cooking or wink, arms crossed = alert (a problem in the recipe) |
| Title sign | The kitchen's name on a hanging sign in its own style, with two lights on the sides | The title on the page, kept separate from the background |
| Props | 10 to 14 objects from the kitchen (a valance or banner, a shelf, a board, two plants, a utensil rail, two food bowls, a signature dish or pot, jars, a jug, a utensil jar) | Objects that move when tapped, later |

Keep the sheet's background plain (one light color, or real transparency), with space between pieces, so they cut
cleanly. Clothing should be what people wear to cook in that region today or traditionally, not a costume.

## Briefs for the other kitchens

The names come from the team's first concept kitchens.

| Kitchen | Title sign | Chefs (clothing) | Props | Kitchen changes (from [INDOOR_REFERENCES.md](../../references/INDOOR_REFERENCES.md)) |
|---|---|---|---|---|
| Chinese | **The Jade Wok**: dark lacquer board with a red frame, jade-green letters edged in gold, red paper lanterns at the sides, plum blossom | Cotton cooking jackets (frog buttons), aprons, one with a head scarf | Red silk valance with tassels, bamboo steamer stack, wok and ladle, chopstick jar, blue-and-white bowls, dumplings, bok choy, chili string, tea set, soy sauce bottles | A tiled wok stove instead of the Western oven; a hood or flue over it |
| Mediterranean | **The Golden Hearth**: olive-wood board, gold letters, olive branch and lemons, iron lanterns | Linen shirts and aprons, one with a head scarf, rolled sleeves | Striped linen valance, olive-oil bottles, garlic braid, bread board, lemons, tomato bowl, copper pans on a rail, terracotta jug, herb pots, majolica plates | Terracotta floor; the fireplace as a cooking hearth; blue and white majolica tiles for the colorful look |
| Mexican | **The Joyful Kitchen**: Talavera-tiled board, bright letters, papel picado above, tin star lanterns | Embroidered blouses and aprons, a rebozo, one with a bandana | Papel picado banner, clay cazuelas on a rail, comal, molcajete, tortilla basket, chili string, limes, Talavera jars, cactus pot, wooden spoons | Talavera on the counter tops; a tiled hood over the stove |

## Next steps

1. The team makes the three sheets (same tool and style as the Saffron Market sheet).
2. Claude adds their boxes to `cut_sheet.py`, traces each kitchen with `trace_kitchens.py`, and maps the chefs to the
   moods above.
3. The app shows each kitchen's sign as the title and its chefs as the guide (after the title layout is chosen on
   the test page, `title_test_page.py`).
