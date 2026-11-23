"""The coverage audit: which countries, culinary regions, dish families and variants EverFlavor has, which it lacks,
and the expansion backlog, from evidence only.

Evidence used (nothing else, nothing invented):
- `data/knowledge/dishes.jsonl`: the dishes we know (Wikipedia cuisine lists, Wikidata facts), by country and region;
- `data/knowledge/dish_families.json`: notebook 15's families (Wikidata "subclass of", "country of origin");
- `data/knowledge/dish_recipe_counts.json`: recipes per dish (the recipe -> dish linking audit);
- `data/knowledge/countries.json`: the world's countries and continents (Wikidata);
- `data/reference/food_taxonomy.csv`: the app's place tree; and the recipe tables' origin_country / origin_region.

A missing dish is a family member Wikidata lists that we do not have. That is a lower bound of what is missing,
not a full list of a cuisine: a country whose dishes Wikidata does not group into families looks better covered
than it is. The reports say so.

    python scripts/knowledge/coverage_audit.py   # data/knowledge/coverage/*.json and docs/audits/coverage_*.md
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from everflavor.taxonomy import load_taxonomy

KNOW = ROOT / "data" / "knowledge"
OUT = KNOW / "coverage"
DOCS = ROOT / "docs" / "audits"
TODAY = date.today().isoformat()

# Wikidata and our tables name some countries differently; only these exact names are merged
SAME_COUNTRY = {"People's Republic of China": "China", "State of Palestine": "Palestine", "Palestinian territories":
                "Palestine", "Kingdom of the Netherlands": "Netherlands", "United States of America": "United States",
                "Republic of Ireland": "Ireland", "Czechia": "Czech Republic", "Republic of Korea": "South Korea",
                "Russian Federation": "Russia", "Türkiye": "Turkey", "Republic of the Congo": "Congo",
                "Kingdom of Denmark": "Denmark", "Taiwan (Republic of China)": "Taiwan"}
# Parts of a country Wikidata gives as the country of origin: the country, and the part as its region
PART_OF_COUNTRY = {"England": ("United Kingdom", "England"), "Scotland": ("United Kingdom", "Scotland"),
                   "Wales": ("United Kingdom", "Wales"), "Northern Ireland": ("United Kingdom", "Northern Ireland"),
                   "Hong Kong": ("China", "Hong Kong"), "Macau": ("China", "Macau"), "Tibet": ("China", "Tibet")}
# Coverage levels (a fixed rule, written down so it can be argued with): share = dishes we have / (we have +
# family members Wikidata lists that we lack)
LEVELS = (("high", 50, 0.6), ("medium", 15, 0.4))
FAMILY_AUDIT = ["dumpling", "flatbread", "curry", "rice dish", "soup", "stew", "noodle", "noodle dish", "pasta",
                "bread", "pastry", "cake", "sausage", "salad", "sandwich"]
VARIANT_AUDIT = ["biryani", "pierogi", "ramen", "curry", "dumpling", "pizza", "taco", "kebab", "pilaf", "noodle"]
INDIGENOUS = {"Native American": r"native american|american indian|cherokee|navajo|ojibwe|lakota|iroquois|pueblo people",
              "First Nations": r"first nations", "Inuit": r"\binuit\b|\binuk\b", "Sámi": r"\bs[aá]mi\b",
              "Aboriginal Australian": r"aboriginal|bush ?tucker|indigenous australian",
              "Māori and Pacific": r"m[aā]ori|polynesian|hawaiian native|native hawaiian",
              "Indigenous South American": r"quechua|aymara|mapuche|guaran[ií]|inca\b|incan|amazonian",
              "Mesoamerican": r"aztec|maya\b|mayan|nahuatl|zapotec|mixtec|pre-columbian|pre-hispanic",
              "Indigenous African": r"\bmaasai|\bsan people|khoisan|berber|amazigh|tuareg",
              "Any 'indigenous'": r"indigenous"}
EUROPE_ASKED = ["France", "Italy", "Spain", "Portugal", "Greece", "Germany", "Poland", "Ukraine", "Hungary",
                "Romania", "Sweden", "Norway", "Finland", "Denmark", "Iceland", "Serbia", "Croatia", "Bosnia and Herzegovina",
                "Bulgaria", "Albania", "North Macedonia", "Slovenia", "Montenegro", "Belgium", "Netherlands",
                "Luxembourg", "Austria", "Switzerland", "Czech Republic", "Slovakia"]
REGIONS_ASKED = {"China": ["Sichuan", "Guangdong", "Hunan", "Jiangsu", "Shandong", "Fujian", "Anhui", "Zhejiang"],
                 "India": ["Punjab", "Bengal", "Gujarat", "Tamil Nadu", "Hyderabad", "Kashmir", "Kerala"],
                 "United States": ["Louisiana", "Texas", "Southern US", "Northeastern US", "Hawaii", "Southwestern US",
                                   "California"]}


def clean_country(name: object) -> tuple[str, str]:
    """(country, region) for a Wikidata country-of-origin name; ("", "") when unknown."""
    name = str(name or "").strip()
    if name in PART_OF_COUNTRY:
        return PART_OF_COUNTRY[name]
    return SAME_COUNTRY.get(name, name), ""


def what_it_is(what: dict) -> tuple[bool, bool, bool]:
    """(a commercial product, not a food, a plant or animal) from Wikidata's "instance of", maker, brand, owner."""
    types = " ".join(what.get("instance_of", [])).lower()
    commercial = bool(what.get("manufacturer") or what.get("brand") or what.get("owner")
                      or any(w in types for w in ("brand", "trademark", "business", "company"))
                      or "product" in what.get("instance_of", []))
    not_food = any(w in types for w in ("fictional", "incident", "scandal", "scare", "event", "outbreak"))
    living = any(w in types for w in ("taxon", "cultivar", "organisms known"))
    return commercial, not_food, living


