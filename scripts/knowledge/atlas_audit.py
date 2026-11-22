"""The Global Culinary Atlas audit: coverage by the UN's world regions (M49, as Unicode CLDR publishes them),
the next dishes to add per continent, the missing versions and the review queue. Reports only: nothing is added
or published, and every dish named comes from the Wikidata backlog of `coverage_audit.py`.

    python scripts/knowledge/fetch_regions.py    # once: data/knowledge/atlas/regions.json (CLDR)
    python scripts/knowledge/atlas_audit.py      # data/knowledge/atlas/*.json, docs/audits/global_culinary_atlas.md

Run after `coverage_audit.py` (it reads `data/knowledge/coverage/`).
"""
from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KNOW = ROOT / "data" / "knowledge"
ATLAS = KNOW / "atlas"
DOC = ROOT / "docs" / "audits" / "global_culinary_atlas.md"
PER_COUNTRY_CAP = 40      # as coverage_reports.next_500: variety over one country's long list
NEXT_SIZE = 500
DEPTH_TARGET = 20         # dishes per country counted as "deep" for the depth half of the score
BANDS = ((75, "good"), (50, "fair"), (25, "thin"), (0, "gap"))


def load(name: str) -> dict:
    return json.loads((KNOW / name).read_text(encoding="utf-8"))


def save(name: str, data: object) -> None:
    ATLAS.mkdir(parents=True, exist_ok=True)
    (ATLAS / name).write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


def band(score: float) -> str:
    return next(name for low, name in BANDS if score >= low)


def score(countries: list[dict]) -> dict:
    """Breadth: the share of the region's countries with at least one dish. Depth: the median dishes of those
    countries against DEPTH_TARGET. The score is their average, 0-100."""
    covered = [c for c in countries if c["dishes"] > 0]
    breadth = len(covered) / len(countries) if countries else 0.0
    median = statistics.median(c["dishes"] for c in covered) if covered else 0
    depth = min(1.0, median / DEPTH_TARGET)
    total = round(50 * breadth + 50 * depth, 1)
    return {"countries": len(countries), "with_dishes": len(covered), "breadth": round(breadth, 3),
            "median_dishes": median, "depth": round(depth, 3), "score": total, "band": band(total),
            "dishes": sum(c["dishes"] for c in countries), "recipes": sum(c["recipes"] for c in countries)}


def next_dishes(ready: list[dict], place: dict[str, tuple[str, str]]) -> list[dict]:
    """Up to NEXT_SIZE ready dishes: a family we have first, then two sources, at most PER_COUNTRY_CAP per
    country, taking turns between subregions and, inside each, between countries."""
    by_sub: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for b in sorted(ready, key=lambda b: (not any(f["family_in_everflavor"] for f in b["families"]),
                                          len(b["sources"]) < 2, b["dish"])):
        row = by_sub[place[b["country"]][1]][b["country"]]
        if len(row) < PER_COUNTRY_CAP:
            row.append(b)
    queues = {s: [b for i in range(PER_COUNTRY_CAP) for c in sorted(cs) for b in cs[c][i:i + 1]]
              for s, cs in by_sub.items()}
    out: list[dict] = []
    i = 0
    while len(out) < NEXT_SIZE and any(i < len(q) for q in queues.values()):
        out += [queues[s][i] for s in sorted(queues) if i < len(queues[s])][:NEXT_SIZE - len(out)]
        i += 1
    return out


