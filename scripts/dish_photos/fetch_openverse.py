"""Free-licensed photos of dishes from Openverse (https://openverse.org), a second source after Wikimedia Commons.

Run from the project folder (reuses the helpers and the CLIP check of fetch_dish_photos.py):

    python -I scripts/dish_photos/fetch_openverse.py search --top 300 --dry             # score and report, write nothing
    python -I scripts/dish_photos/fetch_openverse.py search --top 300                   # new photos for photo-less dishes
    python -I scripts/dish_photos/fetch_openverse.py search --top 0 --upgrade-top 100   # cleaner photos for dishes that have one

--top N is how many photo-less dish names to search (by recipes covered); --upgrade-top N is how many dish names
that already have a photo to try for a cleaner one (the ones covering the most recipes). --dry writes nothing but
the API answers and thumbnails in the cache; --report FILE saves what it found as JSON.

Only the Openverse API is used (https://api.openverse.org/v1/images/), anonymous, one request a second, backing
off on 429. Only free licences: cc0, pdm, by, by-sa (any version), never nc or nd; Wikimedia is excluded because
fetch_dish_photos.py already searches Commons. Every answer is cached in
data/raw/dish_photos_cache/openverse_results.json, so nothing is asked twice. Thumbnails (Openverse's own
thumbnail endpoint) are cached in data/raw/dish_photos_cache/openverse_thumbs/o<id>.<ext>, so nothing is
downloaded twice. A picture that looks like one already stored (perceptual hash, Hamming distance <= 4) is skipped.

A photo is accepted with the same CLIP check as a Commons search photo (fdp.passes with search=True). An upgrade
replaces the current photo only if the new one scores at least 0.02 higher for the same dish name, is at least
400 px on its short side and passes; the replaced rows go to dish_photos_hidden.parquet (nothing is deleted).
Written: data/raw/dish_photos/v<id>.<ext>, data/processed/dish_photos.parquet, manifest.csv, the hidden file.
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "src")
import fetch_dish_photos as fdp

API = "https://api.openverse.org/v1/images/"
LICENSES = "cc0,pdm,by,by-sa"
FREE_CODES = {"cc0", "pdm", "by", "by-sa"}
RESULTS = fdp.CACHE / "openverse_results.json"
THUMBS = fdp.CACHE / "openverse_thumbs"
PHASHES = fdp.CACHE / "openverse_phash.json"   # file name and size -> perceptual hash of the stored photos
UPGRADE_MARGIN = 0.02    # the new photo's clip_score must be this much higher than the current one
UPGRADE_MIN_SIDE = 400   # px on the short side of the original
HASH_DISTANCE = 4        # near-copy: Hamming distance up to this
PER_NAME = 5             # candidates kept per name


# ---------------------------------------------------------------- pure rules (tested without network)
def is_free(code: str | None) -> bool:
    """Only cc0, pdm, by and by-sa; never nc or nd."""
    return (code or "").lower() in FREE_CODES


def license_label(code: str, version: str | None) -> str:
    """'CC BY 2.0', 'CC BY-SA 4.0', 'CC0 1.0', or 'Public domain' for the PD Mark."""
    code = code.lower()
    if code == "pdm":
        return "Public domain"
    base = {"cc0": "CC0", "by": "CC BY", "by-sa": "CC BY-SA"}[code]
    return f"{base} {version}".strip() if version else base


def credit_text(label: str, creator: str, lic: str, source: str) -> str:
    return f"Photo of {label}: {creator}, {lic}, via {source} on Openverse"


def upgrade_ok(old_clip: float | None, new_clip: float, width: int | None, height: int | None,
               passed: bool) -> bool:
    """Replace a photo only if the new one is clearly better, big enough and passes the CLIP check."""
    if old_clip is None or not passed or not width or not height:
        return False
    return new_clip >= old_clip + UPGRADE_MARGIN and min(width, height) >= UPGRADE_MIN_SIDE


def near_duplicate(h: object, known: list[object], distance: int = HASH_DISTANCE) -> bool:
    """True if the perceptual hash h is within `distance` bits of any known hash (imagehash objects)."""
    return any(h - k <= distance for k in known)  # type: ignore[operator]


def keep_candidate(r: dict, phrase: str) -> bool:
    """A free, photo-like result whose title or tags carry every word of the phrase and is not a package or shop."""
    need = {w for w in fdp.key(phrase).split() if w not in fdp.STOP}
    title = r.get("title") or ""
    tags = " ".join(t.get("name", "") for t in r.get("tags") or [])
    words = set(fdp.key(f"{title} {tags}").split())
    w, h = r.get("width") or 0, r.get("height") or 0
    if w and h and (min(w, h) < 300 or max(w, h) / min(w, h) > 2.5):
        return False
    return bool(is_free(r.get("license")) and need <= words and not fdp.SEARCH_BAD.search(title)
                and not fdp.BAD_WORDS.search(title) and (r.get("thumbnail") or "").startswith("https://")
                and not r.get("mature"))


def slim(r: dict) -> dict:
    """What we keep of one API result."""
    return {k: r.get(k) for k in ("id", "title", "foreign_landing_url", "creator", "license", "license_version",
                                  "source", "width", "height", "thumbnail")}


# ---------------------------------------------------------------- network, paced to one request a second
def api_search(s: requests.Session, phrase: str) -> dict:
    params = {"q": phrase, "license": LICENSES, "excluded_source": "wikimedia", "mature": "false",
              "page_size": 10}
    return fdp.get_json(s, API, params, pace=1.0)  # backs off on 429 with Retry-After


def fetch_thumb(s: requests.Session, c: dict, bad: set[str]) -> Path | None:
    """The cached thumbnail of a candidate, downloaded once (1 request a second, backing off on 429)."""
    THUMBS.mkdir(parents=True, exist_ok=True)
    have = sorted(THUMBS.glob(f"o{c['id']}.*"))
    if have:
        return have[0]
    if c["id"] in bad:
        return None
    for t in range(5):
        try:
            r = s.get(c["thumbnail"], timeout=60)
            if r.status_code == 200:
                time.sleep(1.0)
                if len(r.content) < fdp.MIN_BYTES:
                    bad.add(c["id"])
                    return None
                kind = r.headers.get("Content-Type", "").split(";")[0]
                p = THUMBS / f"o{c['id']}.{ {'image/png': 'png', 'image/webp': 'webp'}.get(kind, 'jpg') }"
                p.write_bytes(r.content)
                return p
            if r.status_code in (400, 404):
                bad.add(c["id"])
                return None
            print("  http", r.status_code, "retry", t, flush=True)
            time.sleep(float(r.headers.get("Retry-After", 15 * (t + 1))))
        except requests.RequestException as e:
            print("  error", e, "retry", t, flush=True)
            time.sleep(15 * (t + 1))
    return None


def stored_hashes() -> dict[str, object]:
    """Perceptual hashes of every photo in data/raw/dish_photos (cached by file name and size)."""
    import imagehash
    from PIL import Image
    cache = json.loads(PHASHES.read_text(encoding="utf8")) if PHASHES.exists() else {}
    out: dict[str, object] = {}
    for f in sorted(fdp.OUT.iterdir()):
        if f.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            continue
        ck = f"{f.name}|{f.stat().st_size}"
        if ck not in cache:
            try:
                with Image.open(f) as im:
                    cache[ck] = str(imagehash.phash(im.convert("RGB")))
            except (OSError, ValueError, Image.DecompressionBombError):
                continue
        out[f.name] = imagehash.hex_to_hash(cache[ck])
    fdp.save_json(cache, PHASHES)
    return out


def hash_of(path: Path) -> object | None:
    import imagehash
    from PIL import Image
    try:
        with Image.open(path) as im:
            return imagehash.phash(im.convert("RGB"))
    except (OSError, ValueError, Image.DecompressionBombError):
        return None


# ---------------------------------------------------------------- the stage
def old_clip(file: str, label: str) -> float | None:
    """The current photo's clip_score for this dish name (cached, or scored now)."""
    if not Path(file).exists():
        return None
    sc = fdp.score_images([(file, label)])
    m = sc[(sc.image_file == file) & (sc["name"] == label)]
    return float(m.clip_score.iloc[0]) if len(m) else None


