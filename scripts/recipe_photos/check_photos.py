"""Check that a recipe's own photo shows its dish (plan docs/plans/RECIPE_PHOTOS.md, step 5).

An open image-text model (CLIP ViT-B/32, OpenAI weights, MIT license, via open_clip) runs on the CPU. For each
own photo in data/raw/recipe_photos/manifest.csv it gives two scores against the dish's clean name
(dish_names.clean_title):

- clip_score: cosine of the image with "a photo of <dish>, a type of food." minus the mean cosine with a few
  generic food prompts ("a photo of food", ...). Above 0: the photo looks more like this dish than like food in
  general.
- rank_score: share of 50 random other dish names that fit the image worse than its own name (0 to 1; 1 = its own
  name beats all 50). A rank is more robust than a raw cosine.

Steps (each resumable; photos are untrusted data, so run with python -I):
  python -I scripts/recipe_photos/check_photos.py embed    # image vectors, cached in data/raw/photo_check/
  python -I scripts/recipe_photos/check_photos.py score    # data/processed/photo_check.parquet
  python -I scripts/recipe_photos/check_photos.py sample   # data/reference/photo_check_sample.csv (200 rows)
  python -I scripts/recipe_photos/check_photos.py eval     # precision/recall of cutoffs on the labelled rows
Food.com's own photos (notebook 11): the same steps with PHOTO_SET=foodcom (data/processed/photo_check_foodcom.parquet).
"""
from __future__ import annotations

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from everflavor.dish_names import clean_title

# Which photos: the first set (default) or Food.com's own photos from notebook 11 (PHOTO_SET=foodcom), each with
# its own cache and output so one run never overwrites the other's
SET = os.environ.get("PHOTO_SET", "")
PHOTOS = ROOT / "data" / "raw" / ("foodcom_photos" if SET == "foodcom" else "recipe_photos")
CACHE = ROOT / "data" / "raw" / ("photo_check_foodcom" if SET == "foodcom" else "photo_check")
MODELS = ROOT / "data" / "raw" / "clip_models"
OUT = ROOT / "data" / "processed" / ("photo_check_foodcom.parquet" if SET == "foodcom" else "photo_check.parquet")
SAMPLE = ROOT / "data" / "reference" / "photo_check_sample.csv"
ARCH, WEIGHTS = "ViT-B-32-quickgelu", "openai"
GENERIC = ["a photo of food.", "a photo of a dish.", "a photo of a meal on a plate.", "a close-up photo of food."]
N_OTHERS, CHUNK, BATCH, SEED = 50, 2048, 64, 2277


def manifest_so_far() -> pd.DataFrame:
    """While a Food.com download is still running there is no manifest.csv yet: the same rows from its log
    (results.jsonl) and its links, so the check can start on the photos already downloaded."""
    import json

    recs = []
    for line in (PHOTOS / "results.jsonl").read_text(encoding="utf-8").splitlines():
        try:
            recs.append(json.loads(line))
        except json.JSONDecodeError:   # the line being written right now
            continue
    res = pd.DataFrame(recs).drop_duplicates("url", keep="last")
    links = pd.read_csv(ROOT / "data" / "raw" / "foodcom_links.csv", usecols=["source", "recipe_id", "recipe_name", "url"])
    m = links.merge(res, on="url", how="inner")
    for c in ("file", "http_status", "image_error"):
        if c not in m:
            m[c] = None
    return m[["source", "recipe_id", "recipe_name", "file", "http_status", "image_error"]]


def own_photos() -> pd.DataFrame:
    """One row per recipe with a downloaded, readable own photo, with its clean dish name."""
    if SET == "foodcom" and not (PHOTOS / "manifest.csv").exists():
        m = manifest_so_far()
    else:
        m = pd.read_csv(PHOTOS / "manifest.csv", usecols=["source", "recipe_id", "recipe_name", "file", "http_status",
                                                           "image_error"])
    m = m[(m.http_status == 200) & m.image_error.isna() & m.file.notna()].drop_duplicates("recipe_id")
    m = m[[(PHOTOS / f).is_file() for f in m.file]].copy()
    m["dish_name"] = [str(clean_title(str(t))["dish_name"]) or str(t) for t in m.recipe_name]
    return m.reset_index(drop=True)


