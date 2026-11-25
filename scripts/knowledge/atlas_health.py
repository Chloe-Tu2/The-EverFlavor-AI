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
    scoreboard(snapshot, before, per_gap)
    handoff(snapshot, before, now_t, done_of, waiting, debt, per_gap, regions, answered_ids)
    print(f"debt {total} ({per_country} per country) over {len(debt)} countries; {per_gap}")


def scoreboard(now: dict, before: dict, per_gap: dict[str, int]) -> None:
    """docs/audits/campaign_scoreboard.md: every campaign's number, target and blocker, in the planner's order."""
    sub = read(KNOW / "atlas" / "culinary_coverage.json")["subregions"]
    un = now["UN members with a dish"]
    debt_first = bool(before) and now["debt per country"] >= before.get("debt per country", now["debt per country"])

    def pct(name: str, target: float) -> list[object]:
        value = now[name] if name in now else sub[name]["coverage"]
        return [f"{value}%", f"{target}%", "met" if value >= target else f"{target - value:.1f} points"]

    rows: list[list[object]] = [
        ["A. Empty countries", f"{un} of 193 UN members", f"{min(un + 5, 193)} of 193", f"{193 - un} members",
         "none (policy decided); drops in shared_dish_origins.csv are optional"],
        ["D. Africa 50%", *pct("Africa coverage (%)", 50), "none; next Middle Africa (39.6%) and Southern Africa"],
        ["C. Oceania 35%", *pct("Oceania coverage (%)", 35), "none"],
        ["Q2. Story recovery", f"{per_gap['no story']} countries without a story", "0", f"{per_gap['no story']}",
         "none"],
        ["Walter debt", f"{per_gap['weak Walter']} weak countries; average {now['Walter coverage score']} of 5",
         "0 weak", f"{per_gap['weak Walter']}", "none"],
        ["Q1 phase 0. Regional sources", f"{per_gap['no culinary region']} countries without regional data",
         "a chosen free source", "research not started", "a person picks the source"],
        ["Q4. Family recovery", f"{per_gap['no family']} countries without a family", "0", f"{per_gap['no family']}",
         "none"],
        ["Q3. Image readiness", f"{per_gap['no photo']} countries without a photo", "0", f"{per_gap['no photo']}",
         "a person approves every photo"],
        ["E. Western Asia", *pct("Asia / Western Asia", 80), "none"],
        ["F. Southern Africa (inside D)", *pct("Africa / Southern Africa", 50), "none"],
        ["B. Caribbean", *pct("Americas / Caribbean", 60), "none"],
    ]
    rule = ("**Debt first.** Debt per country did not fall since the last snapshot "
            f"({before.get('debt per country')} -> {now['debt per country']}), so the charter's rule applies: reduce "
            "the debt (Q2, Walter, Q4) before further expansion." if debt_first else
            "Debt per country fell since the last snapshot; expansion and debt work can both go ahead.")
    lines = [f"# Campaign scoreboard ({now['date']})", "",
             ("Where every campaign stands, in the planner's order: the number now, the next target, the gap and "
              "what blocks it. From `scripts/knowledge/atlas_health.py`; targets for E, F and B are Claude's "
              "working targets, not release gates. **Audit only.**"), "", rule, ""]
    velocity = [f"{k.removeprefix('debt: ')} {before[k]} -> {now[k]} ({now[k] - before[k]:+})"
                for k in ["atlas debt", *[f"debt: {g}" for g in DEBTS]] if k in before]
    lines += ["**Debt velocity** since " + (f"{before['commit']} ({before['date']})" if before else "the start") + ": "
              + ("; ".join(velocity) if velocity else "first snapshot") + ".", ""]
    lines += table(["Campaign", "Now", "Next target", "Gap", "Blocked by"], rows)
    save_md("campaign_scoreboard.md", lines)


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

    lines = [f"# Curator handoff ({now['date']})", "",
             ("Read this first in a new session, then [atlas_health.md](atlas_health.md), "
              "[review_impact.md](review_impact.md) and [release_readiness.md](release_readiness.md). From "
              "`scripts/knowledge/atlas_health.py`; the history is in `data/knowledge/atlas/atlas_health_history.jsonl`. "
              "**Audit only.**"), "",
             "## Generated at", "", f"- Date: {now['date']}", f"- Time: {when.strftime('%H:%M')}",
             f"- Git commit: {now['commit']}" + (f" (compared with {since}, {before.get('date', '')})" if since else ""),
             "", "## Current status", "", f"- Branch: {git('branch', '--show-current')}",
             "- Campaign: A, empty country recovery (see the planner's order of all campaigns)",
             f"- Version: {version.group(1) if version else 'unknown'}",
             *[f"- Release readiness {v}: {s}" for v, s in done_of.items()], ""]
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
    lines += ["## Atlas debt", "", f"- Current debt: {now['atlas debt']} ({now['debt per country']} per country)",
              f"- Debt change: {change(now, before, ['atlas debt', 'debt per country'])}", "- Top debt categories:",
              *[f"  {i}. {g}: {per_gap[g]} countries, {WEIGHTS[g] * per_gap[g]} points" for i, g in
                enumerate(top_gaps, start=1)],
              "- Highest-debt regions (per country):",
              *[f"  {i}. {k}: {a:.1f}" for i, (k, _, _, a) in enumerate(regions[:3], start=1)], ""]
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
