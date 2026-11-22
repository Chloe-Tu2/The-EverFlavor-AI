"""The quality sprint's reports: how deep and complete each dish is, what the waiter knows, how far the map, the
place tree, the countries and the culinary regions reach, and the publication queue checked again. Every number
comes from our own files; each report ends with a remediation plan that names the source or script that can fill
a gap (never "write it").

    python scripts/knowledge/quality_reports.py

Needs the audits first (recipe_dish_links.py, coverage_audit.py, graph_assets.py). Writes docs/audits/*_report.md
and data/knowledge/quality/*.json.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from everflavor.domain.food_graph import is_wikipedia
from everflavor.taxonomy import load_taxonomy
from everflavor.waiter import _norm

KNOW = ROOT / "data" / "knowledge"
OUT = KNOW / "quality"
DOCS = ROOT / "docs" / "audits"
TODAY = date.today().isoformat()
# The parts of a rich dish, each from a source we already use, and what fills it when it is missing
PARTS = {
    "summary": ("a summary from its Wikipedia article", "scripts/knowledge/fetch_knowledge.py"),
    "wikipedia": ("its own Wikipedia article to read more", "fetch_knowledge.py (learn_more 'quick')"),
    "origin": ("a country of origin on Wikidata (P495)", "Wikidata itself: nothing to fill on our side"),
    "ingredients": ("its ingredients on Wikidata (P186, made from)", "Wikidata itself"),
    "family": ("a dish family (notebook 15)", "notebook 15, when Wikidata files it under one"),
    "related": ("a related dish or version in EverFlavor", "the Food Graph (comes with family and versions)"),
    "recipe": ("at least one recipe", "a licensed recipe source; never written"),
    "photo": ("a real photo of it (its recipe, the dish or a version)", "scripts/dish_photos/ (image_coverage_report.md)"),
    "fun_facts": ("fun-fact sentences from its Wikipedia intro", "fetch_knowledge.py"),
    "story": ("story sentences (history, origin, culture)", "fetch_knowledge.py --stories"),
    "map": ("map places in the pilot area for its country", "stores.COUNTRY_CUISINES and the places table"),
    "pronunciation": ("how to say it", "data/reference/dish_pronunciation.csv (a person adds it)"),
}
# The dish completeness score (0-100), with the team's weights: the image counts by its level in the media audit
# (a recipe photo 100%, the dish 90%, a version 80%, the family 60%, the placeholder 0%)
WEIGHTS = {"image": 20, "family": 10, "country": 10, "region": 10, "history": 15, "facts": 10, "variants": 10,
           "related": 10, "recipe": 5}
TIERS = (("rich", 70), ("fair", 40), ("thin", 0))


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(name: str, data: object) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def save_md(name: str, lines: list[str]) -> None:
    with (DOCS / name).open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def table(head: list[str], rows: list[list[object]]) -> list[str]:
    out = ["| " + " | ".join(head) + " |", "|---|" + "---:|" * (len(head) - 1)]
    return out + ["| " + " | ".join(str(c).replace("|", "/") for c in r) + " |" for r in rows]


def pct(a: int, b: int) -> str:
    return f"{a / b:.0%}" if b else ""


def tier(score: int) -> str:
    return next(name for name, need in TIERS if score >= need)


def main() -> None:
    dishes = [d for d in (json.loads(line) for line in (KNOW / "dishes.jsonl").open(encoding="utf-8")) if d["kind"] == "dish"]
    fam = read(KNOW / "dish_families.json")
    in_family = set(fam["dish_families"])
    counts = read(KNOW / "dish_recipe_counts.json")["dishes"]
    walter = read(KNOW / "walter_context.json")["dishes"]
    map_prep = read(KNOW / "map_prep.json")
    media = {r["dish_id"]: r for r in read(KNOW / "media" / "dish_media_audit.json")["dishes"]}
    spoken = set(pd.read_csv(ROOT / "data" / "reference" / "dish_pronunciation.csv").wikidata_qid.dropna())
    mapped = {c for c, e in map_prep["countries"].items() if e.get("pilot_places_with_tag")}

    # ---------------------------------------------------------------- dish quality
    rows = []
    for d in dishes:
        q, w = d["qid"], walter.get(d["qid"], {})
        have = {
            "summary": bool(d.get("summary")),
            "wikipedia": any(lm["level"] == "quick" and is_wikipedia(lm["url"]) for lm in d.get("learn_more", [])),
            "origin": bool(d.get("origin")), "ingredients": bool(d.get("made_from")), "family": q in in_family,
            "related": bool(w.get("related") or w.get("variants")), "recipe": counts.get(q, {}).get("recipes", 0) > 0,
            "photo": media.get(q, {}).get("best_level") in {"recipe", "dish", "variant"}, "fun_facts": bool(d.get("fun_facts_candidates") or d.get("fun_fact_candidates")),
            "story": bool(d.get("story_candidates")),
            "map": bool(set(w.get("countries") or [d.get("country")]) & mapped), "pronunciation": q in spoken,
        }
        part = {"image": media.get(q, {}).get("coverage_score", 0) / 100, "family": have["family"],
                "country": have["origin"], "region": bool(d.get("region")), "history": have["story"],
                "facts": have["fun_facts"], "variants": bool(w.get("variants") or w.get("variants_not_in_everflavor")),
                "related": have["related"], "recipe": have["recipe"]}
        score = round(sum(WEIGHTS[k] * float(v) for k, v in part.items()))
        rows.append({"qid": q, "name": d["name"], "country": d.get("country") or "", "region": d.get("region") or "",
                     "score": score, "tier": tier(score), "without_image": round(score - WEIGHTS["image"] * part["image"]),
                     "parts": sum(have.values()), "missing": [k for k, v in have.items() if not v],
                     "recipes": counts.get(q, {}).get("recipes", 0)})
    n = len(rows)
    by_tier = Counter(r["tier"] for r in rows)
    gaps = Counter(m for r in rows for m in r["missing"])
    save_json("dish_quality.json", {"built_on": TODAY, "weights": WEIGHTS, "parts": {k: v[0] for k, v in PARTS.items()},
                                    "tiers": {t: need for t, need in TIERS}, "dishes": rows})
    by_country = defaultdict(list)
    for r in rows:
        by_country[r["country"]].append(r)
    crow = sorted(([c, len(rs), round(sum(r["score"] for r in rs) / len(rs), 1),
                    pct(sum(r["tier"] == "rich" for r in rs), len(rs)), pct(sum(r["tier"] == "thin" for r in rs), len(rs))]
                   for c, rs in by_country.items() if c), key=lambda x: (-x[1], x[0]))
    lines = [f"# Dish quality ({TODAY})", "",
             ("How complete each of our 3,201 dishes is, not how many there are. The completeness score (0-100) "
              "weighs: image 20 (by its level in `image_coverage_report.md`), story 15, family 10, country of origin 10, "
              "region 10, fun facts 10, versions 10, related dishes 10, a recipe 5. **rich** = 70 or more, **fair** "
              "= 40 to 69, **thin** = under 40. Per dish: `data/knowledge/quality/dish_quality.json`."), "",
             (f"**{by_tier['rich']:,} rich ({pct(by_tier['rich'], n)}), {by_tier['fair']:,} fair "
              f"({pct(by_tier['fair'], n)}), {by_tier['thin']:,} thin ({pct(by_tier['thin'], n)}).** "
              f"Average {sum(r['score'] for r in rows) / n:.0f} of 100."), "",
             "## The parts, and what is missing", "",
             "Twelve parts, each from a source we already use (the score is built from most of them and the region):", ""]
    lines += table(["Part", "Dishes with it", "Missing", "What fills it"],
                   [[desc, f"{n - gaps[k]:,} ({pct(n - gaps[k], n)})", f"{gaps[k]:,}", fill]
                    for k, (desc, fill) in PARTS.items()])
    lines += ["", "## By country (20 with the most dishes)", ""]
    lines += table(["Country", "Dishes", "Average score", "Rich", "Thin"], crow[:20])
    lines += ["", "## Remediation plan", "",
              "Most points can come from sources and scripts we already have, in this order of value for effort:", ""]
    plan = sorted(((gaps[k], k) for k in PARTS), reverse=True)
    for i, (g, k) in enumerate([p for p in plan if p[0]][:8], 1):
        lines += [f"{i}. **{PARTS[k][0]}** for {g:,} dishes: {PARTS[k][1]}."]
    lines += ["", ("Origin and ingredients live on Wikidata; where Wikidata has none, the dish stays without them "
              "rather than getting a guess. Recipes are never written: a dish without one stays knowledge-only.")]
    save_md("dish_quality_report.md", lines)

    # ---------------------------------------------------------------- the waiter's knowledge
    facts = [len(d.get("fun_fact_candidates") or []) for d in dishes]
    stories = [len(d.get("story_candidates") or []) for d in dishes]
    levels = Counter(lv for d in dishes for lv in {lm["level"] for lm in d.get("learn_more", [])})
    nlines = Counter(len(w.get("lines", [])) for w in walter.values())
    review = pd.read_csv(KNOW / "review" / "focus_review.csv")
    wc = {"dishes": n, "with_3_facts": sum(f >= 3 for f in facts), "with_a_fact": sum(f > 0 for f in facts),
          "with_a_story": sum(s > 0 for s in stories), "learn_more_levels": dict(levels),
          "graph_lines": {str(k): v for k, v in sorted(nlines.items())},
          "reviewed_by_a_person": sum(bool(d.get("reviewed")) for d in dishes),
          "focus_review_rows": len(review), "focus_review_decided": int(review.verdict.notna().sum())}
    save_json("walter_coverage.json", {"built_on": TODAY, **wc})
    lines = [f"# The waiter's knowledge coverage ({TODAY})", "",
             ("What the waiter can tell about each dish, all of it copied from Wikipedia (credited) and Wikidata, "
             "never written by a model."), ""]
    lines += table(["What", "Dishes", "Share"], [
        ["at least one fun fact", f"{wc['with_a_fact']:,}", pct(wc["with_a_fact"], n)],
        ["three fun facts (what he shows first)", f"{wc['with_3_facts']:,}", pct(wc["with_3_facts"], n)],
        ["a story (history, origin, culture)", f"{wc['with_a_story']:,}", pct(wc["with_a_story"], n)],
        ["read more: its own article", f"{levels['quick']:,}", pct(levels["quick"], n)],
        ["read more: its cuisine or region page", f"{levels['more']:,}", pct(levels["more"], n)],
        ["read more: books, UNESCO, Wikidata", f"{levels['deep']:,}", pct(levels["deep"], n)],
        ["graph lines: 3 or more", f"{sum(v for k, v in nlines.items() if k >= 3):,}",
         pct(sum(v for k, v in nlines.items() if k >= 3), n)],
        ["facts checked by a person", f"{wc['reviewed_by_a_person']:,}", pct(wc["reviewed_by_a_person"], n)]])
    lines += ["", "## Remediation plan", "",
              (f"1. **Review.** No dish's facts are checked by a person yet; the review sheet "
              f"(`data/knowledge/review/focus_review.csv`, {wc['focus_review_rows']} rows) has "
              f"{wc['focus_review_decided']} decisions. Its keep / fix / drop verdicts are the first step before "
              "the chat in 0.8.0 shows facts."),
              (f"2. **Stories** for {n - wc['with_a_story']:,} dishes: `fetch_knowledge.py --stories` reads their "
              "articles' History and Origin sections; where an article has none, there is none to show."),
              f"3. **Three facts** are there for {wc['with_3_facts']:,} dishes; the rest show fewer, never filler.",
              "4. **Graph lines:** a dish with only its place gets more lines when notebook 15 finds its family."]
    save_md("walter_coverage_report.md", lines)

    # ---------------------------------------------------------------- map
    mp = map_prep["countries"]
    rec_total = sum(e["recipes"] for e in mp.values())
    dish_total = sum(e["dishes"] for e in mp.values())
    tagged = {c: e for c, e in mp.items() if e["cuisine_tag"]}
    placed = {c: e for c, e in tagged.items() if e.get("pilot_places_with_tag")}
    mv = {"countries": len(mp), "with_tag": len(tagged), "with_pilot_places": len(placed),
          "dishes_mappable": sum(e["dishes"] for e in placed.values()), "dishes": dish_total,
          "linked_recipes_mappable": sum(e["recipes"] for e in placed.values()), "linked_recipes": rec_total,
          "no_tag": sorted(c for c, e in mp.items() if not e["cuisine_tag"]),
          "tag_but_no_place": sorted(c for c in tagged if c not in placed),
          "place_tags_without_a_country": map_prep.get("place_tags_without_a_country", {})}
    save_json("map_validation.json", {"built_on": TODAY, **mv})
    lines = [f"# Map coverage validation ({TODAY})", "",
             ("Can the map show a place for a dish? A dish is mappable when its country's OpenStreetMap cuisine word "
             "(`stores.COUNTRY_CUISINES`) is on at least one place in the Greater Houston pilot area. From "
             "`data/knowledge/map_prep.json`."), ""]
    lines += table(["What", "Count", "Share"], [
        ["countries with dishes", mv["countries"], ""],
        ["... with a cuisine tag", mv["with_tag"], pct(mv["with_tag"], mv["countries"])],
        ["... with pilot places for it", mv["with_pilot_places"], pct(mv["with_pilot_places"], mv["countries"])],
        ["dishes the map can place (a dish counts once per country of origin)", f"{mv['dishes_mappable']:,}", pct(mv["dishes_mappable"], dish_total)],
        ["linked recipes the map can place", f"{mv['linked_recipes_mappable']:,}", pct(mv["linked_recipes_mappable"], rec_total)]])
    lines += ["", "## Gaps", "",
              (f"- **No cuisine tag** ({len(mv['no_tag'])}): {', '.join(mv['no_tag'])}. No demonym on Wikidata, or "
              "OpenStreetMap seldom uses it."),
              (f"- **A tag but no pilot place** ({len(mv['tag_but_no_place'])}): {', '.join(mv['tag_but_no_place'])}. "
              "The pilot area has no such place; another area would."),
              "- **Places whose tag names no country of ours:** "
              + ", ".join(f"{t} {k}" for t, k in list(mv["place_tags_without_a_country"].items())[:12]) + ".", "",
              "## Remediation plan", "",
              "1. A second pilot area changes \"no pilot place\" the most; the map is Houston-only by design today.",
              ("2. For the countries without a tag, OpenStreetMap's own wiki (Key:cuisine) is the source to check; a "
              "tag is added only where it is in use."),
              ("3. Kinds of food (pizza, seafood, barbecue) are not countries and should stay out of this list; they "
              "could serve dish families later (a pizza place for the pizza family), as a separate reviewed step.")]
    save_md("map_validation_report.md", lines)

    # ---------------------------------------------------------------- taxonomy, countries, culinary regions
    tax = load_taxonomy()
    cov = {r["country"]: r for r in read(KNOW / "coverage" / "country_coverage.json")["countries"]}
    regions = read(KNOW / "coverage" / "culinary_region_coverage.json")
    per_node: dict[str, dict] = {}
    for slug, node in tax.nodes.items():
        names = tax.countries_in(slug)
        if node.level in {"world", "zone", "region", "country"}:
            dsh = sum(cov[c]["dishes"] for c in names if c in cov)
            rec = sum(cov[c]["recipes"] for c in names if c in cov)
        else:
            hit = [r for r in regions["regions"] if r["region"] == node.name]
            dsh, rec = sum(r["dishes"] for r in hit), sum(r["recipes"] for r in hit)
        per_node[slug] = {"name": node.name, "level": node.level, "parent": node.parent or "", "dishes": dsh,
                          "recipes": rec, "path": [p.name for p in tax.path(slug)]}
    empty = [v for v in per_node.values() if v["dishes"] == 0]
    tree_countries = {n.name for n in tax.nodes.values() if n.level == "country"}
    outside = Counter(d.get("country") for d in dishes if d.get("country") not in tree_countries)
    save_json("taxonomy_coverage.json", {"built_on": TODAY, "nodes": per_node, "dish_countries_not_in_tree": dict(outside)})
    lvl = Counter(v["level"] for v in per_node.values())
    lvl_empty = Counter(v["level"] for v in empty)
    lines = [f"# Taxonomy completeness ({TODAY})", "",
             ("How much of the place tree (`data/reference/food_taxonomy.csv`, World down to a culinary region) holds "
             "dishes and recipes. Per node: `data/knowledge/quality/taxonomy_coverage.json`."), ""]
    lines += table(["Level", "Nodes", "With dishes", "Without dishes"],
                   [[k, v, v - lvl_empty[k], lvl_empty[k]] for k, v in lvl.items()])
    lines += ["", "## Nodes without a dish", "",
              ", ".join(f"{v['name']} ({v['level']}, {v['recipes']:,} recipes)" for v in
                        sorted(empty, key=lambda v: -v["recipes"])) + ".", "",
              f"Every dish's country is in the tree: {'yes' if not outside else 'no, ' + str(dict(outside))}.", "",
              "## Remediation plan", "",
              ("1. Countries in the tree with recipes but no dish (Puerto Rico, Venezuela, Iceland...) need their "
              "Wikipedia cuisine list in the knowledge notebook, the same way the 54 countries were read."),
              ("2. States without dishes (Texas, California, the Southern US) have recipes (their own origin_region) "
               "but no dish placed there; their Wikipedia cuisine pages would place dishes, as for China and Mexico."),
              ("3. New levels are added only where a published source draws them (the planner's rule): the coverage "
              "audit lists the Balkans, India's states and Siberia as asked for but not drawn yet.")]
    save_md("taxonomy_coverage_report.md", lines)

    crows = []
    for c, r in sorted(cov.items(), key=lambda kv: -kv[1]["dishes"]):
        if not r["iso"] or r["dishes"] == 0 and r["recipes"] == 0 and r["missing_family_members"] == 0:
            continue
        rs = by_country.get(c, [])
        avg = round(sum(x["score"] for x in rs) / len(rs), 1) if rs else ""
        crows.append([c, r["coverage"], r["dishes"], f"{r['recipes']:,}", r["missing_family_members"], avg,
                      pct(sum(x["tier"] == "thin" for x in rs), len(rs)) if rs else ""])
    save_json("country_quality.json", {"built_on": TODAY, "countries": [
        dict(zip(["country", "coverage", "dishes", "recipes", "missing", "average_score", "thin_share"], row)) for row in crows]})
    lines = [f"# Country coverage and depth ({TODAY})", "",
             ("Coverage (how many of a country's known dishes we have, from the coverage audit) next to depth (the "
             "dish quality score). A country with many thin dishes needs enrichment before more dishes."), ""]
    lines += table(["Country", "Coverage", "Dishes", "Recipes", "Missing", "Average score", "Thin"], crows[:60])
    deep_need = sorted((x for x in crows if isinstance(x[5], float) and x[2] >= 20), key=lambda x: x[5])[:10]
    lines += ["", "## Remediation plan", "",
              "Enrich before adding: the countries with 20+ dishes and the lowest average score are "
              + ", ".join(f"{x[0]} ({x[5]})" for x in deep_need) + ". Their dishes gain most from photos "
              "(`scripts/dish_photos/`) and stories (`fetch_knowledge.py --stories`); new dishes come after, from "
              "`coverage/next_500.json`."]
    save_md("country_coverage_report.md", lines)

    rrows = []
    for r in regions["regions"]:
        rs = [x for x in rows if x["country"] == r["country"] and x["region"] == r["region"]]
        avg = round(sum(x["score"] for x in rs) / len(rs), 1) if rs else ""
        rrows.append([r["country"], r["region"], "yes" if r["in_taxonomy"] else "no", r["dishes"], f"{r['recipes']:,}", avg])
    save_json("culinary_region_quality.json", {"built_on": TODAY, "regions": [
        dict(zip(["country", "region", "in_tree", "dishes", "recipes", "average_score"], x)) for x in rrows],
        "asked": regions["asked"]})
    absent = [a for a in regions["asked"] if not a["in_taxonomy"] and a["dishes"] == 0]
    lines = [f"# Culinary region coverage ({TODAY})", "",
             ("Regions below a country, from the place tree and the knowledge notebook (Wikipedia region pages), with "
             "the average dish score."), ""]
    lines += table(["Country", "Region", "In the tree", "Dishes", "Recipes", "Average score"], rrows)
    lines += ["", "## Gaps", "",
              "- Asked about and absent from our data: " + ", ".join(f"{a['region']} ({a['country']})" for a in absent) + ".",
              "- In the knowledge notebook but not in the tree: "
              + ", ".join(f"{r[1]} ({r[0]})" for r in rrows if r[2] == "no") + ".", "",
              "## Remediation plan", "",
              ("1. Regions with dishes but no tree node (Hong Kong, Yunnan, Fujian, Yucatán...) can join the tree: the "
              "Wikipedia region pages that placed the dishes are the published source the planner's rule asks for."),
              "2. India's regions need a source that places dishes by state; none of ours does today.",
              ("3. US states with many recipes and no dishes (Texas, California, the South) need their own cuisine "
              "pages read, as notebook 11 did for China and Mexico.")]
    save_md("culinary_region_coverage_report.md", lines)

    # ---------------------------------------------------------------- the publication queue, checked again
    backlog = read(KNOW / "coverage" / "expansion_backlog.json")["dishes"]
    ours = {_norm(d["name"]): d["name"] for d in dishes}
    queue = []
    for b in backlog:
        problems = list(b["problems"])
        wiki = next((s["url"] for s in b["sources"] if s["name"] == "Wikipedia"), "")
        if wiki and not is_wikipedia(wiki):
            problems.append("the Wikipedia link is not on wikipedia.org")
        same = ours.get(_norm(b["dish"]))
        if same:
            problems.append(f"same name as our dish {same}: maybe the same dish under another Wikidata item")
        status = b["status"]
        if status == "ready" and problems:
            status = "needs_review"
        queue.append({**{k: b[k] for k in ("dish", "wikidata", "country", "zone", "families", "sources")},
                      "status": status, "problems": problems})
    qs = Counter(q["status"] for q in queue)
    save_json("publication_queue.json", {"built_on": TODAY, "rules": "docs/audits/publishing_rules.md",
                                         "status_counts": dict(qs), "dishes": queue})
    moved = sum(1 for q, b in zip(queue, backlog) if q["status"] != b["status"])
    print(f"dish tiers {dict(by_tier)}; queue {dict(qs)} ({moved} moved to review); map {mv['with_pilot_places']}/"
          f"{mv['countries']} countries; empty nodes {len(empty)}")


if __name__ == "__main__":
    main()
