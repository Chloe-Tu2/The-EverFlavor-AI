# Recipe photos: use the ones we have, show them whole, hide the wrong ones

Plan written 2026-10-25 (Claude, with med27-coder). Builds on [RELIABILITY.md](RELIABILITY.md#2-recipe-photos)
(the options and their pros and cons). Nothing here is built yet.

## What we have

| Data | Recipes | With a photo | Where the photos are |
|---|---|---|---|
| Demo data (`data/demo`, the live site) | 1,000 (train split) | 994 | Hugging Face recipes-with-nutrition's own image links |
| Full data (`data/processed`) | 204,319 (train split) | 0: the column is not kept | Hugging Face rows (37,823) have the same image links in the raw data; TheMealDB rows (583) have a thumbnail (`strMealThumb`); Food.com and CulinaryDB have none |

The two problems the team saw: some photos are **too zoomed in** to see the dish, and some are **not the dish**
(a site logo, a different recipe, bread on top of beans).

## Steps, in order

| # | Step | How | Effort |
|---|---|---|---|
| 1 | **Show the whole photo** | The card shows the photo inside a fixed 4:3 frame with `object-fit: contain` on the panel's color, so the whole picture fits instead of filling (and cropping) the frame; small photos are not blown up past their size | Small (CSS) |
| 2 | **A bigger view on the dish page** | "About this dish" shows the photo at full width with its credit and link | Small |
| 3 | **Keep the photos in the full data** | Notebook 01 keeps `image_url` for Hugging Face and TheMealDB rows (about 38,000 recipes), with the source for the credit | Small, in the next notebook 01 rerun |
| 4 | **Find shared and logo pictures** | A notebook step downloads each photo once (paced, a local cache that is not committed), takes a small fingerprint (perceptual hash) and flags pictures used by many different recipes: those are logos or placeholders | Medium |
| 5 | **Check that the photo shows the dish** | An open image-text model run locally (CLIP, for example `openai/clip-vit-base-patch32`, MIT license) scores each photo against the dish's clean name (`dish_names.py`); a hand-checked sample of about 200 photos sets the cutoff. Below it, the card shows "No photo of this dish yet" (or the pixel-art dish, planner 0.5.2 item 5) and keeps the credit link | Medium; CPU is enough for 38,000 photos in a few hours |
| 6 | **"Wrong photo?" button** | Hides the photo for everyone after a team member confirms; saves only the recipe id, nothing about the person (privacy rules) | Medium; needs a small shared store |

Steps 1 and 2 fix the zoom at once; steps 4 and 5 hide unrelated photos; step 6 catches what the checks miss.

## Rules

- Only the photos the sources already give; no AI-made photos (RELIABILITY.md: a made-up picture of a real recipe
  misleads).
- Every photo keeps its credit and a link to the recipe's page; photos belong to their sources (research use).
- A hidden photo is never replaced by another recipe's photo.

## Open questions

- Who hand-checks the 200-photo sample (and the "Wrong photo?" reports)?
- Show the pixel-art dish or the "No photo yet" card when a photo is hidden?
