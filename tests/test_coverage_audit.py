"""The coverage audit's backlog follows the publishing rules (docs/audits/publishing_rules.md), and the 500-dish
plan only takes ready dishes. These checks read the committed files, so a rerun that breaks a rule fails here."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COVERAGE = ROOT / "data" / "knowledge" / "coverage"


def read(name: str) -> dict:
    return json.loads((COVERAGE / name).read_text(encoding="utf-8"))


BACKLOG = read("expansion_backlog.json")["dishes"]
OURS = {json.loads(line)["qid"] for line in (ROOT / "data" / "knowledge" / "dishes.jsonl").open(encoding="utf-8")}


def test_every_candidate_is_sourced_and_new() -> None:
    assert BACKLOG and len({b["wikidata"] for b in BACKLOG}) == len(BACKLOG)
    for b in BACKLOG:
        assert b["wikidata"] not in OURS                       # never a dish we already have
        assert b["sources"][0]["licence"] == "CC0 1.0" and b["sources"][0]["url"].endswith(b["wikidata"])
        assert b["families"] and b["knowledge_only"]           # a family, and no invented recipe


def test_the_approval_state_follows_the_rules() -> None:
    for b in BACKLOG:
        if b["status"] == "blocked":
            assert not b["country"] or b["not_a_dish"]    # no country, or a brand or an event
        elif b["status"] == "ready":
            assert b["country"] and b["taxonomy_ready"] and not b["problems"] and not b["requires_review"]
            assert any(s["name"] == "Wikipedia" for s in b["sources"])
        else:
            assert b["status"] == "needs_review" and b["problems"] and b["country"]


def test_the_500_plan_takes_only_ready_dishes_with_variety() -> None:
    plan = read("next_500.json")["dishes"]
    ready = {b["wikidata"] for b in BACKLOG if b["status"] == "ready"}
    assert len(plan) == min(500, len(ready)) and {p["wikidata"] for p in plan} <= ready
    assert max(Counter(p["country"] for p in plan).values()) <= 40


def test_country_rows_add_up() -> None:
    rows = read("country_coverage.json")["countries"]
    assert len({r["country"] for r in rows}) == len(rows)
    for r in rows:
        assert r["dishes_with_recipes"] <= r["dishes"]
        assert (r["coverage"] == "absent") == (r["dishes"] == 0 and r["recipes"] == 0)
    reports = ["coverage_world", "coverage_europe", "dish_family_gap_report", "variant_gap_report", "culinary_regions"]
    assert all((ROOT / "docs" / "audits" / f"{n}.md").exists() for n in reports)