def load_model():  # type: ignore[no-untyped-def]
    import open_clip
    import torch

    torch.set_num_threads(max(1, (torch.get_num_threads() or 4)))
    model, _, preprocess = open_clip.create_model_and_transforms(ARCH, pretrained=WEIGHTS, cache_dir=str(MODELS))
    model.eval()
    return model, preprocess, open_clip.get_tokenizer(ARCH), torch


def cached() -> tuple[list[str], np.ndarray, np.ndarray]:
    """Every vector saved so far, with its file. A chunk names its own files; older chunks (before 2026-10-26)
    take theirs from files.csv by position."""
    names: list[str] = []
    vectors, oks = [], []
    old = pd.read_csv(CACHE / "files.csv").file.tolist() if (CACHE / "files.csv").exists() else []
    for c, path in enumerate(sorted(CACHE.glob("emb_*.npz"))):
        part = np.load(path)
        names += list(part["files"]) if "files" in part else old[c * CHUNK:c * CHUNK + len(part["emb"])]
        vectors.append(part["emb"])
        oks.append(part["ok"])
    if not vectors:
        return [], np.zeros((0, 512), np.float16), np.zeros(0, bool)
    return names, np.concatenate(vectors), np.concatenate(oks)


def embed() -> None:
    """Image vectors for every photo file not embedded yet, saved in chunks that name their files, so a stopped
    run resumes and a later run (more photos downloaded) only adds the new ones."""
    from PIL import Image

    CACHE.mkdir(parents=True, exist_ok=True)
    done = set(cached()[0])
    files = [f for f in sorted(own_photos().file.unique()) if f not in done]
    first = len(list(CACHE.glob("emb_*.npz")))
    print(f"{len(done)} photos embedded before, {len(files)} to embed", flush=True)
    if not files:
        return
    model, preprocess, _, torch = load_model()

    def prep(f: str):  # type: ignore[no-untyped-def]
        try:
            with Image.open(PHOTOS / f) as im:
                return preprocess(im.convert("RGB")), True
        except (OSError, ValueError, SyntaxError, Image.DecompressionBombError):  # an unreadable picture gets a zero vector and is reported as bad
            return torch.zeros(3, 224, 224), False

    t0 = time.time()
    n_chunks = (len(files) + CHUNK - 1) // CHUNK
    with ThreadPoolExecutor(4) as pool:
        for c in range(n_chunks):
            path = CACHE / f"emb_{first + c:03d}.npz"
            part = files[c * CHUNK:(c + 1) * CHUNK]
            vecs, oks = [], []
            for b in range(0, len(part), BATCH):
                got = list(pool.map(prep, part[b:b + BATCH]))
                x = torch.stack([g[0] for g in got])
                with torch.no_grad():
                    v = model.encode_image(x)
                vecs.append(torch.nn.functional.normalize(v, dim=-1).numpy().astype(np.float16))
                oks += [g[1] for g in got]
            np.savez(path, emb=np.concatenate(vecs), ok=np.array(oks), files=np.array(part))
            done = min(len(files), (c + 1) * CHUNK)
            print(f"chunk {c + 1}/{n_chunks}: {done} photos, {time.time() - t0:.0f} s", flush=True)
    print(f"embed done: {len(files)} photos in {time.time() - t0:.0f} s", flush=True)


