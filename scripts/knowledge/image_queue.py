"""The approved image collection queue: which Wikidata images of our dishes pass the photo pipeline's licence and
credit rules, so the pipeline can fetch them once the team says yes. Only file information is read from the
Wikimedia Commons API (licence, author, size, type); no image is downloaded and nothing is shown in the app.

    python scripts/knowledge/image_queue.py   # data/knowledge/media/commons_meta.json, approved_image_queue.json

"Approved" means the file passes the automatic rules; a person still looks at every photo after it is fetched
(`data/reference/dish_photo_review.csv`), as for every dish photo. Run after `media_audit.py`.
"""
from __future__ import annotations

import html
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
MEDIA = ROOT / "data" / "knowledge" / "media"
META = MEDIA / "commons_meta.json"
OUT = MEDIA / "approved_image_queue.json"
REPORT = ROOT / "docs" / "audits" / "image_coverage_report.md"
SECTION = "## Approved for collection"
sys.path.insert(0, str(ROOT / "scripts" / "dish_photos"))

from fetch_dish_photos import (  # the pipeline's own rules
    BAD_WORDS,
    FREE,
    author_name,
    commons_credit,
)

UA = {"User-Agent": "EverFlavorImageQueue/0.1 (student project; https://github.com/Chloe-Tu2/The-EverFlavor-AI)"}
MIN_SIDE = 400                       # smaller files make a blurry card
PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp"}
PRIORITY = {"high": 0, "medium": 1, "low": 2}


EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def no_email(text: str) -> str:
    """Commons fields sometimes hold the uploader's e-mail address; it is never stored or passed on."""
    return EMAIL.sub("[e-mail removed]", text)


def fetch_meta(files: list[str], known: dict[str, dict]) -> dict[str, dict]:
    """Commons file information for the files not cached yet, 25 per request, 1 s apart."""
    todo = sorted(set(files) - set(known))
    with requests.Session() as s:
        s.headers.update(UA)
        for i in range(0, len(todo), 25):
            r = s.get("https://commons.wikimedia.org/w/api.php", timeout=60, params={
                "action": "query", "titles": "|".join("File:" + t for t in todo[i:i + 25]), "prop": "imageinfo",
                "iiprop": "url|extmetadata|size|mime", "format": "json", "formatversion": 2})
            r.raise_for_status()
            j = r.json()
            norm = {n["to"]: n["from"] for n in j.get("query", {}).get("normalized", [])}
            for p in j.get("query", {}).get("pages", []):
                ii = (p.get("imageinfo") or [{}])[0]
                md = ii.get("extmetadata", {})
                known[norm.get(p["title"], p["title"])[5:]] = {
                    "file_page": ii.get("descriptionurl", ""), "width": ii.get("width"), "height": ii.get("height"),
                    "mime": ii.get("mime", ""), "missing": bool(p.get("missing")),
                    "license": re.sub(r"\s+", " ", html.unescape(md.get("LicenseShortName", {}).get("value", ""))).strip(),
                    "author": author_name(md.get("Artist", {}).get("value", "")),
                    "description": no_email(re.sub(r"<[^>]+>", "", md.get("ImageDescription", {}).get("value", "")))[:300]}
            print(f"  commons {min(i + 25, len(todo))}/{len(todo)}", flush=True)
            time.sleep(1)
    return known


def check(file: str, m: dict) -> list[str]:
    """Why a file cannot be queued; [] when it passes every rule."""
    if not m or m.get("missing"):
        return ["the file is not on Commons"]
    why = []
    if not FREE.match(m.get("license", "")):
        why.append(f"licence not free ({m.get('license') or 'none given'})")
    if not m.get("author"):
        why.append("no author to credit")
    if m.get("mime") not in PHOTO_TYPES:
        why.append(f"not a photo ({m.get('mime') or 'unknown type'})")
    if min(m.get("width") or 0, m.get("height") or 0) < MIN_SIDE:
        why.append(f"smaller than {MIN_SIDE} px")
    if BAD_WORDS.search(f"{file} {m.get('description', '')}"):
        why.append("named or described as a map, logo, drawing or label, not a photo")
    return why


