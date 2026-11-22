"""The coverage audit's markdown reports (docs/audits/coverage_*.md and the gap reports), written from the
numbers `coverage_audit.build` counted. Plain tables; every number comes from the JSON files next to them."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

CAVEAT = ("**How to read it.** \"Dishes\" are the dishes in our knowledge notebook listed for the country (from its "
          "Wikipedia cuisine list). \"Missing\" are dishes Wikidata files under a dish family with this country of "
          "origin that we do not have: a lower bound, since many dishes are in no family on Wikidata. \"Share\" is "
          "dishes / (dishes + missing). Coverage: **high** = 50+ dishes and share 60%+, **medium** = 15+ dishes and "
          "share 40%+, **low** = fewer, **recipes only** = recipes but no dish knowledge, **absent** = neither.")
ZONE_DOCS = {"europe": ("Europe", {"Europe"}), "asia": ("Asia", {"Asia"}), "africa": ("Africa", {"Africa"}),
             "americas": ("the Americas and the Caribbean", {"North America", "Latin America", "Caribbean"}),
             "oceania": ("Oceania", {"Oceania"}), "middle_east": ("the Middle East and North Africa",
                                                                  {"Middle East & North Africa"})}
CONTINENT_DOC = {"Europe": "europe", "Asia": "asia", "Africa": "africa", "North America": "americas",
                 "South America": "americas", "Oceania": "oceania", "Insular Oceania": "oceania", "Eurasia": "asia"}
PER_COUNTRY_CAP = 40   # the 500-dish plan takes at most this many from one country, for variety


def doc_of(row: dict) -> str:
    """Which zone report a country goes in: its place in the tree, else its Wikidata continent."""
    for key, (_, zones) in ZONE_DOCS.items():
        if row["zone"] in zones:
            return key
    if "Middle East" in row.get("part_of", []):
        return "middle_east"
    for c in row["continents"]:
        if c in CONTINENT_DOC:
            return CONTINENT_DOC[c]
    return "other"


def save(path: Path, lines: list[str]) -> None:
    """One report, one blank line at most between blocks and a single newline at the end (Unix line ends)."""
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def pct(x: float | None) -> str:
    return "" if x is None else f"{x:.0%}"


def table(head: list[str], rows: list[list[object]]) -> list[str]:
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---" if i == 0 else "---:" for i in range(len(head))) + "|"]
    out += ["| " + " | ".join(str(c).replace("|", "/") for c in r) + " |" for r in rows]
    return out


def country_rows(rows: list[dict]) -> list[list[object]]:
    return [[r["country"], r["coverage"], r["dishes"], r["dishes_with_recipes"], r["families"], r["variants"],
             f"{r['recipes']:,}", r["missing_family_members"], pct(r["share_known"])] for r in rows]


HEAD = ["Country", "Coverage", "Dishes", "With recipes", "Families", "Variants", "Recipes", "Missing", "Share"]


def next_500(res: dict) -> list[dict]:
    """The 500 ready dishes to add first: tier 1 countries first, a dish whose family we have before one whose
    family we lack, with a Wikipedia article, at most PER_COUNTRY_CAP per country, then round-robin by country."""
    tier = {p["country"]: p["tier"] for p in res["priority"]}
    ready = [b for b in res["backlog"] if b["status"] == "ready"]
    by_country = defaultdict(list)
    for b in sorted(ready, key=lambda b: (not any(f["family_in_everflavor"] for f in b["families"]),
                                          len(b["sources"]) < 2, b["dish"])):
        if len(by_country[b["country"]]) < PER_COUNTRY_CAP:
            by_country[b["country"]].append(b)
    order = sorted(by_country, key=lambda c: (tier.get(c, 4), -len(by_country[c]), c))
    out: list[dict] = []
    i = 0
    while len(out) < 500 and any(i < len(by_country[c]) for c in order):
        out += [by_country[c][i] for c in order if i < len(by_country[c])][:500 - len(out)]
        i += 1
    return out


def write_reports(res: dict, docs: Path, today: str) -> None:
    docs.mkdir(parents=True, exist_ok=True)
    rows = res["rows"]
    for r in rows:
        r.setdefault("part_of", [])
    groups = defaultdict(list)
    for r in rows:
        groups[doc_of(r)].append(r)
    status = Counter(b["status"] for b in res["backlog"])
    ready_by = Counter(b["country"] for b in res["backlog"] if b["status"] == "ready")
    review_by = Counter(b["country"] for b in res["backlog"] if b["status"] == "needs_review")
    top_cut = 10

    # ---------------------------------------------------------------- the world
    w = [f"# World coverage (audit, {today})", "",
         ("Which parts of the world EverFlavor covers, which it lacks, and where the next dishes should come from. "
         "Built by `scripts/knowledge/coverage_audit.py`; the data is in `data/knowledge/coverage/`. Nothing was "
         "added to the app."), "", CAVEAT, "", "## By zone", ""]
    zrows = []
    for key, (label, _) in ZONE_DOCS.items():
        g = groups[key]
        zrows.append([f"[{label}](coverage_{key}.md)", len(g), sum(r["in_taxonomy"] for r in g),
                      sum(r["dishes"] > 0 for r in g), sum(r["dishes"] for r in g), f"{sum(r['recipes'] for r in g):,}",
                      sum(ready_by[r["country"]] for r in g), sum(review_by[r["country"]] for r in g)])
    w += table(["Zone", "Countries", "In the tree", "With dishes", "Dishes", "Recipes", "Ready to add", "To review"], zrows)
    total_rec = sum(r["recipes"] for r in rows) or 1
    total_dish = sum(r["dishes"] for r in rows) or 1
    over = sorted(rows, key=lambda r: -r["recipes"])[:top_cut]
    w += ["", "## Over-represented", "",
          "Where most of the recipes are (share of all recipes with a known country) and the dishes behind them:", ""]
    w += table(["Country", "Recipes", "Share of recipes", "Dishes", "Share of dishes"],
               [[r["country"], f"{r['recipes']:,}", pct(r["recipes"] / total_rec), r["dishes"], pct(r["dishes"] / total_dish)]
                for r in over])
    under = [r for r in rows if r["coverage"] == "recipes only"]
    big_absent = sorted([r for r in rows if r["coverage"] == "absent" and (r["population"] or 0) >= 20_000_000],
                        key=lambda r: -(r["population"] or 0))
    w += ["", "## Under-represented", "",
          f"- **Recipes but no dish knowledge** ({len(under)}): "
          + ", ".join(f"{r['country']} ({r['recipes']:,})" for r in sorted(under, key=lambda r: -r["recipes"])) + ".",
          f"- **Absent, 20 million people or more** ({len(big_absent)}; population from Wikidata): "
          + ", ".join(r["country"] for r in big_absent) + ".",
          (f"- **Absent in all**: {len(res['missing_countries'])} countries and territories with neither dishes nor recipes "
          "(`missing_countries.json`)."), "",
          "## The expansion backlog", "",
          (f"{len(res['backlog']):,} dishes Wikidata lists in a family that we do not have: **{status['ready']:,} ready**, "
          f"**{status['needs_review']:,} to review** and **{status['blocked']:,} blocked** (no country of origin), "
          "by the rules in [publishing_rules.md](publishing_rules.md). Every one would be a knowledge-only dish: "
          "none comes with a recipe."), ""]
    plan = next_500(res)
    by_zone = Counter(doc_of(next(r for r in rows if r["country"] == b["country"])) for b in plan)
    by_c = Counter(b["country"] for b in plan)
    w += ["## If EverFlavor adds 500 dishes next", "",
          (f"A fixed rule, not a taste: ready dishes only; countries in priority order (tier 1 first); within a "
          f"country, dishes whose family EverFlavor already has first (they join the graph at once), then those with "
          f"a Wikipedia article; at most {PER_COUNTRY_CAP} from one country; then one country after another. The "
          f"list is `data/knowledge/coverage/next_500.json` ({len(plan)} dishes)."), ""]
    w += table(["Zone", "Dishes"], [[ZONE_DOCS[z][0] if z in ZONE_DOCS else z, n] for z, n in by_zone.most_common()])
    w += ["", "By country: " + ", ".join(f"{c} {n}" for c, n in by_c.most_common()) + ".", "",
          ("Why so few from Africa and Oceania: Wikidata files few of their dishes under a family "
          "with a country of origin, so they have few ready dishes. Growing them needs a new source (their "
          "Wikipedia cuisine lists, as notebook 11 reads for 54 countries today), not a guess."), "",
          "## Priority tiers", "",
          "- **Tier 1:** in the place tree and 20+ ready dishes, or 200+ recipes with fewer than 15 dishes.",
          "- **Tier 2:** 5+ dishes ready or to review, or 50+ recipes with fewer than 5 dishes.",
          "- **Tier 3:** any other gap.", "",
          "Cultural importance is not scored: no source we use measures it, and we do not guess it.", ""]
    w += table(["Tier", "Country", "Zone", "Coverage", "Why"],
               [[p["tier"], p["country"], p["zone"], p["coverage"], p["why"]] for p in res["priority"] if p["tier"] < 3])
    save(docs / "coverage_world.md", w)
    (docs.parents[1] / "data" / "knowledge" / "coverage" / "next_500.json").write_text(
        json.dumps({"rule": "coverage_world.md, 'If EverFlavor adds 500 dishes next'", "dishes": plan},
                   ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # ---------------------------------------------------------------- one page per zone
    for key, (label, _) in ZONE_DOCS.items():
        g = sorted(groups[key], key=lambda r: (r["taxonomy_region"] or "~", -r["dishes"], -r["recipes"], r["country"]))
        z = [f"# Coverage: {label} ({today})", "", "Back to [world coverage](coverage_world.md).", "", CAVEAT, ""]
        regions = defaultdict(list)
        for r in g:
            regions[r["taxonomy_region"] or "Not in the place tree yet"].append(r)
        for region, rs in regions.items():
            shown = [r for r in rs if r["in_taxonomy"] or r["missing_family_members"] or r["recipes"]]
            if not shown:
                continue
            z += [f"## {region}", ""] + table(HEAD, country_rows(shown)) + [""]
        if key == "europe":
            z += ["## The countries asked about", ""]
            have = {r["country"]: r for r in g}
            from coverage_audit import EUROPE_ASKED
            for c in EUROPE_ASKED:
                r = have.get(c)
                if not r:
                    continue
                fams = ", ".join(r["family_names"][:8]) or "none"
                z += [f"### {c}", "",
                      (f"- Coverage: **{r['coverage']}** ({r['dishes']} dishes, {r['dishes_with_recipes']} with recipes, "
                      f"{r['recipes']:,} recipes; place tree: {' > '.join(r['taxonomy_path']) or 'not in it yet'})."),
                      f"- Its listed dishes with the most recipes (the country's Wikipedia list includes shared dishes): {', '.join(r['representative_dishes']) or 'none'}.",
                      f"- Families present: {fams}.",
                      (f"- Missing (Wikidata family members we lack, {r['missing_family_members']}): "
                      f"{', '.join(r['missing_examples']) or 'none listed'}."), ""]
            z += [("The Balkans are not a region of the place tree: Albania and Croatia sit under Mediterranean Europe, "
                  "Bulgaria under Eastern Europe, and Serbia, Bosnia and Herzegovina, North Macedonia, Montenegro, "
                  "Kosovo and Slovenia are not in it. Adding a Balkans region needs a published source that draws it, "
                  "as the planner's rule for new levels says."), ""]
        else:
            z += ["## Countries with the most to add", ""]
            best = sorted(g, key=lambda r: -(ready_by[r["country"]] + review_by[r["country"]]))[:15]
            for r in best:
                if ready_by[r["country"]] + review_by[r["country"]] == 0:
                    break
                z += [(f"- **{r['country']}** ({r['coverage']}; {ready_by[r['country']]} ready, "
                      f"{review_by[r['country']]} to review): {', '.join(r['missing_examples'][:8])}.")]
            z += [""]
        save(docs / f"coverage_{key}.md", z)

    # ---------------------------------------------------------------- dish families and variants
    f = [f"# Dish family gaps ({today})", "",
         ("How much of each Wikidata dish family (notebook 15) EverFlavor has. \"Missing by zone\" counts only members "
         "with a country we can place."), "", "## The families asked about", ""]
    asked = [r for rs in res["family_audit"].values() for r in rs]
    f += table(["Family", "Members", "We have", "Missing", "Share", "Missing by zone", "Missing, for example"],
               [[r["family"], r["members"], r["have"], r["missing"], pct(r["share"]),
                 ", ".join(f"{k} {v}" for k, v in list(r["missing_by_zone"].items())[:4]),
                 ", ".join(r["missing_examples"][:5])] for r in asked])
    weak = [r for r in res["families"] if r["members"] >= 10 and (r["share"] or 0) < 0.3]
    f += ["", f"## Weakly covered families (10+ members, under 30% present: {len(weak)})", ""]
    f += table(["Family", "Members", "We have", "Share", "Missing, for example"],
               [[r["family"], r["members"], r["have"], pct(r["share"]), ", ".join(r["missing_examples"][:6])]
                for r in sorted(weak, key=lambda r: -r["missing"])[:40]])
    f += ["", ("Street food is not a Wikidata family of dishes (no \"subclass of\" street food links), so it cannot "
          "be measured this way."), ""]
    save(docs / "dish_family_gap_report.md", f)

    v = [f"# Variant gaps ({today})", "",
         ("Families whose own dish EverFlavor has, with versions we lack: adding these joins the graph at once (each "
         "gets a \"version of\" link). Most missing first."), ""]
    v += table(["Family", "Members", "We have", "Missing", "Missing, for example"],
               [[r["family"], r["members"], r["have"], r["missing"], ", ".join(r["missing_examples"][:6])]
                for r in res["variants"][:40]])
    v += ["", "## The families asked about", ""]
    for name, rs in res["variants_asked"].items():
        if not rs:
            v += [f"- **{name}:** not a family on Wikidata in notebook 15."]
            continue
        r = rs[0]
        v += [(f"- **{r['family']}:** {r['have']} of {r['members']} versions present; missing: "
              f"{', '.join(r['missing_examples'][:8]) or 'none with an article'}.")]
    save(docs / "variant_gap_report.md", v)

    # ---------------------------------------------------------------- culinary regions and indigenous foodways
    c = [f"# Culinary regions and indigenous foodways ({today})", "",
         "Regions below a country: the place tree's own and the knowledge notebook's (from Wikipedia region pages).", ""]
    c += table(["Country", "Region", "In the tree", "Dishes", "Recipes"],
               [[r["country"], r["region"], "yes" if r["in_taxonomy"] else "no", r["dishes"], f"{r['recipes']:,}"]
                for r in res["regions"]])
    c += ["", "## The regions asked about", ""]
    c += table(["Country", "Region", "In the tree", "Dishes", "Recipes"],
               [[r["country"], r["region"], "yes" if r["in_taxonomy"] else "no", r["dishes"], f"{r['recipes']:,}"]
                for r in res["regions_asked"]])
    c += ["", ("India has no regions in our data: neither the recipes nor the knowledge notebook give an Indian state. "
          "Adding them needs a source that places dishes by state (a Wikipedia regional cuisine page, as for China and "
          "Mexico)."), "", "## Indigenous foodways", "",
          ("Dishes whose own Wikipedia summary or list headings mention the people or the word. A mention is not a "
          "classification: a person should check each before it is shown as indigenous food."), ""]
    c += table(["Search", "Dishes", "Countries", "Examples"],
               [[k, x["dishes"], ", ".join(f"{a} {b}" for a, b in x["countries"].items()),
                 ", ".join(x["examples"][:8])] for k, x in res["indigenous"].items()])
    c += ["", ("Very little is covered. The knowledge notebook reads national cuisine lists, which seldom list "
          "indigenous foods; a source made for them (for example the Wikipedia articles on Native American, Inuit "
          "and Aboriginal Australian cuisine) is needed, and their words and claims should be checked with care."), ""]
    save(docs / "culinary_regions.md", c)