def main() -> None:
    regions = json.loads((ATLAS / "regions.json").read_text(encoding="utf-8"))
    by_iso = regions["countries"]             # ISO -> {"continent", "subregion"}
    coverage = load("coverage/country_coverage.json")["countries"]
    backlog = load("coverage/expansion_backlog.json")["dishes"]
    today = date.today().isoformat()
    about = {"built_on": today, "by": "scripts/knowledge/atlas_audit.py",
             "regions": regions["source"], "dishes": "data/knowledge/coverage/ (Wikidata, our knowledge notebook)"}

    rows = [c for c in coverage if c["iso"] in by_iso]
    unplaced = sorted(c["country"] for c in coverage if c["iso"] not in by_iso and (c["dishes"] or c["recipes"]))
    place = {c["country"]: (by_iso[c["iso"]]["continent"], by_iso[c["iso"]]["subregion"]) for c in rows}
    by_sub: dict[str, list[dict]] = defaultdict(list)
    by_cont: dict[str, list[dict]] = defaultdict(list)
    for c in rows:
        by_sub[place[c["country"]][1]].append(c)
        by_cont[place[c["country"]][0]].append(c)
    sub_cont = {s: by_iso[cs[0]["iso"]]["continent"] for s, cs in by_sub.items()}

    placed = [b for b in backlog if b["country"] in place]
    status = {s: Counter(b["status"] for b in placed if place[b["country"]][1] == s) for s in by_sub}
    subregions = []
    for s, cs in sorted(by_sub.items(), key=lambda x: (sub_cont[x[0]], x[0])):
        sc = score(cs)
        sc.update({"subregion": s, "continent": sub_cont[s], "backlog": dict(status[s]),
                   "countries_without_dishes": sorted(c["country"] for c in cs if c["dishes"] == 0)})
        subregions.append(sc)
    continents = [{"continent": k, **score(v)} for k, v in sorted(by_cont.items())]
    countries = [{"country": c["country"], "iso": c["iso"], "continent": place[c["country"]][0],
                  "subregion": place[c["country"]][1], "dishes": c["dishes"], "recipes": c["recipes"],
                  "families": c["families"], "variants": c["variants"], "coverage": c["coverage"]}
                 for c in sorted(rows, key=lambda c: c["country"])]
    save("coverage_scores.json", {"about": about, "rule": score.__doc__.split("\n")[0] + " " + " ".join(
        score.__doc__.split("\n")[1:]).strip(), "bands": {n: lo for lo, n in BANDS},
        "continents": continents, "subregions": subregions, "countries": countries,
        "countries_not_placed": unplaced})
    save("missing_regions.json", {"about": about, "subregions": [
        {k: s[k] for k in ("subregion", "continent", "countries", "with_dishes", "score", "band",
                           "countries_without_dishes")} for s in subregions if s["band"] in ("gap", "thin")]})

    variants = [b for b in placed if b["status"] != "blocked" and any(f["family_in_everflavor"] for f in b["families"])]
    save("missing_variants.json", {"about": about, "rule": "Backlog dishes (ready or to review) whose Wikidata "
                                   "family is a dish EverFlavor has: versions of a dish we already show.",
                                   "subregions": {s: sorted(({"dish": b["dish"], "wikidata": b["wikidata"],
                                                              "country": b["country"], "status": b["status"],
                                                              "version_of": [f["name"] for f in b["families"]
                                                                             if f["family_in_everflavor"]]}
                                                             for b in variants if place[b["country"]][1] == s),
                                                            key=lambda r: (r["country"], r["dish"]))
                                                  for s in sorted(by_sub)}})
    backlog_rows = defaultdict(list)
    for b in placed:
        backlog_rows[place[b["country"]][1]].append({"dish": b["dish"], "wikidata": b["wikidata"],
                                                     "country": b["country"], "status": b["status"],
                                                     "problems": b["problems"]})
    save("regional_expansion_backlog.json", {"about": about, "not_placed": len(backlog) - len(placed),
                                             "subregions": {s: sorted(v, key=lambda r: (r["status"], r["country"],
                                                                                        r["dish"]))
                                                            for s, v in sorted(backlog_rows.items())}})
    review = [b for b in backlog if b["status"] == "needs_review"]
    reasons = Counter(p for b in review for p in b["problems"])
    save("publication_review_queue.json", {
        "about": about, "rule": "Every backlog dish a person must check before it can be added; nothing here is "
        "published. Grouped by the problem found.", "by_problem": dict(reasons.most_common()),
        "dishes": [{"dish": b["dish"], "wikidata": b["wikidata"], "country": b["country"] or "(none)",
                    "subregion": place.get(b["country"], ("", "(not placed)"))[1], "problems": b["problems"]}
                   for b in sorted(review, key=lambda b: (b["country"], b["dish"]))]})

    ready = [b for b in placed if b["status"] == "ready"]
    plans = {}
    for cont in sorted(by_cont):
        picked = next_dishes([b for b in ready if place[b["country"]][0] == cont], place)
        plans[cont] = picked
        save(f"{cont.replace(' ', '_')}_Next_500.json", {
            "about": about, "rule": next_dishes.__doc__.replace("\n   ", ""), "count": len(picked),
            "dishes": [{"dish": b["dish"], "wikidata": b["wikidata"], "country": b["country"],
                        "subregion": place[b["country"]][1], "families": [f["name"] for f in b["families"]],
                        "sources": b["sources"]} for b in picked]})
    write_doc(today, regions, continents, subregions, plans, reasons, len(review), unplaced, len(variants))
    print(f"{len(subregions)} subregions; next dishes " + ", ".join(f"{k} {len(v)}" for k, v in plans.items()))


