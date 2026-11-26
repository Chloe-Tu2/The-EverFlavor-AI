"""Atlas health, every run: the five measures, the atlas debt per country and region, release readiness, and the
session handoff. Audit only: it reads the latest audit files, changes nothing and marks nothing reviewed.

    python scripts/knowledge/atlas_health.py   # last in the audit chain (after walter_gaps.py, review_impact.py)

Atlas debt is like technical debt, for the atlas. Each country with a dish gets points for each gap, weighted by
how much the gap costs the atlas (med27-coder, 2026-11-24; "no family" is Claude's proposal, same as a story):
  - no culinary region data (no dish with a culinary region)                       3
  - no story (no dish with a story sentence: History, Origin, Culture and similar sections)                            2
  - no dish family                                                                  2
  - only one dish                                                                   2
  - no photo (no verified dish photo and no cuisine photo that passes the rules)    1
  - weak Walter coverage (its dishes answer fewer than 3 of the five on average)    1
The ranking by these points is the country priority list. Debt per country is the fair measure over time: a new
country brings its own gaps, so the total can rise while the atlas gets better.
Writes docs/audits/atlas_health.md, release_readiness.md and curator_handoff.md, data/knowledge/atlas/atlas_debt.json
and one snapshot per commit in atlas_health_history.jsonl.
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

from quality_reports import read, save_md, table

KNOW = ROOT / "data" / "knowledge"
PLANNER = ROOT / "docs" / "plans" / "README.md"
REVIEW_ITEMS = ROOT / "docs" / "governance" / "needs_human_review.md"
HISTORY = KNOW / "atlas" / "atlas_health_history.jsonl"
WEIGHTS = {"no culinary region": 3, "no story": 2, "no family": 2, "one dish only": 2, "no photo": 1, "weak Walter": 1}
DEBTS = list(WEIGHTS)
CLAUDE_GAPS = ["no story", "weak Walter", "no family", "one dish only"]   # photos need a person; regions a source
LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")   # a Markdown link, kept as its text
TARGETS_1_0 = {"world culinary coverage (%)": 60, "Africa coverage (%)": 50, "Oceania coverage (%)": 35}
LOWER_IS_BETTER = ("atlas debt", "debt per country", "debt: ", "review items open")


def git(*args: str) -> str:
    done = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)  # noqa: S603, S607
    return done.stdout.strip()


def country_debt() -> list[dict]:
    scores = [c for c in read(KNOW / "atlas" / "country_scores.json")["countries"] if c["covered"]]
    walter = {c["country"]: c["score"] for c in read(KNOW / "quality" / "walter_country_scores.json")["countries"]}
    media = read(KNOW / "media" / "country_media_coverage.json")["countries"]
    cuisine = {i["country"] for i in read(KNOW / "media" / "cuisine_image_queue.json")["images"] if i["passes"] == "yes"}
    regions: dict[str, int] = defaultdict(int)
    for line in (KNOW / "dishes.jsonl").open(encoding="utf-8"):
        d = json.loads(line)
        if d.get("kind") == "dish" and (d.get("region") or d.get("regions")):
            regions[d["country"]] += 1   # a culinary region belongs to the listing country
    wd_regions = KNOW / "atlas" / "wikidata_culinary_regions.json"   # review item 33: only regions linked to a dish
    if wd_regions.exists():
        for r in read(wd_regions)["regions"]:
            if r["status"] == "linked":
                regions[r["country"]] += len(r["our_dishes"])
    out = []
    for c in scores:
        name = c["country"]
        gaps = {"no culinary region": regions.get(name, 0) == 0,
                "no story": c["representation_parts"]["stories"] == 0,
                "no family": c["representation_parts"]["families"] == 0,
                "one dish only": c["dishes"] == 1,
                "no photo": not media.get(name, {}).get("verified") and name not in cuisine,
                "weak Walter": walter.get(name, 0) < 3}
        out.append({"country": name, "continent": c["continent"], "subregion": c["subregion"], "dishes": c["dishes"],
                    "walter": walter.get(name), "debt": sum(WEIGHTS[g] for g in DEBTS if gaps[g]),
                    "gaps": [g for g in DEBTS if gaps[g]]})
    return sorted(out, key=lambda r: (-r["debt"], r["dishes"], r["country"]))


def gate_rows(heading: str) -> list[dict]:
    """The condition table that follows a bold version heading in the planner."""
    text = PLANNER.read_text(encoding="utf-8")
    start = text.find(heading)
    if start < 0:
        return []
    rows = []
    for line in text[start:].splitlines()[1:]:
        if line.startswith("**"):
            break
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 4 and cells[0] not in ("Area", "---"):
            rows.append({"area": cells[0], "condition": LINK.sub(r"\1", cells[1].split(";")[0]), "who": cells[2],
                         "state": cells[3]})
    return rows


def readiness(r: dict) -> str:
    state = r["state"].lower()
    if re.match(r"met\b", state):
        return "done"
    if "after the above" in state:
        return "last step"
    if "waiting" in state or "built" in state or r["who"].lower().startswith("person"):
        return "waiting on a person"
    return "open for Claude"


def review_counts() -> tuple[int, int, list[str]]:
    """(items logged, items answered, numbers of the answered ones) in needs_human_review.md."""
    rows = [line for line in REVIEW_ITEMS.open(encoding="utf-8") if re.match(r"\| \d+ \|", line)]
    answered = [line.split("|")[1].strip() for line in rows if "**Answered**" in line]
    return len(rows), len(answered), answered


def sheet_counts(name: str) -> tuple[int, int]:
    """(rows, rows with a verdict) of a review sheet."""
    path = KNOW / "review" / name
    if not path.exists():
        return 0, 0
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return len(rows), sum(bool(r.get("verdict", "").strip()) for r in rows)


def record(snapshot: dict) -> dict:
    """Keep one snapshot per commit in the history; return the latest one from another commit ({} if none)."""
    old = [json.loads(line) for line in HISTORY.open(encoding="utf-8")] if HISTORY.exists() else []
    old = [s for s in old if s.get("commit") != snapshot["commit"]]
    HISTORY.write_text("".join(json.dumps(s, ensure_ascii=False) + "\n" for s in [*old, snapshot]), encoding="utf-8")
    return old[-1] if old else {}


def change(now: dict, before: dict, keys: list[str]) -> str:
    parts = [f"{k} {before[k]} -> {now[k]}" for k in keys if k in before and before[k] != now[k]]
    return "; ".join(parts) or ("no change" if before else "first snapshot")


def main() -> None:
    metrics = read(KNOW / "atlas" / "atlas_metrics.json")
    cov, rep, enr, pre = (metrics[k] for k in ("coverage", "representation", "enrichment", "preservation"))
    un = read(KNOW / "atlas" / "culinary_coverage.json")["un_states"]
    walter = read(KNOW / "quality" / "walter_country_scores.json")["countries"]
    walter_avg = round(sum(c["score"] for c in walter) / len(walter), 2) if walter else 0.0
    debt = country_debt()
    total = sum(r["debt"] for r in debt)
    per_country = round(total / len(debt), 2) if debt else 0.0
    per_gap = {g: sum(g in r["gaps"] for r in debt) for g in DEBTS}
    by_region: dict[str, list[int]] = defaultdict(list)
    for r in debt:
        by_region[f"{r['continent']} / {r['subregion']}"].append(r["debt"])
    regions = sorted(((k, len(v), sum(v), sum(v) / len(v)) for k, v in by_region.items()), key=lambda x: -x[3])
    logged, answered, answered_ids = review_counts()
    tags, tags_done = sheet_counts("indigenous_tags.csv")
    _, facts_done = sheet_counts("focus_review.csv")
    (KNOW / "atlas" / "atlas_debt.json").write_text(json.dumps(
        {"by": "scripts/knowledge/atlas_health.py", "built_on": datetime.now().date().isoformat(), "weights": WEIGHTS,
         "total": total, "per_country": per_country, "per_gap": per_gap, "countries": debt},
        ensure_ascii=False, indent=1), encoding="utf-8")

    now_t = datetime.now()
    today = now_t.date().isoformat()
    lines = [f"# Atlas health ({today})", "",
             ("The five measures, the atlas debt and release readiness, from `scripts/knowledge/atlas_health.py` "
              f"(metrics built {metrics['generated_at']}). **Audit only.** Start a session with "
              "[curator_handoff.md](curator_handoff.md); what to review first: [review_impact.md](review_impact.md)."),
             "", "## The five measures", ""]
    for area, values in (("coverage", cov), ("representation", rep), ("enrichment", enr), ("preservation", pre)):
        lines.append(f"- **{area.capitalize()}:** " + "; ".join(f"{k} {v:,}" if isinstance(v, int) else f"{k} {v}"
                                                               for k, v in values.items()))
    lines += [(f"- **Governance:** {logged} review items logged in "
               f"[needs_human_review.md](../governance/needs_human_review.md), {answered} answered by a person; "
               "none closed by Claude."), "",
              "## Atlas debt", "",
              (f"{total} weighted debt points across {len(debt)} countries with a dish, {per_country} per country. "
               "Weights: " + ", ".join(f"{g} {w}" for g, w in WEIGHTS.items()) + ". Lowering it beats adding dishes "
               "once the coverage targets are met. Debt per country is the measure to follow: a newly covered "
               "country brings its own gaps. Most countries lack culinary region data because the place tree has "
               "few regions within countries yet; that gap needs a source first (Q1 phase 0)."), ""]
    lines += table(["Gap", "Weight", "Countries", "Points"], [[g, WEIGHTS[g], per_gap[g], WEIGHTS[g] * per_gap[g]]
                                                              for g in DEBTS])
    lines += ["", "### Regions with the most debt per country", ""]
    lines += table(["Region", "Countries", "Debt", "Per country"],
                   [[k, n, s, f"{a:.1f}"] for k, n, s, a in regions[:12]])
    lines += ["", "### Country priority (the most debt first)", "",
              "The full list: `data/knowledge/atlas/atlas_debt.json`.", ""]
    lines += table(["Country", "Dishes", "Debt", "Gaps"],
                   [[r["country"], r["dishes"], r["debt"], ", ".join(r["gaps"])] for r in debt[:30]])
    weak_walter = sorted((r for r in debt if r["walter"] is not None), key=lambda r: (r["walter"], r["country"]))[:20]
    lines += ["", "### Walter debt: the 20 weakest countries", "",
              "The average of Walter's five questions their dishes answer (0 to 5); enrichment targets.", ""]
    lines += table(["Country", "Dishes", "Walter score"], [[r["country"], r["dishes"], f"{r['walter']:.2f}"]
                                                          for r in weak_walter])

    ready: list[str] = []
    waiting: list[str] = []
    done_of: dict[str, str] = {}
    for version, heading in (("0.8", "**0.8.0 beta"), ("0.9", "**0.9.0 beta")):
        rows = gate_rows(heading)
        count: dict[str, int] = defaultdict(int)
        for r in rows:
            count[readiness(r)] += 1
            if readiness(r) == "waiting on a person":
                waiting.append(f"{version}: {r['condition']}")
        done_of[version] = f"{count['done']} of {len(rows)} conditions done"
        ready += [f"### {version}.0: {done_of[version]}", ""]
        ready += table(["Area", "Condition", "Readiness"], [[r["area"], r["condition"], readiness(r)] for r in rows])
        ready.append("")
    targets: list[list[object]] = [[k, f">= {t}%", f"{cov[k]}%", "done" if cov[k] >= t else "open"]
                                   for k, t in TARGETS_1_0.items()]
    met = sum(cov[k] >= t for k, t in TARGETS_1_0.items())
    done_of["1.0"] = f"{met} of {len(TARGETS_1_0)} coverage targets met; the rest wait on reviews"
    ready += ["### 1.0.0: coverage targets", ""]
    ready += table(["Target", "Goal", "Now", "Readiness"], targets)
    ready += ["", ("Risks: most open 0.8 and 0.9 conditions wait on people; review time, not data, sets the pace. "
                   "Every other 1.0 target (pages complete, Walter reviewed, no open critical item) waits on the "
                   "reviews above.")]
    lines += ["", "## Release readiness", "", *ready]
    save_md("atlas_health.md", lines)
    save_md("release_readiness.md", [f"# Release readiness ({today})", "",
                                     ("Done, waiting on a person, open for Claude, per release gate in the planner. "
                                      "From `scripts/knowledge/atlas_health.py`."), "", *ready])

    commit = git("rev-parse", "--short", "HEAD") + ("+work" if git("status", "--porcelain", "--untracked-files=no") else "")
    snapshot = {"date": today, "commit": commit,
                **{k: v for k, v in cov.items() if isinstance(v, (int, float))},
                "UN members with a dish": un["members_with_a_dish"],
                "dishes": sum('"kind": "dish"' in line for line in (KNOW / "dishes.jsonl").open(encoding="utf-8")),
                "dish families and categories": rep["dish families and categories"],
                "region pages": len(list((KNOW / "atlas" / "regions").glob("*.json"))),
                "countries with three dishes or more": rep["countries with three dishes or more"],
                "countries with a story": rep["countries with a story"],
                "entries with a story": enr["entries with a story (History or Origin sentences)"],
                "entries with a Wikidata origin": enr["entries with a Wikidata origin"],
                "Walter coverage score": walter_avg,
                "Indigenous traditions tracked": pre["Indigenous traditions tracked"],
                "Indigenous candidates": tags, "Indigenous candidates reviewed": tags_done,
                "reviewed cultural facts": facts_done, "review items logged": logged,
                "review items answered": answered, "review items open": logged - answered,
                "atlas debt": total, "debt per country": per_country, **{f"debt: {g}": per_gap[g] for g in DEBTS}}
    before = record(snapshot)
    campaign, kind, blocker = scoreboard(snapshot, before, per_gap, debt)
    lines[4:4] = ["## Headline", "", f"- Coverage: {snapshot['world culinary coverage (%)']}%",
                  f"- UN members: {snapshot['UN members with a dish']} of 193",
                  f"- Atlas debt: {per_country} per country", f"- Story debt: {per_gap['no story']} countries",
                  f"- Campaign: {campaign}", f"- Blocked by: {kind} ({blocker})", ""]
    save_md("atlas_health.md", lines)
    handoff(snapshot, before, now_t, done_of, waiting, debt, per_gap, regions, answered_ids)
    print(f"debt {total} ({per_country} per country) over {len(debt)} countries; {per_gap}")


# campaign health (med27-coder, 2026-11-25): status, the kind of blocker, Claude's estimate of the gain and confidence
HEALTH: dict[str, tuple[str, str, str, str]] = {
    "Q1. Regional source discovery": ("active", "source", "high", "medium"),
    "F. Southern Africa 50%": ("active", "review (3 empty countries need a person's picks, item 38)", "medium", "medium"),
    "C. Oceania 35%": ("active", "data (coverage gaps)", "medium", "high"),
    "Q2b. New story sources": ("active", "source", "high", "low"),
    "Walter debt": ("active", "data", "medium", "medium"),
    "Q4. Family recovery": ("active", "data", "low", "medium"),
    "Q3. Image completion": ("review-driven", "review", "medium", "high"),
    "G. Manual country research": ("active", "review", "medium", "medium"),
    "E. Western Asia": ("backlog", "none", "low", "medium"),
    "B. Caribbean": ("backlog", "none", "low", "medium"),
    "D. Africa 50% (complete, maintenance)": ("complete, maintenance", "none", "none", "high"),
}


def scoreboard(now: dict, before: dict, per_gap: dict[str, int], debt: list[dict]) -> tuple[str, str, str]:
    """docs/audits/campaign_scoreboard.md: every campaign's number, target, blocker and completion criteria, in the
    planner's order (med27-coder, 2026-11-25)."""
    sub = read(KNOW / "atlas" / "culinary_coverage.json")["subregions"]
    un = now["UN members with a dish"]
    debt_first = bool(before) and now["debt per country"] >= before.get("debt per country", now["debt per country"])

    def value(name: str) -> float:
        return float(now[name] if name in now else sub[name]["coverage"])

    def pct(name: str, target: float) -> list[object]:
        v = value(name)
        return [f"{v}%", f"{target}%", "met" if v >= target else f"{target - v:.1f} points"]

    south = [c for c in debt if c["subregion"] == "Southern Africa"]
    south_walter = round(sum(c["walter"] or 0 for c in south) / len(south), 2) if south else 0.0
    south_no_region = [c["country"] for c in south if "no culinary region" in c["gaps"]]
    top10_oceania = [c["country"] for c in debt[:10] if c["continent"] == "Oceania"]
    rows: list[list[object]] = [
        ["Q1. Regional source discovery", f"{per_gap['no culinary region']} countries without regional data", "90 (phase 1)",
         f"{max(per_gap['no culinary region'] - 90, 0)}", "a second free regional source (Wikidata links few dishes, item 36)"],
        ["F. Southern Africa 50%", *pct("Africa / Southern Africa", 50), "none"],
        ["C. Oceania 35%", *pct("Oceania coverage (%)", 35), "none"],
        ["Q2b. New story sources", f"{per_gap['no story']} countries without a story", "0", f"{per_gap['no story']}",
         "a new free story source (Q2a, the existing sources, is largely exhausted)"],
        ["Walter debt", f"{per_gap['weak Walter']} weak countries; average {now['Walter coverage score']} of 5",
         "0 weak", f"{per_gap['weak Walter']}", "none"],
        ["Q4. Family recovery", f"{per_gap['no family']} countries without a family", "0", f"{per_gap['no family']}",
         "none"],
        ["Q3. Image completion", f"{per_gap['no photo']} countries without a photo", "0", f"{per_gap['no photo']}",
         "a person approves every photo"],
        ["G. Manual country research", f"{193 - un} UN members without a dish", "0", f"{193 - un} members",
         "a person or a new approved source (A's automatic routes are exhausted)"],
        ["E. Western Asia", *pct("Asia / Western Asia", 80), "none"],
        ["B. Caribbean", *pct("Americas / Caribbean", 60), "none"],
        ["D. Africa 50% (complete, maintenance)", *pct("Africa coverage (%)", 50), "none; keep above 50%"],
    ]

    def yes(ok: bool) -> str:
        return "yes" if ok else "no"

    # a campaign is complete only when every condition holds (med27-coder, 2026-11-25)
    criteria: list[tuple[str, list[tuple[str, str, bool]]]] = [
        ("Q1. Regional source discovery", [
            ("countries without regional data at most 90 (phase 1, Wikidata links)",
             str(per_gap["no culinary region"]), per_gap["no culinary region"] <= 90),
            ("at most 50 (phase 2, needs a second regional source)", str(per_gap["no culinary region"]),
             per_gap["no culinary region"] <= 50)]),
        ("F. Southern Africa 50%", [
            ("coverage at least 50%", f"{value('Africa / Southern Africa')}%", value("Africa / Southern Africa") >= 50),
            ("average Walter score at least 4.0", f"{south_walter}", south_walter >= 4.0),
            ("every covered country has regional data", ", ".join(south_no_region) or "all have it",
             not south_no_region)]),
        ("C. Oceania 35%", [
            ("coverage at least 35%", f"{value('Oceania coverage (%)')}%", value("Oceania coverage (%)") >= 35),
            ("no Oceania country among the 10 highest-debt countries", ", ".join(top10_oceania) or "none",
             not top10_oceania)]),
        ("Walter debt", [("no country under 3 of 5", str(per_gap["weak Walter"]), per_gap["weak Walter"] == 0)]),
        ("Q2b. New story sources", [("no country without a story", str(per_gap["no story"]), per_gap["no story"] == 0)]),
        ("Q4. Family recovery", [("no country without a family", str(per_gap["no family"]), per_gap["no family"] == 0)]),
        ("G. Manual country research", [("every UN member has a dish", f"{un} of 193", un >= 193)]),
        ("Q3. Image completion", [("no country without a photo", str(per_gap["no photo"]), per_gap["no photo"] == 0)]),
        ("E. Western Asia", [("coverage at least 80%", f"{value('Asia / Western Asia')}%",
                              value("Asia / Western Asia") >= 80)]),
        ("B. Caribbean", [("coverage at least 60%", f"{value('Americas / Caribbean')}%",
                           value("Americas / Caribbean") >= 60)]),
        ("D. Africa 50%", [("coverage stays at least 50%", f"{value('Africa coverage (%)')}%",
                            value("Africa coverage (%)") >= 50)]),
    ]
    crit_rows = [[name, cond, now_v, yes(ok)] for name, conds in criteria for cond, now_v, ok in conds]
    done = [name for name, conds in criteria if all(ok for _, _, ok in conds)]
    rule = ("**Debt first.** Debt per country did not fall since the last snapshot "
            f"({before.get('debt per country')} -> {now['debt per country']}), so the charter's rule applies: reduce "
            "the debt (Q1, Q2, Walter, Q4) before further expansion, so Q1 comes first." if debt_first else
            "Debt per country fell since the last snapshot; expansion and debt work can both go ahead.")
    lines = [f"# Campaign scoreboard ({now['date']})", "",
             ("Where every campaign stands, in the planner's order: the number now, the next target, the gap and "
              "what blocks it. From `scripts/knowledge/atlas_health.py`; targets for E, F and B are Claude's "
              "working targets, not release gates. **Audit only.**"), "", rule, ""]
    velocity = [f"{k.removeprefix('debt: ')} {before[k]} -> {now[k]} ({now[k] - before[k]:+})"
                for k in ["atlas debt", *[f"debt: {g}" for g in DEBTS]] if k in before]
    lines += ["**Debt velocity** since " + (f"{before['commit']} ({before['date']})" if before else "the start") + ": "
              + ("; ".join(velocity) if velocity else "first snapshot") + ".", ""]
    # debt reduction efficiency (med27-coder, 2026-11-25): compares quality-focused and coverage-focused sprints
    if "dishes" in before and "atlas debt" in before:
        new = now["dishes"] - before["dishes"]
        removed = before["atlas debt"] - now["atlas debt"]
        per_country = f"{now['debt per country'] - before['debt per country']:+.2f} per country"
        lines += [("**Debt reduction efficiency:** " + (f"{removed * 100 / new:+.0f} debt points removed per 100 new "
                   f"dishes ({new:+} dishes, {removed:+} points removed, {per_country})" if new > 0 else
                   f"no new dishes; {removed:+} debt points removed ({per_country})")), ""]
    else:
        lines += ["**Debt reduction efficiency:** measured from the next snapshot on (the dish count is new).", ""]
    lines += table(["Campaign", "Now", "Next target", "Gap", "Blocked by"], rows)
    lines += ["", "## Campaign health", "",
              ("Status, what kind of thing blocks each campaign (data, source, policy, review, tooling or none), and "
               "Claude's working estimate of the gain and of how sure that estimate is (med27-coder, 2026-11-25); the "
               "estimates are judgments, not measurements."), ""]
    lines += table(["Campaign", "Status", "Blocked by", "Expected gain", "Confidence"],
                   [[name, *HEALTH.get(name, ("active", "none", "", ""))] for name, *_ in rows])
    lines += ["", "## Completion criteria", "",
              ("A campaign is complete only when every condition holds (med27-coder, 2026-11-25); complete now: "
               f"{', '.join(done) or 'none'}. The Q1 phase 1 target of 90 is what the Wikidata links can reach (24 "
               "countries without regional data have a provisional region); phase 2 waits for a second source."), ""]
    lines += table(["Campaign", "Condition", "Now", "Met"], crit_rows)
    save_md("campaign_scoreboard.md", lines)
    first = str(rows[0][0])
    return first, HEALTH.get(first, ("active", "none", "", ""))[1], str(rows[0][4])


