"""Fetch the approved dish photos (`data/knowledge/media/approved_image_queue.json`) into a staging folder, score them
with the photo check (CLIP) and make contact sheets for a person to check by eye. Nothing reaches the app here:
`dish_photos.parquet` is not touched until the `apply` stage, after the review.

Run from the project folder, stage by stage (each is resumable):

    python -I scripts/dish_photos/fetch_approved.py download   # 480 px thumbnails, 1 s apart
    python -I scripts/dish_photos/fetch_approved.py score      # CLIP clip_score, rank_score, nonfood
    python -I scripts/dish_photos/fetch_approved.py sheets     # contact sheets of 16 for the check by eye
    python -I scripts/dish_photos/fetch_approved.py apply      # after the review: the photos people kept

Staging: data/raw/dish_photos_approved/ (git-ignored): the photos, staging.parquet and sheets/. The check by eye
goes into data/reference/dish_photo_review.csv (keep = no with a reason), as for every dish photo; `apply` takes
a photo only when it passed the CLIP check, was not marked "no", and its dish's sheet is listed in
data/reference/approved_photo_sheets_checked.txt (one sheet name per line, with who checked it).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fetch_tools as ft
from fetch_dish_photos import UA, WIDTH, passes, score_images

QUEUE = Path("data/knowledge/media/approved_image_queue.json")
STAGE = Path("data/raw/dish_photos_approved")
TABLE = STAGE / "staging.parquet"
SHEETS = STAGE / "sheets"
REVIEW = Path("data/reference/dish_photo_review.csv")
CHECKED = Path("data/reference/approved_photo_sheets_checked.txt")
PHOTOS = Path("data/processed/dish_photos.parquet")
PER_SHEET = 16


def queue() -> list[dict]:
    return json.loads(QUEUE.read_text(encoding="utf-8"))["dishes"]


def stage_download() -> None:
    """The 480 px thumbnail of each approved file (the URL from the Commons API), skipping ones already staged."""
    rows = pd.read_parquet(TABLE).to_dict("records") if TABLE.exists() else []
    done = {r["dish_qid"] for r in rows}
    todo = [d for d in queue() if d["dish_id"] not in done]
    print("staged", len(done), "to fetch", len(todo), flush=True)
    s = requests.Session()
    s.headers["User-Agent"] = UA
    for i in range(0, len(todo), 25):
        part = todo[i:i + 25]
        j = ft.get_json(s, "https://commons.wikimedia.org/w/api.php", {
            "action": "query", "titles": "|".join("File:" + d["commons_file"] for d in part), "prop": "imageinfo",
            "iiprop": "url", "iiurlwidth": WIDTH, "format": "json", "formatversion": 2})
        norm = {n["to"]: n["from"] for n in j.get("query", {}).get("normalized", [])}
        thumbs = {norm.get(p["title"], p["title"])[5:]: (p.get("imageinfo") or [{}])[0].get("thumburl", "")
                  for p in j.get("query", {}).get("pages", [])}
        for d in part:
            url = thumbs.get(d["commons_file"], "")
            path = STAGE / f"{d['dish_id']}.jpg"
            status = ft.download_image(s, url, path, pace=1.0) if url else "no thumbnail"
            rows.append({"dish_qid": d["dish_id"], "dish_label": d["dish_name"], "image_file": path.as_posix(),
                         "thumb_url": url, "file_page": d["file_page"], "license": d["license"],
                         "author": d["author"], "credit": d["credit"], "status": status})
        ft.save_table(pd.DataFrame(rows), TABLE)
        print(f"  {min(i + 25, len(todo))}/{len(todo)}", flush=True)
    print(pd.DataFrame(rows).status.value_counts().to_dict())


def stage_score() -> None:
    """The photo check's scores for each staged photo against its dish's name, and whether it passes."""
    t = pd.read_parquet(TABLE)
    got = t[t.status == "got"]
    s = score_images([(f, n.lower()) for f, n in zip(got.image_file, got.dish_label)])
    s = s.drop_duplicates(["image_file", "name"], keep="last").set_index(["image_file", "name"])
    for col in ("clip_score", "rank_score", "nonfood"):
        t[col] = [s[col].get((f, n.lower())) if st == "got" else None
                  for f, n, st in zip(t.image_file, t.dish_label, t.status)]
    t["clip_pass"] = [bool(st == "got" and passes(c, r, nf)) for st, c, r, nf in
                      zip(t.status, t.clip_score, t.rank_score, t.nonfood)]
    ft.save_table(t, TABLE)
    print("passed the photo check", int(t.clip_pass.sum()), "of", int((t.status == "got").sum()))


def stage_sheets() -> None:
    """Contact sheets of 16, the photos that failed the photo check first, each labelled with dish and score."""
    from PIL import Image, ImageDraw
    t = pd.read_parquet(TABLE)
    t = t[t.status == "got"].sort_values(["clip_pass", "clip_score"]).reset_index(drop=True)
    SHEETS.mkdir(parents=True, exist_ok=True)
    index = []
    for n, start in enumerate(range(0, len(t), PER_SHEET)):
        part = t.iloc[start:start + PER_SHEET]
        sheet = Image.new("RGB", (4 * 260, 4 * 290), "white")
        draw = ImageDraw.Draw(sheet)
        for k, r in enumerate(part.itertuples()):
            x, y = (k % 4) * 260, (k // 4) * 290
            try:
                with Image.open(r.image_file) as im:
                    im.thumbnail((250, 250))
                    sheet.paste(im.convert("RGB"), (x + 5, y + 5))
            except OSError:
                draw.text((x + 10, y + 100), "cannot open", fill="red")
            mark = "" if r.clip_pass else "  FAILED CHECK"
            draw.text((x + 5, y + 258), f"{r.dish_label[:30]}", fill="black")
            draw.text((x + 5, y + 272), f"{r.dish_qid}  {r.clip_score:.3f}{mark}", fill="red" if mark else "gray")
        name = f"sheet_{n:03d}.jpg"
        sheet.save(SHEETS / name, quality=85)
        index += [{"sheet": name, "dish_qid": r.dish_qid, "dish_label": r.dish_label} for r in part.itertuples()]
    pd.DataFrame(index).to_csv(SHEETS / "index.csv", index=False)
    print(len(index), "photos on", n + 1 if index else 0, "sheets in", SHEETS)


def stage_apply() -> None:
    """Add the reviewed photos to dish_photos.parquet: passed the check, not marked "no", on a checked sheet."""
    if not CHECKED.exists():
        raise SystemExit(f"{CHECKED} not found: no sheet has been checked by a person yet, so nothing is added")
    sheets = {line.split()[0] for line in CHECKED.read_text(encoding="utf-8").splitlines() if line.strip()}
    index = pd.read_csv(SHEETS / "index.csv")
    checked = set(index[index.sheet.isin(sheets)].dish_qid)
    rejected = set(pd.read_csv(REVIEW).query("keep == 'no'").dish_qid)
    t = pd.read_parquet(TABLE)
    keep = t[t.clip_pass & t.dish_qid.isin(checked) & ~t.dish_qid.isin(rejected)]
    print(f"{len(keep)} photos to add (checked {len(checked)}, rejected by eye {len(rejected & checked)})")
    # recipes get these photos through the app's dish match; the table links a photo to the dish's recipes
    raise SystemExit("apply is written for after the review; link recipes and append when the team asks")


if __name__ == "__main__":
    stages = {"download": stage_download, "score": stage_score, "sheets": stage_sheets, "apply": stage_apply}
    if len(sys.argv) != 2 or sys.argv[1] not in stages:
        raise SystemExit(f"usage: fetch_approved.py {{{'|'.join(stages)}}}")
    stages[sys.argv[1]]()