def main() -> None:
    audit = json.loads((MEDIA / "dish_media_audit.json").read_text(encoding="utf-8"))["dishes"]
    queue = json.loads((MEDIA / "image_priority_queue.json").read_text(encoding="utf-8"))
    prio = {r["dish_id"]: r.get("priority", "low") for r in queue.get("dishes", queue.get("queue", []))}
    wanted = [d for d in audit if d["review_status"] == "fetch_candidate" and d.get("wikidata_image")]
    known = json.loads(META.read_text(encoding="utf-8")) if META.exists() else {}
    known = fetch_meta([d["wikidata_image"] for d in wanted], known)
    for m in known.values():   # entries cached before the e-mail rule too
        m["description"], m["author"] = no_email(m.get("description", "")), no_email(m.get("author", ""))
    META.write_text(json.dumps(known, ensure_ascii=False, indent=0, sort_keys=True) + "\n", encoding="utf-8",
                    newline="\n")
    approved, rejected = [], []
    for d in wanted:
        f = d["wikidata_image"]
        m = known.get(f, {})
        why = check(f, m)
        row = {"dish_id": d["dish_id"], "dish_name": d["dish_name"], "country": d["country"],
               "now_shows": d["best_level"], "priority": prio.get(d["dish_id"], "low"), "commons_file": f,
               "file_page": m.get("file_page", ""), "license": m.get("license", ""), "author": m.get("author", "")}
        if why:
            rejected.append({**row, "reasons": why})
        else:
            approved.append({**row, "width": m["width"], "height": m["height"],
                             "credit": commons_credit(d["dish_name"], m["author"], m["license"]),
                             "status": "approved_for_collection"})
    approved.sort(key=lambda r: (PRIORITY.get(r["priority"], 3), r["country"], r["dish_name"]))
    reasons: dict[str, int] = {}
    for r in rejected:
        for w in r["reasons"]:
            k = w.split(" (")[0]
            reasons[k] = reasons.get(k, 0) + 1
    OUT.write_text(json.dumps({
        "about": "Wikidata images of our dishes that pass the photo pipeline's rules (free licence, an author to "
                 "credit, a photo type, at least 400 px, not a map or drawing). Not downloaded and not shown: the "
                 "pipeline fetches them when the team agrees, and a person checks each photo by eye.",
        "built_on": date.today().isoformat(), "by": "scripts/knowledge/image_queue.py",
        "asked": len(wanted), "approved": len(approved), "rejected": len(rejected),
        "rejected_by_reason": dict(sorted(reasons.items(), key=lambda x: -x[1])),
        "dishes": approved, "rejected_dishes": rejected}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8", newline="\n")
    add_to_report(len(wanted), approved, reasons)
    print(f"{len(approved)} of {len(wanted)} approved for collection; rejected {reasons}")


def add_to_report(asked: int, approved: list[dict], reasons: dict[str, int]) -> None:
    """The queue's section at the end of the image report (`media_audit.py` writes the rest), replacing an old one."""
    text = REPORT.read_text(encoding="utf-8").split(SECTION)[0].rstrip("\n")
    prio = {p: sum(r["priority"] == p for r in approved) for p in PRIORITY}
    lines = ["", "", SECTION, "",
             (f"{len(approved):,} of {asked:,} Wikidata images pass the photo pipeline's rules (free licence, an author "
              f"to credit, a photo type, at least {MIN_SIDE} px, not a map or drawing), read from the Commons API "
              "without downloading: " + ", ".join(f"{n:,} {p} priority" for p, n in prio.items()) + ". The rest:"),
             ""]
    lines += [f"- {k}: {n:,}" for k, n in reasons.items()]
    lines += ["", ("The queue (`data/knowledge/media/approved_image_queue.json`) is for the photo pipeline to fetch "
                   "once the team agrees; a person then checks each photo by eye before the app shows it.")]
    REPORT.write_text(text + "\n".join(lines) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
