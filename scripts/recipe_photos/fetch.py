"""Download recipe photos once per URL (resumable), then write manifest.csv.

usage: python -I fetch.py LINKS_CSV PHOTO_DIR [--sample N]
"""
import csv
import hashlib
import io
import json
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from PIL import Image

LINKS, ROOT = Path(sys.argv[1]), Path(sys.argv[2])
SAMPLE = int(sys.argv[sys.argv.index("--sample") + 1]) if "--sample" in sys.argv else 0
UA = "EverFlavorAI-capstone-photo-index/0.1 (student research; one download per photo)"
LOG = ROOT / ("results_sample.jsonl" if SAMPLE else "results.jsonl")
lock = threading.Lock()
local = threading.local()


def sess():
    if not hasattr(local, "s"):
        local.s = requests.Session()
        local.s.headers["User-Agent"] = UA
    return local.s


def sniff(b):
    """File type from the first bytes (the S3 host sends application/octet-stream)."""
    if b[:3] == b"\xff\xd8\xff":
        return "jpg"
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        return "webp"
    if b[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if b[4:12] in (b"ftypavif", b"ftypheic", b"ftypmif1"):
        return "avif"
    return None


def ahash(img):
    g = img.convert("L").resize((8, 8), Image.LANCZOS)
    px = list(g.tobytes())
    m = sum(px) / 64
    return f"{sum(1 << i for i, p in enumerate(px) if p > m):016x}"


def describe(path):
    data = path.read_bytes()
    out = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "format": sniff(data)}
    try:
        with Image.open(io.BytesIO(data)) as im:
            out["width"], out["height"] = im.size
            out["ahash"] = ahash(im)
    except Exception as e:  # noqa: BLE001  (any file that is not a readable image is recorded, not fatal)
        out["image_error"] = type(e).__name__
    return out


def fetch(source, url):
    sha1 = hashlib.sha1(url.encode(), usedforsecurity=False).hexdigest()   # a file name, not security
    d = ROOT / source
    if d.exists():
        for p in d.glob(sha1 + ".*"):
            if not p.name.endswith(".part"):
                return {"url": url, "file": str(p.relative_to(ROOT)).replace("\\", "/"), "http_status": 200,
                        "content_type": None, "reused": True, **describe(p)}
    last = {}
    for attempt in range(4):
        try:
            r = sess().get(url, timeout=(10, 40))
            ct = (r.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            if r.status_code == 200:
                ext = sniff(r.content) or "bin"
                d.mkdir(parents=True, exist_ok=True)
                p = d / f"{sha1}.{ext}"
                tmp = p.with_name(p.name + ".part")
                tmp.write_bytes(r.content)
                tmp.replace(p)
                time.sleep(0.1)
                return {"url": url, "file": str(p.relative_to(ROOT)).replace("\\", "/"), "http_status": 200,
                        "content_type": ct, **describe(p)}
            last = {"url": url, "http_status": r.status_code, "content_type": ct, "error": f"http_{r.status_code}"}
            if r.status_code in (400, 401, 403, 404, 410):
                return last
        except requests.RequestException as e:
            last = {"url": url, "http_status": None, "error": type(e).__name__}
        time.sleep(2 ** attempt + random.random())
    return last


def main():
    links = pd.read_csv(LINKS)
    urls = links.drop_duplicates("url")[["source", "url"]]
    if SAMPLE:
        urls = urls.sample(SAMPLE, random_state=7)
    done = {}
    if LOG.exists():
        for line in LOG.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            if rec.get("http_status") == 200 or str(rec.get("error", "")).startswith("http_4"):
                done[rec["url"]] = rec
    todo = [(s, u) for s, u in urls.itertuples(index=False) if u not in done]
    print(f"{len(urls)} urls, {len(done)} done, {len(todo)} to fetch", flush=True)
    t0, n, nbytes, nfail = time.time(), 0, 0, 0
    ROOT.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(4) as ex, LOG.open("a", encoding="utf-8") as log:
        futs = [ex.submit(fetch, s, u) for s, u in todo]
        for f in as_completed(futs):
            rec = f.result()
            rec["downloaded_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            with lock:
                log.write(json.dumps(rec) + "\n")
                log.flush()
            done[rec["url"]] = rec
            n += 1
            nbytes += rec.get("bytes", 0)
            nfail += rec.get("http_status") != 200
            if n % 500 == 0 or n == len(todo):
                el = time.time() - t0
                print(f"{n}/{len(todo)} fetched, {nfail} failed, {nbytes/1e6:.0f} MB, {el/60:.1f} min, "
                      f"eta {(len(todo)-n)*el/n/60:.0f} min", flush=True)
    res = pd.DataFrame(done.values())
    if SAMPLE:
        ok = res[res.http_status == 200]
        print(res.http_status.value_counts(dropna=False).to_dict())
        print("content types", ok.content_type.value_counts().to_dict(), "formats", ok.format.value_counts().to_dict())
        print("bytes median", ok.bytes.median(), "mean", ok.bytes.mean(), "max", ok.bytes.max())
        print("dims median", ok.width.median(), ok.height.median())
        tot = links.drop_duplicates("url").shape[0]
        print(f"estimated total {ok.bytes.mean()*tot/1e9:.2f} GB for {tot} urls")
        return
    m = links.merge(res, on="url", how="left")
    cols = ["source", "recipe_id", "recipe_name", "url", "file", "http_status", "bytes", "width", "height",
            "content_type", "format", "sha256", "ahash", "downloaded_at", "in_full_data", "in_demo",
            "error", "image_error"]
    for c in cols:
        if c not in m:
            m[c] = None
    m[cols].to_csv(ROOT / "manifest.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    print("manifest rows", len(m))


main()