def grouped(reasons: Counter) -> list[tuple[str, int, str]]:
    """The review problems by kind: one line for "not in the place tree yet" and one for "not a country today",
    with the most common names, instead of one line per country."""
    kinds: dict[str, Counter] = defaultdict(Counter)
    for problem, n in reasons.items():
        if problem.endswith(" is not in the place tree yet"):
            kinds["a country the place tree lacks yet"][problem.removesuffix(" is not in the place tree yet")] += n
        elif "is not one of today's countries" in problem:
            kinds["not a country today (a region, city or former state): a person places it"][
                problem.split("'")[1]] += n
        else:
            kinds[problem][""] += n
    out = []
    for kind, names in kinds.items():
        top = [f"{k} {v}" for k, v in names.most_common(6) if k]
        out.append((kind, sum(names.values()), f" ({', '.join(top)}{', ...' if len(names) > 6 else ''})" if top else ""))
    return sorted(out, key=lambda x: -x[1])


def write_doc(today: str, regions: dict, continents: list[dict], subregions: list[dict], plans: dict,
              reasons: Counter, review: int, unplaced: list[str], variants: int) -> None:
    head = "| Region | Countries | With dishes | Median dishes | Score | Band | Ready | To review | Blocked |"
    line = "|---|---:|---:|---:|---:|---|---:|---:|---:|"

    def row(name: str, s: dict) -> str:
        b = s.get("backlog", {})
        return (f"| {name} | {s['countries']} | {s['with_dishes']} | {s['median_dishes']:g} | {s['score']:g} | "
                f"{s['band']} | {b.get('ready', '')} | {b.get('needs_review', '')} | {b.get('blocked', '')} |")

    out = [f"# Global Culinary Atlas ({today})", "",
           ("Coverage of the world's food by the UN's regions (M49), from Unicode CLDR "
           f"{regions['source']['version']} (Unicode License V3). Reports only: nothing is added or published."),
           ("Every dish named comes from the Wikidata backlog (`coverage_audit.py`); no dish, fact or link is "
           "invented. Data: `data/knowledge/atlas/`, written by `scripts/knowledge/atlas_audit.py`."), "",
           "## How the score works", "",
           "- **Breadth:** the share of the region's countries with at least one dish.",
           (f"- **Depth:** the median number of dishes of those countries, against {DEPTH_TARGET} (more counts as "
           "full)."),
           "- **Score:** the average of the two, 0 to 100: good from 75, fair from 50, thin from 25, else a gap.",
           (f"- {sum(c['countries'] for c in continents)} countries and territories are counted, every one with "
            "an ISO code that CLDR places, small territories with no cuisine of their own included, so breadth is "
            "strict."),
           ("- The UN regions have no Balkans or Siberia. Those need a published source that draws them before "
           "the atlas shows them."), "",
           "## Continents", "", "| Continent | Countries | With dishes | Median dishes | Score | Band |",
           "|---|---:|---:|---:|---:|---|"]
    out += [f"| {c['continent']} | {c['countries']} | {c['with_dishes']} | {c['median_dishes']:g} | {c['score']:g} | "
            f"{c['band']} |" for c in continents]
    out += ["", "## Subregions", "", head, line]
    out += [row(f"{s['subregion']} ({s['continent']})", s) for s in sorted(subregions, key=lambda s: s["score"])]
    gaps = [s for s in subregions if s["band"] in ("gap", "thin")]
    out += ["", "## Where the gaps are", ""]
    out += [f"- **{s['subregion']}:** {s['with_dishes']} of {s['countries']} countries have a dish; none yet in "
            f"{', '.join(s['countries_without_dishes'][:8])}{' and more' if len(s['countries_without_dishes']) > 8 else ''}."
            for s in sorted(gaps, key=lambda s: s["score"])]
    out += ["", "## The next dishes, per continent", "",
            (f"`<Continent>_Next_500.json`: up to {NEXT_SIZE} ready backlog dishes each, a dish whose family we "
            f"have first, at most {PER_COUNTRY_CAP} per country, taking turns between subregions so no one region "
            "fills the list. They are candidates for a person to approve, not additions."), ""]
    out += [f"- {k}: {len(v)} dishes from {len({b['country'] for b in v})} countries" for k, v in plans.items()]
    out += ["", "## Versions we lack, and the review queue", "",
            (f"- `missing_variants.json`: {variants} backlog dishes are versions of a dish EverFlavor already "
            "shows (their Wikidata family is one of our dishes), by subregion."),
            f"- `publication_review_queue.json`: {review} dishes need a person first. The problems found:"]
    out += [f"  - {kind}: {n}{examples}" for kind, n, examples in grouped(reasons)]
    out += ["", "## Not placed", "",
            (f"Places with dishes or recipes but no current ISO code, so no UN region: {', '.join(unplaced)}. "
             "They stay in the country reports.") if unplaced else "None: every place with dishes or recipes has one."]
    DOC.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
