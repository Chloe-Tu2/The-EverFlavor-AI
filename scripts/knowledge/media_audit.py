"""The dish media audit: for each of our dishes, the best image it can show, its licence and credit, the fallback
it would use, and what to fetch next. Reports only: no image is downloaded and the app is not changed.

Image levels, best first (points out of 100):
- recipe (100): a photo of one of the dish's own linked recipes, kept by the photo check;
- dish (90): a free photo of the dish from Wikimedia Commons (`dish_photos.parquet`, licence and credit recorded);
- variant (80): a Commons photo of a version of it, or of the dish it is a version of;
- family (60): a Commons photo of its dish family (notebook 15), shown as "a dumpling in general";
- placeholder (0): the app's own pixel-art kitchen, so no page is ever empty.
A cuisine or country photo is not used: it would show something that is not the dish.

Statuses: verified (recipe or dish photo, licence and credit complete), fallback (variant or family), candidate
(only the placeholder now, but Wikidata names a Commons image to fetch), missing (placeholder, nothing known),
review (a photo whose licence or credit fails the rules).

    python scripts/knowledge/media_audit.py   # data/knowledge/media/*.json, docs/audits/dish_image_report.md
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from everflavor.waiter import Knowledge

KNOW = ROOT / "data" / "knowledge"
DATA = ROOT / "data" / "processed"
OUT = KNOW / "media"
TODAY = date.today().isoformat()
POINTS = {"recipe": 100, "dish": 90, "variant": 80, "family": 60, "placeholder": 0}
# Free licences only (CC0, public domain, CC BY, CC BY-SA, any version and port)
LICENCE_OK = re.compile(r"^(CC0|Public domain|CC BY( |-SA )?\d\.\d( [a-z]{2})?|CC BY-SA \d\.\d( [a-z]{2})?)$", re.IGNORECASE)
COMMONS = re.compile(r"^https://(commons\.wikimedia\.org/wiki/File:|upload\.wikimedia\.org/|thumb\.wikimedia\.org/)")


def photo_record(row: dict) -> dict:
    """One Commons photo as the audit records it, with the rule checks it passes or fails."""
    problems = []
    if not LICENCE_OK.match(str(row.get("license") or "")):
        problems.append(f"licence not on the free list: {row.get('license')!r}")
    if not str(row.get("credit") or "").strip() or not str(row.get("author") or "").strip():
        problems.append("no credit line or author")
    if not COMMONS.match(str(row.get("file_page") or "")) or not COMMONS.match(str(row.get("thumb_url") or "")):
        problems.append("not a Wikimedia Commons file")
    return {"source_type": "wikimedia", "file_page": row.get("file_page"), "url": row.get("thumb_url"),
            "license": row.get("license"), "attribution": row.get("credit"), "of": row.get("dish_label"),
            "valid": not problems, "problems": problems}


def recipe_photos(know: Knowledge) -> dict[str, Counter]:
    """For each dish, how many of its linked recipes have their own photo that the photo check kept, by source.
    Only Food.com's photos have a recorded licence (CC0, the irkaal Kaggle set in docs/sources.md); the others'
    licence is not recorded yet, so they count as "licence to confirm", never as verified."""
    spec = importlib.util.spec_from_file_location("links", ROOT / "scripts" / "knowledge" / "recipe_dish_links.py")
    if spec is None or spec.loader is None:
        raise SystemExit("scripts/knowledge/recipe_dish_links.py is missing")
    links = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(links)
    longest = max(len(k.split()) for k in know.by_name)
    df = pd.concat([pd.read_parquet(DATA / f"recipes_{s}.parquet", columns=["recipe_id", "source", "dish_name",
                                                                             "origin_country", "image_url", "photo_ok"])
                    for s in ("train", "val", "test")], ignore_index=True)
    fc = pd.read_parquet(DATA / "foodcom_photos.parquet", columns=["recipe_id", "image_url", "photo_ok"])
    df = df.merge(fc.rename(columns={"image_url": "fc_url", "photo_ok": "fc_ok"}), on="recipe_id", how="left")
    fill = df.image_url.isna() & df.fc_url.notna()
    df.loc[fill, "image_url"], df.loc[fill, "photo_ok"] = df.loc[fill, "fc_url"], df.loc[fill, "fc_ok"]
    df = df[df.image_url.notna() & (df.photo_ok.astype("boolean").fillna(False))]   # only photos the check kept
    out: dict[str, Counter] = {}
    for n, c, s in zip(df.dish_name, df.origin_country, df.source):
        e, _ = links.fast_find(know, longest, str(n), c if isinstance(c, str) and c != "Unknown" else None)
        if e and e.get("qid"):
            out.setdefault(str(e["qid"]), Counter())["licensed" if s == "foodcom" else "to_confirm"] += 1
    return out


def main() -> None:
    know = Knowledge.load(KNOW / "dishes.jsonl")
    dishes = [d for d in know.dishes if d.get("kind") == "dish"]
    fam = json.loads((KNOW / "dish_families.json").read_text(encoding="utf-8"))
    families = {f["qid"]: f for f in fam["families"]}
    walter = json.loads((KNOW / "walter_context.json").read_text(encoding="utf-8"))["dishes"]
    names_to_q = {f["name"]: q for q, f in families.items()} | {d["name"]: d["qid"] for d in dishes}
    wd_images = json.loads((OUT / "wikidata_images.json").read_text(encoding="utf-8"))["images"]
    photos = pd.read_parquet(DATA / "dish_photos.parquet")
    review = pd.read_csv(ROOT / "data" / "reference" / "dish_photo_review.csv")
    turned_down = set(review.loc[review.keep.astype(str).str.lower().isin({"false", "no", "0"}), "dish_qid"])
    best_photo = {}
    for row in photos.drop_duplicates("dish_qid").to_dict("records"):
        if row["dish_qid"] not in turned_down:
            best_photo[row["dish_qid"]] = photo_record(row)
    own_recipe_photos = recipe_photos(know)
    zone_of = {r["country"]: r["zone"] for r in json.loads(
        (KNOW / "coverage" / "country_coverage.json").read_text(encoding="utf-8"))["countries"]}

    records = []
    for d in dishes:
        q, w = d["qid"], walter.get(d["qid"], {})
        fam_q = [names_to_q[n] for n in w.get("kind_of", []) if n in names_to_q]
        version_q = [names_to_q[n] for n in w.get("variants", []) if n in names_to_q]
        mine = own_recipe_photos.get(q, Counter())
        chain = {"recipe": mine["licensed"] or None, "dish": best_photo.get(q),
                 "variant": next((best_photo[v] for v in [*version_q, *fam_q[:1]] if v in best_photo and v != q
                                  and families.get(v, {}).get("kind") != "family"), None),
                 "family": next((best_photo[f] for f in fam_q if f in best_photo
                                 and families.get(f, {}).get("kind") == "family"), None),
                 "placeholder": "the app's pixel-art kitchen"}
        level = next(k for k in POINTS if chain[k])
        photo = None if level == "recipe" else chain.get(level)   # a Food.com photo: CC0, credited to Food.com
        bad = isinstance(photo, dict) and not photo["valid"]
        status = ("review" if bad else "verified" if level in {"recipe", "dish"} else "fallback" if level != "placeholder"
                  else "candidate" if q in wd_images else "missing")
        records.append({
            "dish_id": q, "dish_name": d["name"], "country": d.get("country") or "", "region": d.get("region") or "",
            "zone": zone_of.get(d.get("country") or "", ""), "family": ", ".join(w.get("kind_of", [])[:2]),
            "best_level": level, "coverage_score": POINTS[level], "image_status": status,
            "recipe_photos": mine["licensed"], "recipe_photos_licence_to_confirm": mine["to_confirm"],
            "primary_image": chain["dish"],
            "fallbacks": {k: chain[k] for k in ("variant", "family") if chain[k]},
            "wikidata_image": wd_images.get(q), "fallback_available": bool(chain["variant"] or chain["family"]),
            "license_valid": (level == "recipe") if not isinstance(photo, dict) else photo["valid"],
            "attribution_complete": None if not isinstance(photo, dict) else not any("credit" in p for p in photo["problems"]),
            "review_status": "ready" if status == "verified" else "license_review" if status == "review"
            else "fetch_candidate" if q in wd_images and level not in {"recipe", "dish"} else "needs_image"})
    OUT.mkdir(parents=True, exist_ok=True)

    def save(name: str, data: object) -> None:
        (OUT / name).write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    about = {"built_on": TODAY, "by": "scripts/knowledge/media_audit.py", "points": POINTS}
    save("dish_media_audit.json", {"about": about, "dishes": records})

    def coverage(key: str) -> dict:
        groups = defaultdict(list)
        for r in records:
            groups[r[key] or "unknown"].append(r)
        return {g: {"dishes": len(rs), "verified": sum(r["image_status"] == "verified" for r in rs),
                    "with_any_photo": sum(r["best_level"] != "placeholder" for r in rs),
                    "fetchable": sum(r["review_status"] == "fetch_candidate" for r in rs),
                    "average_score": round(sum(r["coverage_score"] for r in rs) / len(rs), 1)}
                for g, rs in sorted(groups.items(), key=lambda kv: -len(kv[1]))}
    by_country, by_zone = coverage("country"), coverage("zone")
    save("country_media_coverage.json", {"about": about, "countries": by_country})
    save("region_media_coverage.json", {"about": about, "zones": by_zone})
    missing = [r for r in records if r["best_level"] in {"placeholder", "family", "variant"}]
    save("missing_images.json", {"about": about, "dishes": [
        {k: r[k] for k in ("dish_id", "dish_name", "country", "best_level", "wikidata_image")} for r in missing]})
    # priority: no photo of its own while the rest of the dish is complete (completeness without the image), fetchable first
    quality = {}
    qfile = KNOW / "quality" / "dish_quality.json"
    if qfile.exists():
        quality = {r["qid"]: r.get("without_image", 0) for r in json.loads(qfile.read_text(encoding="utf-8"))["dishes"]}
    queue = sorted(({"dish_id": r["dish_id"], "dish": r["dish_name"], "country": r["country"],
                     "priority": "high" if quality.get(r["dish_id"], 0) >= 50 and r["wikidata_image"] else
                     "medium" if r["wikidata_image"] else "low",
                     "reason": ("no photo of its own; Wikidata names " + r["wikidata_image"]) if r["wikidata_image"]
                     else "no photo of its own, and none on Wikidata",
                     "quality_score": quality.get(r["dish_id"])} for r in missing),
                   key=lambda x: (["high", "medium", "low"].index(x["priority"]), -(x["quality_score"] or 0), x["dish"]))
    save("image_priority_queue.json", {"about": about, "queue": queue})

    n = len(records)
    lv = Counter(r["best_level"] for r in records)
    st = Counter(r["image_status"] for r in records)
    pr = Counter(x["priority"] for x in queue)
    lines = [f"# Dish image audit ({TODAY})", "",
             ("The best image each of our 3,201 dishes can show, its licence and credit, and what to fetch next. "
             "Reports only: no image was downloaded. Built by `scripts/knowledge/media_audit.py`; per dish in "
             "`data/knowledge/media/dish_media_audit.json`."), "",
             ("Levels, best first: a photo of one of its own recipes (100 points), a Commons photo of the dish (90), "
             "of a version of it (80), of its family (60, shown as \"a dumpling in general\"), else the app's "
             "pixel-art kitchen (0). A cuisine or country photo is not used, since it would not show the dish."), "",
             "## Where the dishes stand", ""]
    lines.append("| Best level | Dishes | Share |")
    lines.append("|---|---:|---:|")
    lines += [f"| {k} | {lv[k]:,} | {lv[k] / n:.0%} |" for k in POINTS]
    lines += ["", (f"Statuses: {', '.join(f'{k} {v:,}' for k, v in st.most_common())}. Every dish resolves to an image "
              "or the placeholder, so no page is empty."), "", "## By zone", "",
              "| Zone | Dishes | Own photo | Any photo | Fetchable from Wikidata | Average score |",
              "|---|---:|---:|---:|---:|---:|"]
    lines += [f"| {z} | {v['dishes']:,} | {v['verified'] / v['dishes']:.0%} | {v['with_any_photo'] / v['dishes']:.0%} | "
              f"{v['fetchable']:,} | {v['average_score']} |" for z, v in by_zone.items()]
    lines += ["", "## By country (20 with the most dishes)", "",
              "| Country | Dishes | Own photo | Any photo | Fetchable | Average score |", "|---|---:|---:|---:|---:|---:|"]
    lines += [f"| {c} | {v['dishes']:,} | {v['verified'] / v['dishes']:.0%} | {v['with_any_photo'] / v['dishes']:.0%} | "
              f"{v['fetchable']:,} | {v['average_score']} |" for c, v in list(by_country.items())[:20]]
    lines += ["", "## Rules checked", "",
              ("- Every dish, version and family photo is a Wikimedia Commons file with a licence on the free list "
               "(CC0, public domain, CC BY, CC BY-SA) and a credit line; one that fails goes to `review`, never to the "
               "page."),
              ("- A recipe photo counts only from Food.com, whose photos are CC0 (`docs/sources.md`). "
               f"{sum(1 for r in records if r['recipe_photos_licence_to_confirm'] and not r['recipe_photos']):,} "
               "dishes have recipe photos only from the Hugging Face set, whose photo licence is not recorded yet: "
               "they are not counted until a person confirms it on the dataset page."),
              "- Photos a person turned down (`data/reference/dish_photo_review.csv`) are not used.",
              "- No image is generated, and no photo from a site without a free licence is used.", "",
              "## Remediation plan", "",
              (f"1. **Fetch** the Wikidata images of {sum(r['review_status'] == 'fetch_candidate' for r in records):,} "
              "dishes through the existing photo pipeline (`scripts/dish_photos/fetch_dish_photos.py meta`, "
              "`download`, `curate`, `write`), which checks each licence and keeps a credit line: "
              f"{pr['high']:,} high priority (50+ of the 80 points besides the image), {pr['medium']:,} medium "
              "(`image_priority_queue.json`)."),
              (f"2. **No image anywhere** for {pr['low']:,} dishes: Commons search by name is the next source; a "
              "person checks each match, as the photo review sheet does today."),
              "3. **Family photos** stand in meanwhile, labelled as the family, never as the dish."]
    with (ROOT / "docs" / "audits" / "dish_image_report.md").open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines).rstrip() + "\n")
    print(f"levels {dict(lv)}; statuses {dict(st)}; queue {dict(pr)}")


if __name__ == "__main__":
    main()