def handoff(now: dict, before: dict, when: datetime, done_of: dict[str, str], waiting: list[str], debt: list[dict],
            per_gap: dict[str, int], regions: list[tuple], answered_ids: list[str]) -> None:
    """docs/audits/curator_handoff.md, in the session handoff format (med27-coder, 2026-11-24)."""
    better: list[str] = []
    worse: list[str] = []
    for k, v in now.items():
        if k in ("date", "commit") or k not in before or v == before[k] or not isinstance(v, (int, float)):
            continue
        (better if (v < before[k]) == k.startswith(LOWER_IS_BETTER) else worse).append(f"{k}: {before[k]} -> {v}")
    impact = ROOT / "docs" / "audits" / "review_impact.md"
    people = [[c.strip() for c in line.split("|")[1:-1]] for line in impact.read_text(encoding="utf-8").splitlines()
              if re.match(r"\| \d+ \|", line)] if impact.exists() else []
    gap = max(CLAUDE_GAPS, key=lambda g: per_gap[g])
    worst = [r["country"] for r in debt if gap in r["gaps"]][:8]
    since = before.get("commit", "")
    work = git("log", "--oneline", "--no-merges", f"{since.removesuffix('+work')}..HEAD") if since else ""
    version = re.search(r'__version__ = "([^"]+)"', (ROOT / "src" / "everflavor" / "__init__.py")
                        .read_text(encoding="utf-8"))
    top_gaps = sorted(DEBTS, key=lambda g: -WEIGHTS[g] * per_gap[g])[:3]
    minutes = sum(int(p[-1]) for p in people[:5] if p[-1].isdigit())

    def area(title: str, keys: list[str]) -> list[str]:
        return [f"## {title}", "", *[f"- {k}: {now[k]}" for k in keys],
                f"- Change since the last run: {change(now, before, keys)}", ""]

    board = ROOT / "docs" / "audits" / "campaign_scoreboard.md"
    cells = next(([c.strip() for c in line.split("|")[1:-1]] for line in board.read_text(encoding="utf-8").splitlines()
                  if line.startswith("| ") and not line.startswith("| Campaign")), []) if board.exists() else []
    current = cells[0] if cells else "see the planner's order of all campaigns"
    kind = HEALTH.get(current, ("", "none", "", ""))[1]
    lines = [f"# Curator handoff ({now['date']})", "",
             ("Read this first in a new session, then [atlas_health.md](atlas_health.md), "
              "[review_impact.md](review_impact.md) and [release_readiness.md](release_readiness.md). From "
              "`scripts/knowledge/atlas_health.py`; the history is in `data/knowledge/atlas/atlas_health_history.jsonl`. "
              "**Audit only.**"), "",
             "## Generated at", "", f"- Date: {now['date']}", f"- Time: {when.strftime('%H:%M')}",
             f"- Git commit: {now['commit']}" + (f" (compared with {since}, {before.get('date', '')})" if since else ""),
             "", "## Current status", "", f"- Branch: {git('branch', '--show-current')}",
             f"- Campaign: {current} (the first on the campaign scoreboard, in the planner's order)",
             f"- Version: {version.group(1) if version else 'unknown'}",
             *[f"- Release readiness {v}: {s}" for v, s in done_of.items()], ""]
    # the headline is the atlas debt, not the dish count (med27-coder, 2026-11-25)
    lines += ["## Headline", "", f"- Coverage: {now['world culinary coverage (%)']}%",
              f"- UN members with a dish: {now['UN members with a dish']} of 193",
              f"- Atlas debt: {now['debt per country']} per country",
              f"- Regional debt: {per_gap['no culinary region']} countries",
              f"- Story debt: {per_gap['no story']} countries", f"- Campaign: {current}",
              f"- Blocked by: {kind}" + (f" ({cells[4]})" if len(cells) > 4 else ""), ""]
    lines += ["## Atlas debt", "", f"- Current debt: {now['atlas debt']} ({now['debt per country']} per country)",
              f"- Debt change: {change(now, before, ['atlas debt', 'debt per country'])}", "- Top debt categories:",
              *[f"  {i}. {g}: {per_gap[g]} countries, {WEIGHTS[g] * per_gap[g]} points" for i, g in
                enumerate(top_gaps, start=1)],
              "- Highest-debt regions (per country):",
              *[f"  {i}. {k}: {a:.1f}" for i, (k, _, _, a) in enumerate(regions[:3], start=1)], ""]
    lines += area("Coverage", ["world culinary coverage (%)", "Africa coverage (%)", "Oceania coverage (%)",
                               "countries with a dish", "UN members with a dish"])
    lines += area("Representation", ["dish families and categories", "country pages", "region pages",
                                     "countries with three dishes or more"])
    lines += area("Enrichment", ["entries with a story", "entries with a Wikidata origin", "Walter coverage score"])
    lines += area("Preservation", ["Indigenous traditions tracked", "Indigenous candidates",
                                   "Indigenous candidates reviewed", "reviewed cultural facts"])
    added = now["review items logged"] - before.get("review items logged", now["review items logged"])
    lines += ["## Governance", "", f"- Review items open: {now['review items open']}",
              f"- Review items added since the last run: {added}",
              f"- Review items answered by a person: {now['review items answered']}"
              + (f" (items {', '.join(answered_ids)})" if answered_ids else ""),
              f"- Change since the last run: {change(now, before, ['review items open', 'review items answered'])}", ""]
    lines += ["## Work completed since the last snapshot", "",
              *([f"- {w}" for w in work.splitlines()] or ["- nothing committed since the last snapshot"]), "",
              "## What improved", "", *([f"- {x}" for x in better] or ["- nothing measured changed"]), "",
              "## What regressed", "", *([f"- {x}" for x in worse] or ["- nothing"]), "",
              "## Human review required", "", "Priority order (from review_impact.md):", "",
              *[f"{i}. {p[1]} (gate {p[2]}, about {p[-1]} minutes)" for i, p in enumerate(people[:5], start=1)], "",
              f"Estimated time for these five: about {minutes} minutes.", "",
              "## Blocked work (waiting on a person)", "", *[f"- {x}" for x in waiting], "",
              ("Impact: these hold the 0.8 and 0.9 releases. Suggested resolution: the review order above."), "",
              "## Recommended next action", "",
              "If a person is available: review the highest-impact item above.", "",
              "If running unattended:", "",
              "- Continue the current campaign as far as its review items allow.",
              (f"- Quality work Claude can do alone with the most countries: **{gap}** ({per_gap[gap]} countries; "
               f"first {', '.join(worst)})."),
              "- Regenerate the audits, atlas health and review impact; prepare evidence packets.", "",
              "## Final question", "",
              ("How much more of the world's food culture can EverFlavor represent, explain and preserve now than "
               "before this run? Coverage, representation, enrichment, preservation and governance above; the atlas "
               "debt per country says whether quality kept up.")]
    save_md("curator_handoff.md", lines)


if __name__ == "__main__":
    main()
