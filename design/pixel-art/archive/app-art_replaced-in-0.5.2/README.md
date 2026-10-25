# App art replaced in 0.5.2

The kitchen and chef pictures the app loaded until 0.5.1 and no longer uses, moved here on 2026-10-24:

| Files | What they were | Replaced by |
|---|---|---|
| `kitchen_{chinese,mediterranean,mexican,middle_eastern}.png`, `scene_*.json`, `*_x4.png` | The v2 cuisine kitchens (code-drawn) | The v5 traced kitchens (`../../assets/scene_v5_*.json`) |
| `kitchen_basil.png`, `scene_basil.json`, `kitchen_basil_x4.png` | The Basil theme (Classic in green) | Dropped: one Classic kitchen |
| `kitchen_morning.png`, `kitchen_night.png` | The Morning and Night themes' still pictures | Classic's morning and night light (`../../build_classic_scene.py` still reads their `scene_morning.json` and `scene_night.json`) |
| `chef_{chinese,japanese,middle_eastern}_*.png`, `chef_{alert,thinking,wink}.png`, `*_x8.png` | The code-drawn chefs | The chefs from the team's references (`chef_ref_*`) |

`make_pixel_art.py` and `cuisine_kitchens.py` still draw them: running those again writes them back into
`../../assets/`. Move them here again (or drop them from those scripts) if that happens.