def level(dishes: int, share: float | None, recipes: int) -> str:
    if dishes == 0:
        return "recipes only" if recipes else "absent"
    for name, need, need_share in LEVELS:
        if dishes >= need and (share is None or share >= need_share):
            return name
    return "low"


def load() -> dict:
    tax = load_taxonomy()
    dishes = [json.loads(line) for line in (KNOW / "dishes.jsonl").open(encoding="utf-8")]
    fam = json.loads((KNOW / "dish_families.json").read_text(encoding="utf-8"))
    counts = json.loads((KNOW / "dish_recipe_counts.json").read_text(encoding="utf-8"))
    world = json.loads((KNOW / "countries.json").read_text(encoding="utf-8"))
    types_file = OUT / "wikidata_types.json"   # from fetch_backlog_types.py
    kinds = json.loads(types_file.read_text(encoding="utf-8"))["items"] if types_file.exists() else {}
    recipes = pd.concat([pd.read_parquet(ROOT / "data" / "processed" / f"recipes_{s}.parquet",
                                         columns=["origin_country", "origin_region"]) for s in ("train", "val", "test")])
    return {"tax": tax, "dishes": dishes, "fam": fam, "counts": counts, "world": world, "recipes": recipes,
            "kinds": kinds}


def build(src: dict) -> dict:
    tax, fam, kinds = src["tax"], src["fam"], src["kinds"]
    ours = {d["qid"]: d for d in src["dishes"] if d.get("kind") == "dish"}
    known = {d["qid"] for d in src["dishes"]}   # dishes and foods: never a backlog candidate
    linked = src["counts"]["dishes"]
    recipe_country = src["recipes"].origin_country.value_counts().to_dict()
    recipe_region = src["recipes"].dropna(subset=["origin_region"]).groupby(["origin_country", "origin_region"]).size()
    tax_country = {n.name: n for n in tax.nodes.values() if n.level == "country"}
    continent = {}
    for c in src["world"]["countries"]:
        name = SAME_COUNTRY.get(c["name"], c["name"])
        continent.setdefault(name, {"continents": c["continents"], "iso": c["iso"], "qid": c["qid"],
                                    "population": c["population"], "part_of": c["part_of"]})

    families = [f for f in fam["families"] if f.get("kind") == "family"]
    fam_of_member: dict[str, list[dict]] = defaultdict(list)
    for f in families:
        for m in f["members"]:
            fam_of_member[m["qid"]].append(f)

    # missing dishes: family members we do not have, once each, with every family they are in
    missing: dict[str, dict] = {}
    for f in families:
        for m in f["members"]:
            if m["in_everflavor"] or m["qid"] in known:
                continue
            c, region = clean_country(m.get("country"))
            entry = missing.setdefault(m["qid"], {"qid": m["qid"], "name": m["name"], "country": c, "region": region,
                                                  "wikidata_country": m.get("country") or "", "wikipedia": m.get("wikipedia"),
                                                  "families": []})
            entry["families"].append({"qid": f["qid"], "name": f["name"], "family_in_everflavor": f["qid"] in ours})

    per = defaultdict(lambda: {"dishes": 0, "dishes_with_recipes": 0, "families": set(), "variants": 0,
                               "missing": 0, "regions": Counter(), "examples": [], "missing_examples": []})
    for q, d in ours.items():
        p = per[d.get("country") or ""]
        p["dishes"] += 1
        p["dishes_with_recipes"] += q in linked
        for f in fam_of_member.get(q, []):
            p["families"].add(f["name"])
            p["variants"] += 1
        if d.get("region"):
            p["regions"][d["region"]] += 1
        p["examples"].append((linked.get(q, {}).get("recipes", 0), d["name"]))
    for m in missing.values():
        commercial, not_food, _ = what_it_is(kinds.get(m["qid"], {}))
        if commercial or not_food:
            continue   # a brand or an event is not a missing dish
        p = per[m["country"]]
        p["missing"] += 1
        p["missing_examples"].append((bool(m["wikipedia"]), len(m["families"]), m["name"]))

    names = (set(per) | set(tax_country) | {c for c in recipe_country if isinstance(c, str)} | set(continent)) - {"",
                                                                                                                "Unknown"}
    rows = []
    for name in sorted(names):
        p = per[name]
        node = tax_country.get(name)
        path = [n.name for n in tax.path(node.slug)][1:-1] if node else []
        share = p["dishes"] / (p["dishes"] + p["missing"]) if p["dishes"] + p["missing"] else None
        rec = int(recipe_country.get(name, 0))
        info = continent.get(name, {})
        rows.append({
            "country": name, "iso": info.get("iso", ""), "wikidata": info.get("qid", ""),
            "continents": info.get("continents", []), "population": info.get("population"),
            "part_of": info.get("part_of", []),
            "in_taxonomy": bool(node), "taxonomy_path": path, "zone": path[0] if path else "",
            "taxonomy_region": path[1] if len(path) > 1 else "",
            "recipes": rec, "dishes": p["dishes"], "dishes_with_recipes": p["dishes_with_recipes"],
            "families": len(p["families"]), "family_names": sorted(p["families"])[:25], "variants": p["variants"],
            "missing_family_members": p["missing"], "share_known": round(share, 3) if share is not None else None,
            "coverage": level(p["dishes"], share, rec),
            "culinary_regions": dict(p["regions"].most_common()),
            "representative_dishes": [n for _, n in sorted(p["examples"], reverse=True)[:8]],
            "missing_examples": [n for *_, n in sorted(p["missing_examples"], reverse=True)[:10]],
            "not_a_country_today": name not in continent,
        })
    by_country = {r["country"]: r for r in rows}

    # the backlog: every missing dish with what the publishing rules need, and its approval state
    backlog = []
    for m in sorted(missing.values(), key=lambda m: (m["country"], m["name"])):
        c = by_country.get(m["country"])
        problems = []
        if not m["country"]:
            problems.append("no country of origin on Wikidata")
        elif m["country"] not in continent:
            problems.append(f"'{m['country']}' is not one of today's countries (a region, city or former state): "
                            "a person places it")
        elif not (c and c["in_taxonomy"]):
            problems.append(f"{m['country']} is not in the place tree yet")
        if len({f['qid'] for f in m["families"]}) > 3:
            problems.append("in more than 3 families: check which one it belongs to")
        if not m["wikipedia"]:
            problems.append("no English Wikipedia article")
        what = kinds.get(m["qid"], {})
        commercial, not_food, living = what_it_is(what)
        if commercial:
            problems.append("a commercial product (Wikidata gives a brand, maker or owner)")
        if not_food:
            problems.append("not a food (Wikidata: " + ", ".join(what["instance_of"]) + ")")
        if living:
            problems.append("a plant or animal on Wikidata, not a dish")
        status = ("blocked" if not m["country"] or commercial or not_food
                  else "needs_review" if problems else "ready")
        backlog.append({
            "dish": m["name"], "wikidata": m["qid"], "country": m["country"], "region": m["region"],
            "zone": c["zone"] if c else "", "taxonomy_region": c["taxonomy_region"] if c else "",
            "continents": c["continents"] if c else [], "families": m["families"],
            "status": status, "taxonomy_ready": bool(c and c["in_taxonomy"]), "requires_review": status != "ready",
            "problems": problems, "knowledge_only": True, "not_a_dish": bool(commercial or not_food),
            "sources": [{"name": "Wikidata", "url": f"https://www.wikidata.org/wiki/{m['qid']}", "licence": "CC0 1.0",
                         "retrieved": fam["source"].get("retrieved", "")}]
                       + ([{"name": "Wikipedia", "url": m["wikipedia"], "licence": "CC BY-SA 4.0",
                            "credit": "Wikipedia contributors"}] if m["wikipedia"] else []),
        })

    # dish families: how much of each we have (commercial products and non-foods do not count as members)
    not_dish = {b["wikidata"] for b in backlog if b["not_a_dish"]}
    fam_rows = []
    for f in families:
        members = [m for m in f["members"] if m["qid"] not in not_dish]
        have = [m for m in members if m["in_everflavor"] or m["qid"] in ours]
        lack = [m for m in members if not (m["in_everflavor"] or m["qid"] in ours)]
        zones = Counter(by_country[clean_country(m.get("country"))[0]]["zone"] or "not in the tree"
                        for m in lack if clean_country(m.get("country"))[0] in by_country)
        fam_rows.append({"family": f["name"], "qid": f["qid"], "family_dish_in_everflavor": f["qid"] in ours,
                         "members": len(members), "have": len(have), "missing": len(lack),
                         "products_left_out": len(f["members"]) - len(members),
                         "share": round(len(have) / len(members), 3) if members else None,
                         "missing_by_zone": dict(zones.most_common()),
                         "missing_examples": [m["name"] for m in lack if m.get("wikipedia")][:12]})
    fam_rows.sort(key=lambda r: -r["missing"])

    # culinary regions below a country: the tree's own, the knowledge notebook's, and the ones asked about
    region_rows = []
    tree_regions = {(tax.ancestor(n.slug, "country").name if tax.ancestor(n.slug, "country") else "", n.name): n
                    for n in tax.nodes.values() if n.level in {"state", "division", "culinary_region"}}
    know_regions = Counter((d.get("country"), d.get("region")) for d in ours.values() if d.get("region"))
    for key in sorted(set(tree_regions) | set(know_regions), key=lambda k: (str(k[0]), str(k[1]))):
        c, r = key
        region_rows.append({"country": c, "region": r, "in_taxonomy": key in tree_regions,
                            "level": tree_regions[key].level if key in tree_regions else "",
                            "dishes": know_regions.get(key, 0), "recipes": int(recipe_region.get(key, 0))})
    asked = []
    for c, regs in REGIONS_ASKED.items():
        for r in regs:
            hit = next((x for x in region_rows if x["country"] == c and x["region"] == r), None)
            asked.append({"country": c, "region": r, "in_taxonomy": bool(hit and hit["in_taxonomy"]),
                          "dishes": hit["dishes"] if hit else 0, "recipes": hit["recipes"] if hit else 0})

    # indigenous foodways: dishes whose own Wikipedia text or list headings name them
    indigenous = {}
    for label, pattern in INDIGENOUS.items():
        rx = re.compile(pattern, re.IGNORECASE)
        found = [d for d in ours.values()
                 if rx.search(" ".join([d.get("summary") or "", *d.get("sections", []), *d.get("regions", [])]))]
        indigenous[label] = {"dishes": len(found), "countries": dict(Counter(d.get("country") for d in found).most_common()),
                             "examples": sorted(d["name"] for d in found)[:15]}

    # the families asked about, and the variant families
    fam_by_name = defaultdict(list)
    for r in fam_rows:
        fam_by_name[r["family"].lower()].append(r)
    family_audit = {n: sorted(fam_by_name.get(n, []), key=lambda r: -r["members"])[:1] for n in FAMILY_AUDIT}
    variant_rows = [r for r in fam_rows if r["family_dish_in_everflavor"] and r["missing"]]
    variant_rows.sort(key=lambda r: (-r["missing"], r["family"]))
    variant_asked = {n: fam_by_name.get(n, [])[:1] for n in VARIANT_AUDIT}

    # priority: evidence only (ready dishes waiting, recipes without dish knowledge, the tree ready)
    ready = Counter(b["country"] for b in backlog if b["status"] == "ready")
    review = Counter(b["country"] for b in backlog if b["status"] == "needs_review")
    prio = []
    for r in rows:
        if r["not_a_country_today"]:
            continue
        gap_recipes = r["recipes"] >= 200 and r["dishes"] < 15
        tier = (1 if (ready[r["country"]] >= 20 or gap_recipes) and r["in_taxonomy"]
                else 2 if ready[r["country"]] + review[r["country"]] >= 5 or (r["recipes"] >= 50 and r["dishes"] < 5)
                else 3 if ready[r["country"]] + review[r["country"]] or r["coverage"] in {"absent", "recipes only", "low"}
                else None)
        if tier:
            prio.append({"country": r["country"], "tier": tier, "zone": r["zone"] or "not in the tree",
                         "continents": r["continents"], "coverage": r["coverage"], "dishes": r["dishes"],
                         "recipes": r["recipes"], "ready_dishes": ready[r["country"]],
                         "dishes_to_review": review[r["country"]], "in_taxonomy": r["in_taxonomy"],
                         "why": "; ".join(x for x in [
                             f"{ready[r['country']]} dishes ready to add" if ready[r["country"]] else "",
                             f"{review[r['country']]} to review" if review[r["country"]] else "",
                             f"{r['recipes']} recipes but {r['dishes']} dishes" if gap_recipes else "",
                             "not in the place tree" if not r["in_taxonomy"] else ""] if x)})
    prio.sort(key=lambda p: (p["tier"], -p["ready_dishes"], -p["dishes_to_review"], -p["recipes"], p["country"]))

    missing_countries = [r for r in rows if r["dishes"] == 0 and r["recipes"] == 0 and r["iso"]
                         and not r["not_a_country_today"]]
    return {"rows": rows, "backlog": backlog, "families": fam_rows, "regions": region_rows, "regions_asked": asked,
            "indigenous": indigenous, "family_audit": family_audit, "variants": variant_rows,
            "variants_asked": variant_asked, "priority": prio, "missing_countries": missing_countries}


