"""The maintenance sprint (2026-11-22): the enrichment queues' rules, the Food Graph with no broken links, the
hygiene audit and the stricter provenance fields."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "knowledge"))
sys.path.insert(0, str(ROOT / "scripts" / "governance"))

import enrichment_queues
import graph_validation
import hygiene_audit
import provenance_audit

from everflavor.domain import KnowledgeGraph
from everflavor.taxonomy import load_taxonomy


def dish(qid: str, score: int, missing: list[str], region: str = "Sichuan") -> dict:
    return {"qid": qid, "name": qid, "country": "China", "region": region, "score": score,
            "tier": "rich" if score >= 70 else "fair", "missing": missing}


def test_the_upgrade_queue_puts_the_lowest_effort_first() -> None:
    dishes = [dish("Q1", 80, []), dish("Q2", 55, ["photo"]), dish("Q3", 55, ["recipe"]),
              dish("Q4", 40, ["story", "family"])]
    q = enrichment_queues.upgrade_queue(dishes, approved=set(), passed={"Q2"}, failed=set())
    assert [r["qid"] for r in q] == ["Q2", "Q4", "Q3"]          # rich dishes are left out
    assert q[0]["rich_with_low_work"] and q[0]["score_with_low_work"] == 75
    assert not q[2]["rich_within_reach"]                       # a recipe is high work: never counted as near
    no_photo = enrichment_queues.upgrade_queue([dish("Q5", 50, ["photo"])], set(), set(), set())
    assert no_photo[0]["gaps"][0]["work"] == "high"


def test_a_missing_region_is_a_gap_but_never_guessed() -> None:
    q = enrichment_queues.upgrade_queue([dish("Q6", 50, [], region="")], set(), set(), set())
    assert q[0]["gaps"] == [{"gap": "region", "points": 10, "work": "medium",
                             "how": "a region on Wikidata or the place tree; never guessed"}]


def test_the_walter_queue_lists_what_the_waiter_cannot_tell() -> None:
    raw = {"Q1": {"name": "A", "origin": ["China"], "made_from": ["rice"], "story_candidates": ["x"],
                  "fun_fact_candidates": ["y"]},
           "Q2": {"name": "B"}}
    q = enrichment_queues.walter_queue(raw, {"Q1": {"related": ["Q2"]}})
    assert [r["qid"] for r in q] == ["Q2"]
    assert q[0]["missing"] == ["history", "origin", "ingredient_explanation", "interesting_fact", "related_dishes"]


def test_the_food_graph_has_no_broken_links() -> None:
    res = graph_validation.validate(KnowledgeGraph.load(ROOT), load_taxonomy())
    assert res["not_reaching_world"] == []
    assert res["part_of_cycles"] == []
    assert res["family_cycles"] == []
    assert res["dishes_without_edges"] == []


def test_the_hygiene_audit_finds_no_temporary_or_debug_files() -> None:
    found = hygiene_audit.audit()
    for kind in ("temporary", "debug", "scratch", "copy", "empty file"):
        assert found.get(kind, []) == [], kind


def test_the_strict_provenance_fields_read_licence_version_and_credit() -> None:
    assert provenance_audit.strict("Wikidata (CC0), dump of 2026-11-01") == {
        "licence_named": True, "version": True, "attribution": True}
    assert provenance_audit.strict("a list of dishes") == {
        "licence_named": False, "version": False, "attribution": False}
