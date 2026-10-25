# Archive

Every earlier version of the pixel art, labelled in order, so the team can see how the kitchens got to where they
are and bring an old look back. Before changing or dropping a picture the app uses, copy the current file here and
add a row.

What stays outside the archive: the team's concept art (`../references/concepts/`), the current draft
(`../drafts/traced-kitchens/`, v5) and the art the app shows today (`../assets/`, `../previews/`, drawn by
`make_pixel_art.py` and `cuisine_kitchens.py`, which the app needs).

## Versions

| Version | Folder | What it was | Why we moved on |
|---|---|---|---|
| v1 (2026-10-18) | [v1_2026-10-18_code-drawn/](v1_2026-10-18_code-drawn/) | Kitchens drawn in code from simple shapes: Classic, Morning, Night, Basil and four cuisine drafts; all chefs in every mood; page mockups | Flat and generic next to the team's concept sheet |
| v2 (2026-10-18, in the app until 0.5.1) | [v2_2026-10-18_cuisine-mockups/](v2_2026-10-18_cuisine-mockups/README.md) | The cuisine kitchens redrawn after the concept art, six cuisines (Chinese and Moroccan added), shown as page mockups. Its kitchen and chef files are in [app-art_replaced-in-0.5.2/](app-art_replaced-in-0.5.2/README.md) | Still simple shapes; not the detailed style |
| v3 (2026-10-19) | [v3_2026-10-19_concept-sheet-recreation/](v3_2026-10-19_concept-sheet-recreation/README.md) | The concept sheet's four small kitchens and four chefs recreated in code, with shading (`concept_recreation.py`) | The sheet's panels are small; the team's four full kitchens came next |
| v4 (2026-10-21 to 22) | [v4_2026-10-21_full-kitchens-in-code/](v4_2026-10-21_full-kitchens-in-code/README.md) | The team's four full kitchens redrawn in code at 418 x 235 (`concept_kitchens.py`), plus the unapplied plant and rug fix in `wip/` | Wrong angles (the window flat in front, not on the side wall), different chairs, plants and rugs off |
| **v5 (2026-10-22, current, in the app since 0.5.2)** | `../drafts/traced-kitchens/` (sources), `../assets/scene_v5_*.json` (the app) (build steps in [v5_2026-10-22_build-steps/](v5_2026-10-22_build-steps/README.md)) | Each object traced from the team's original and assembled on the pixel grid, then lit (`../trace_kitchens.py`); morning, afternoon, evening and night versions (`../day_night.py`), lamps off by day | Current |
| v6 (future work) | [../future-works/v6/](../future-works/v6/README.md) | A team concept sheet per kitchen: the room, its own chefs, its own title sign and props; the colorful Saffron Market is the first | Set aside on 2026-10-22: its trace looked too pixelated |

The scripts in v3 and v4 are kept as they were. To run one again, copy it back to `design/pixel-art/` (v4 needs
`concept_recreation.py` from v3 next to it).

Other finished work: the [title card test](title-test_2026-10-22/README.md) (four title layouts, desktop and phone).

## Progress sheets

Each kitchen from the concept through every version, labelled (rebuild with
`python design/pixel-art/archive/progress/make_progress.py`):

| Kitchen | Sheet |
|---|---|
| Chinese | [progress/chinese.png](progress/chinese.png) |
| Mediterranean | [progress/mediterranean.png](progress/mediterranean.png) |
| Mexican | [progress/mexican.png](progress/mexican.png) |
| Middle Eastern | [progress/middle_eastern.png](progress/middle_eastern.png) |

A version is left out of a sheet when it had no drawing of that kitchen (for example, no Chinese kitchen in v1 or v3).