def write_json(name: str, data: object) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def main() -> None:
    res = build(load())
    about = {"built_on": TODAY, "by": "scripts/knowledge/coverage_audit.py", "rules": "docs/audits/publishing_rules.md"}
    write_json("country_coverage.json", {"about": about, "countries": res["rows"]})
    write_json("culinary_region_coverage.json", {"about": about, "regions": res["regions"], "asked": res["regions_asked"]})
    write_json("expansion_backlog.json", {"about": about, "status_counts": Counter(b["status"] for b in res["backlog"]),
                                          "dishes": res["backlog"]})
    write_json("expansion_priority_list.json", {"about": about, "countries": res["priority"]})
    write_json("missing_countries.json", {"about": about, "countries": [
        {"country": r["country"], "iso": r["iso"], "continents": r["continents"], "population": r["population"]}
        for r in res["missing_countries"]]})
    write_json("missing_regions.json", {"about": about, "not_in_taxonomy": [r for r in res["regions"] if not r["in_taxonomy"]],
                                        "asked_and_absent": [r for r in res["regions_asked"] if not r["in_taxonomy"]]})
    write_json("family_coverage.json", {"about": about, "families": res["families"], "asked": res["family_audit"],
                                        "variant_families": res["variants"][:200], "variants_asked": res["variants_asked"],
                                        "indigenous": res["indigenous"]})
    from coverage_reports import (
        write_reports,  # the markdown, kept apart from the counting
    )
    write_reports(res, DOCS, TODAY)
    s = Counter(b["status"] for b in res["backlog"])
    print(f"{len(res['rows'])} countries; backlog {len(res['backlog'])} ({dict(s)}); "
          f"priority {Counter(p['tier'] for p in res['priority'])}")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    main()