def stage_search(top: int, upgrade_top: int, dry: bool, report: str | None) -> None:
    fdp.Opts.extend = True
    res = fdp.load_json(RESULTS) if RESULTS.exists() else {}
    bad = set(res.get("_bad_thumbs", []))
    done = {k for k, v in res.items() if k != "_bad_thumbs" and v.get("done")}

    # (a) photo-less names, same grouping as the Commons search
    ph = fdp.photoless_recipes()
    cn = fdp.clean_names(ph.recipe_name.dropna().astype(str).unique().tolist())
    ph["core"] = ph.recipe_name.astype(str).map(cn).map(fdp.core_phrase)
    ph = ph[ph.core != ""].copy()
    ph["gk"] = ph.core.map(fdp.key)
    groups = ph.groupby("gk").agg(n=("recipe_id", "size"), phrase=("core", lambda x: x.value_counts().index[0]))
    groups = groups[~groups.index.isin(done)].reset_index().sort_values(["n", "gk"], ascending=[False, True])
    new_t = groups.head(top)
    targets = [{"gk": g, "phrase": p, "kind": "new", "n": int(n)} for g, p, n in zip(new_t.gk, new_t.phrase, new_t.n)]

    # (b) names that already have a photo, the ones covering the most recipes
    dp = fdp.existing_dish_photos()
    if upgrade_top and len(dp):
        dp = dp[~dp.dish_qid.astype(str).str.startswith("openverse:")].copy()
        dp["gk"] = dp.dish_label.map(fdp.key)
        g2 = dp.groupby("gk").agg(n=("recipe_id", "size"), phrase=("dish_label", "first"))
        g2 = g2[~g2.index.isin(done)].reset_index().sort_values(["n", "gk"], ascending=[False, True]).head(upgrade_top)
        targets += [{"gk": g, "phrase": p, "kind": "up", "n": int(n)} for g, p, n in zip(g2.gk, g2.phrase, g2.n)]
    n_new = sum(t["kind"] == "new" for t in targets)
    print(f"photo-less recipes {len(ph)} in {len(groups)} unsearched names; this round "
          f"{n_new} new names, {len(targets) - n_new} upgrade names", flush=True)

    s = fdp.session()
    searched = 0
    for i, t in enumerate(targets):
        if t["gk"] in res:  # asked before (a --dry round or a stopped run)
            continue
        j = api_search(s, t["phrase"])
        cands = [slim(r) for r in j.get("results", []) if keep_candidate(r, t["phrase"])][:PER_NAME]
        res[t["gk"]] = {"phrase": t["phrase"], "hits": len(j.get("results", [])), "cands": cands}
        searched += 1
        if searched % 25 == 0:
            fdp.save_json(res, RESULTS)
            print(f"  searched {i + 1}/{len(targets)}", flush=True)
    fdp.save_json(res, RESULTS)

    print("thumbnails", flush=True)
    paths: dict[str, Path] = {}
    for t in targets:
        for c in res[t["gk"]]["cands"]:
            p = fetch_thumb(s, c, bad)
            if p is not None:
                paths[c["id"]] = p
    res["_bad_thumbs"] = sorted(bad)
    fdp.save_json(res, RESULTS)

    # near-copies of photos already stored are skipped
    known = list(stored_hashes().values())
    dup = set()
    for cid, p in paths.items():
        h = hash_of(p)
        if h is not None and near_duplicate(h, known):
            dup.add(cid)

    cur = {gk: grp for gk, grp in dp.groupby("gk")} if upgrade_top and len(dp) else {}
    pairs = [(paths[c["id"]].as_posix(), t["phrase"]) for t in targets for c in res[t["gk"]]["cands"]
             if c["id"] in paths and c["id"] not in dup]
    sc = fdp.score_images(pairs).drop_duplicates(["image_file", "name"]).set_index(["image_file", "name"])

    best: dict[str, dict] = {}
    ups: list[dict] = []
    stat = {"rejected": 0, "none": 0, "dup": 0, "cands": 0, "up_rejected": 0}
    for t in targets:
        gk, phrase = t["gk"], t["phrase"]
        cs = res[gk]["cands"]
        stat["cands"] += len(cs)
        stat["dup"] += sum(c["id"] in dup for c in cs)
        scored = [(sc.loc[(paths[c["id"]].as_posix(), phrase)], c) for c in cs
                  if c["id"] in paths and c["id"] not in dup and (paths[c["id"]].as_posix(), phrase) in sc.index]
        if not scored:
            stat["none"] += 1
            continue
        ok = [(x, c) for x, c in scored if fdp.passes(x.clip_score, x.rank_score, x.nonfood, search=True)]
        if t["kind"] == "new":
            if ok:
                x, c = max(ok, key=lambda p: p[0].clip_score)
                best[gk] = {**c, "clip": float(x.clip_score), "path": paths[c["id"]].as_posix(), "label": phrase,
                            "gk": gk, "n": t["n"]}
            else:
                stat["rejected"] += 1
            continue
        old_file = str(cur[gk].image_file.iloc[0])
        oc = old_clip(old_file, phrase)
        pick = None
        for x, c in sorted(ok, key=lambda p: -p[0].clip_score):
            if upgrade_ok(oc, float(x.clip_score), c.get("width"), c.get("height"), True):
                pick = (x, c)
                break
        if pick:
            x, c = pick
            ups.append({**c, "clip": float(x.clip_score), "old_clip": oc, "path": paths[c["id"]].as_posix(),
                        "label": phrase, "gk": gk, "n": t["n"], "old_file": old_file})
        else:
            stat["up_rejected"] += 1

    print(f"ROUND names searched {len(targets)} candidates {stat['cands']} near-copies skipped {stat['dup']}\n"
          f"  new photos: names {len(best)} recipes {sum(b['n'] for b in best.values())} "
          f"rejected_by_clip {stat['rejected']}\n"
          f"  upgrades: {len(ups)} (kept the old photo {stat['up_rejected']})\n"
          f"  no candidates or nothing scorable: {stat['none']}", flush=True)
    for u in ups:
        print(f"  upgrade {u['label']!r}: {u['old_clip']:.3f} -> {u['clip']:.3f}  ({u['n']} recipes)")
    if report:
        Path(report).write_text(json.dumps({"new": list(best.values()), "up": ups}, default=str), encoding="utf8")
    if dry:
        return
    write_all(res, targets, best, ups, ph)


