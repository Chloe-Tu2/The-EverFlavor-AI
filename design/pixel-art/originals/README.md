# Originals: the Team's Own Art

Put the team's pictures here (the detailed style of the concept sheet). Each one replaces the code-drawn version
the next time the art is redrawn: `python design/pixel-art/make_pixel_art.py`. Remove a file and the code-drawn
version comes back (it is also kept in `../archive/`).

## Kitchens

One picture per kitchen, **the kitchen alone**: no title sign, buttons, chef or text on it (the page draws
those). Landscape, about 16:9; any size from 960 x 540 up. PNG.

| File | Kitchen | Opens for |
|---|---|---|
| `classic.png` | The everyday kitchen (Classic theme) | No cuisine chosen |
| `japanese.png` | Japanese | Asian recipes |
| `mediterranean.png` | Mediterranean | European recipes |
| `mexican.png` | Mexican | Latin American recipes |
| `middle_eastern.png` | Middle Eastern | Middle Eastern recipes |

(`morning.png`, `night.png` and `basil.png` work the same way for those themes.)

Keep the middle and the bottom fairly quiet: the title sits top left, Settings top right, and the panels cover
the lower part.

## Things that move when tapped (optional)

To keep the jars, pots and plants shaking when tapped, add `<kitchen>.hotspots.json` next to the picture, with a
box around each object in the picture's own pixels (any image editor shows the position under the mouse):

```json
[
  {"name": "soy_bottle", "x": 120, "y": 210, "w": 40, "h": 90},
  {"name": "bonsai", "x": 1180, "y": 520, "w": 160, "h": 150}
]
```

Claude can make this file from the picture.

## Chefs

One picture per chef, **on a transparent background**, square, the head and shoulders like the concept sheet:
`chef_classic.png`, `chef_japanese.png`, `chef_mexican.png`, `chef_middle_eastern.png`. The same picture is used
in every mood; the page still makes it hop when tapped.

## License

Write in `../references/SOURCES.md` where each picture came from (who made it, and with which tool), so the
team can show it may be used.