def text_vectors(texts: list[str]) -> np.ndarray:
    """Text vectors, cached in CACHE/text_vectors.npz so a stopped run keeps what it has (Food.com has ~100k names)."""
    model, _, tokenizer, torch = load_model()
    path = CACHE / "text_vectors.npz"
    have: dict[str, np.ndarray] = {}
    if path.exists():
        part = np.load(path)
        have = dict(zip(part["texts"].tolist(), part["vecs"], strict=True))
    todo = [t for t in dict.fromkeys(texts) if t not in have]
    for b in range(0, len(todo), 256):
        with torch.no_grad():
            v = model.encode_text(tokenizer(todo[b:b + 256]))
        have.update(zip(todo[b:b + 256], torch.nn.functional.normalize(v, dim=-1).numpy(), strict=True))
        if (b // 256) % 20 == 19 or b + 256 >= len(todo):
            CACHE.mkdir(parents=True, exist_ok=True)
            np.savez(path, texts=np.array(list(have)), vecs=np.stack(list(have.values())))
            print(f"text vectors: {min(b + 256, len(todo))} of {len(todo)} new", flush=True)
    return np.stack([have[t] for t in texts])


def score() -> None:
    t0 = time.time()
    photos = own_photos()
    files, emb16, ok = cached()
    emb = emb16.astype(np.float32)
    row_of = {f: i for i, f in enumerate(files)}
    photos = photos[photos.file.map(lambda f: f in row_of and ok[row_of[f]])].reset_index(drop=True)
    img = emb[photos.file.map(row_of).to_numpy()]

    dishes = sorted(photos.dish_name.unique())
    dish_idx = {d: i for i, d in enumerate(dishes)}
    tv = text_vectors([f"a photo of {d}, a type of food." for d in dishes])
    gv = text_vectors(GENERIC)
    own = photos.dish_name.map(dish_idx).to_numpy()
    own_cos = np.einsum("ij,ij->i", img, tv[own])
    clip_score = own_cos - (img @ gv.T).mean(axis=1)

    rng = np.random.default_rng(SEED)
    others = rng.integers(0, len(dishes), size=(len(photos), N_OTHERS))
    clash = others == own[:, None]
    others[clash] = (others[clash] + 1) % len(dishes)  # never the recipe's own name
    other_cos = np.empty(others.shape, dtype=np.float32)
    for r in range(0, len(photos), 2048):  # in pieces: all at once needs ~11 GB for Food.com
        other_cos[r:r + 2048] = np.einsum("id,ikd->ik", img[r:r + 2048], tv[others[r:r + 2048]])
    rank_score = (other_cos < own_cos[:, None]).mean(axis=1)

    out = pd.DataFrame({"recipe_id": photos.recipe_id, "clip_score": clip_score.round(4),
                        "rank_score": rank_score.round(3)})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT, index=False)
    print(f"score done: {len(out)} recipes, {len(dishes)} dish names, {time.time() - t0:.0f} s")
    print(out[["clip_score", "rank_score"]].describe().round(3).to_string())


def sample() -> None:
    """200 photos, 20 from each of 10 bands of rank_score (ties broken by clip_score)."""
    if SAMPLE.exists():
        sys.exit(f"{SAMPLE} exists; delete it first (it may hold labels)")
    s = pd.read_parquet(OUT).merge(own_photos()[["recipe_id", "dish_name", "file"]], on="recipe_id")
    key = s.rank_score + s.clip_score / 10
    s["band"] = pd.qcut(key.rank(method="first"), 10, labels=False)
    pick = s.groupby("band", group_keys=False).sample(20, random_state=SEED)
    pick = pick.sort_values(["band", "recipe_id"])
    pick["matches_dish"], pick["checked_by"] = "", ""
    cols = ["recipe_id", "dish_name", "file", "clip_score", "rank_score", "matches_dish", "checked_by"]
    SAMPLE.parent.mkdir(parents=True, exist_ok=True)
    pick[cols].to_csv(SAMPLE, index=False)
    print(f"wrote {len(pick)} rows to {SAMPLE}")


def evaluate() -> None:
    """Precision and recall of 'hide below the cutoff' on the labelled rows (positive = wrong photo)."""
    lab = pd.read_csv(SAMPLE)
    lab = lab[lab.matches_dish.isin(["yes", "no"])]
    wrong = lab.matches_dish.eq("no")
    full = pd.read_parquet(OUT)
    print(f"labelled {len(lab)}: {wrong.sum()} wrong, {(~wrong).sum()} right")
    for col, cuts in (("rank_score", [0.3, 0.5, 0.6, 0.7, 0.8, 0.9]), ("clip_score", [0.0, 0.01, 0.02, 0.03, 0.04])):
        for c in cuts:
            hide = lab[col] < c
            tp = (hide & wrong).sum()
            prec = tp / hide.sum() if hide.sum() else float("nan")
            rec = tp / wrong.sum() if wrong.sum() else float("nan")
            print(f"{col} < {c}: hides {hide.sum()} of sample (precision {prec:.2f}, recall {rec:.2f}); "
                  f"hides {(full[col] < c).sum()} of {len(full)} photos")


if __name__ == "__main__":
    steps = {"embed": embed, "score": score, "sample": sample, "eval": evaluate}
    if len(sys.argv) != 2 or sys.argv[1] not in steps:
        sys.exit(f"usage: check_photos.py {{{'|'.join(steps)}}}")
    steps[sys.argv[1]]()