def row_for(c: dict, label: str, gk: str, dst: Path) -> dict:
    lic = license_label(c["license"], c.get("license_version"))
    creator = (c.get("creator") or "author not stated")[:200]
    return {"dish_qid": f"openverse:{gk}", "dish_label": label, "image_file": dst.as_posix(),
            "thumb_url": c["thumbnail"], "file_page": c.get("foreign_landing_url") or "", "license": lic,
            "author": creator, "credit": credit_text(label, creator, lic, c.get("source") or "the web")}


def write_all(res: dict, targets: list[dict], best: dict, ups: list[dict], ph: pd.DataFrame) -> None:
    """Write new rows, replace upgraded ones (old rows to HIDDEN), append to the manifest."""
    for t in targets:
        res[t["gk"]]["done"] = True
    fdp.save_json(res, RESULTS)
    out = fdp.existing_dish_photos()
    cols = list(out.columns)
    dtypes = out.dtypes.to_dict()
    man, rows = [], []
    for gk, c in best.items():
        dst = fdp.OUT / f"v{c['id']}{Path(c['path']).suffix}"
        if not dst.exists():
            shutil.copyfile(c["path"], dst)
        d = row_for(c, c["label"], gk, dst)
        man.append({**d, "recipes": c["n"], "commons_file": f"openverse:{c['id']}"})
        rows.append(ph[ph.gk == gk][["recipe_id"]].assign(**d))
    new = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=cols)
    new = new[~new.recipe_id.isin(set(out.recipe_id))]

    hide = []
    keys = out.dish_label.map(fdp.key)
    for u in ups:
        dst = fdp.OUT / f"v{u['id']}{Path(u['path']).suffix}"
        if not dst.exists():
            shutil.copyfile(u["path"], dst)
        d = row_for(u, u["label"], u["gk"], dst)
        man.append({**d, "recipes": u["n"], "commons_file": f"openverse:{u['id']}"})
        m = keys == u["gk"]
        hide.append(out[m])  # the old rows, so the upgrade can be undone
        for k, v in d.items():
            out.loc[m, k] = v
    if hide:
        h = pd.concat(hide)
        hidden = pd.concat([pd.read_parquet(fdp.HIDDEN), h]) if fdp.HIDDEN.exists() else h
        hidden.to_parquet(fdp.HIDDEN, index=False)
    pd.concat([out, new[cols].astype(dtypes)], ignore_index=True).to_parquet(
        fdp.PROC / "dish_photos.parquet", index=False)
    if man:
        pd.concat([pd.read_csv(fdp.OUT / "manifest.csv"), pd.DataFrame(man)], ignore_index=True).to_csv(
            fdp.OUT / "manifest.csv", index=False, encoding="utf-8")
    print("rows added", len(new), "rows upgraded", sum(len(x) for x in hide))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=["search"])
    ap.add_argument("--top", type=int, default=300, help="photo-less dish names to search (default %(default)s)")
    ap.add_argument("--upgrade-top", type=int, default=0, help="dish names that have a photo to try to improve")
    ap.add_argument("--dry", action="store_true", help="score and report, write nothing")
    ap.add_argument("--report", help="save the accepted candidates and upgrades as JSON (for a contact sheet)")
    a = ap.parse_args()
    stage_search(a.top, a.upgrade_top, a.dry, a.report)
