"""Confidence (how sure) stays apart from severity (how serious): the may-contain table, the matrix, the labels."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor.confidence import (
    Confidence,
    ProfileResponse,
    gate_confidence,
    load_may_contain,
    may_contain_in,
    severity_for,
)
from everflavor.restrictions import assess, rule_ids_from_profile
from everflavor.safety import UserProfile, check_recipe


def test_every_may_contain_row_is_sourced_and_read_by_the_gate() -> None:
    rows = load_may_contain()
    assert len(rows) >= 30
    for row in rows:
        assert row.source.startswith("https://en.wikipedia.org/wiki/") and row.note, row.item
        assert row.confidence in (Confidence.LIKELY, Confidence.POSSIBLE), row.item
        for flag in row.flags:   # what it contains must set the flags it names, or the row says nothing
            assert check_recipe(list(row.contains), "", UserProfile(avoid=(flag,)))["problems"], (row.item, flag)


def test_lines_find_their_rows() -> None:
    assert {r.flags[0] for r in may_contain_in("3 tbsp teriyaki sauce")} == {"contains_alcohol"}
    assert {r.confidence for r in may_contain_in("Classic tiramisu")} == {Confidence.LIKELY, Confidence.POSSIBLE}
    assert not may_contain_in("1 ripe avocado (guacamole)")        # "mole" only as a word


def test_severity_and_confidence_are_separate() -> None:
    assert severity_for("major", Confidence.VERIFIED) == "major"
    assert severity_for("major", Confidence.LIKELY) == "major"
    assert severity_for("major", Confidence.POSSIBLE) == "moderate"
    assert severity_for("critical", Confidence.POSSIBLE, from_gate=True) == "critical"   # the gate's call stands
    assert severity_for("major", Confidence.VERIFIED, ProfileResponse.AVOID) == "moderate"
    assert severity_for("major", Confidence.VERIFIED, ProfileResponse.WARN) == "info"
    assert severity_for("major", Confidence.VERIFIED, ProfileResponse.IGNORE) is None
    # nobody gets "warn me" for an allergy
    assert severity_for("critical", Confidence.VERIFIED, ProfileResponse.WARN, category="allergies") == "critical"


def test_gate_matches_are_labelled_not_softened() -> None:
    assert gate_confidence("1 tbsp mirin", "contains_alcohol", ["mirin"])[0] is Confidence.VERIFIED
    conf, note, source = gate_confidence("2 tbsp satay sauce", "contains_peanut", ["satay sauce"])
    assert conf is Confidence.LIKELY and "peanuts" in note and source.endswith("Peanut_sauce")
    assert gate_confidence("(dish name) Bacon pasta", "contains_pork", ["bacon"])[0] is Confidence.LIKELY


def test_results_grouped_by_how_sure() -> None:
    ids = rule_ids_from_profile(["contains_peanut", "contains_alcohol"], ["halal_friendly"])
    got = assess(["1 tbsp mirin", "3 tbsp teriyaki sauce", "2 tbsp house sauce", "200 g pork belly",
                  "2 chicken breasts", "1 tbsp satay sauce"], "Tiramisu", ids)
    lines = {c: [r["line"] for r in rows] for c, rows in got["by_confidence"].items()}
    assert lines["verified"] == ["1 tbsp mirin", "200 g pork belly"]
    assert set(lines["likely"]) == {"1 tbsp satay sauce", "3 tbsp teriyaki sauce"}
    assert lines["possible"] == ["(dish name) Tiramisu"] and lines["unknown"] == ["2 tbsp house sauce"]
    assert got["no_issue"] == ["2 chicken breasts"]
    satay = next(r for r in got["by_confidence"]["likely"] if "satay" in r["line"])
    assert satay["severity"] == "critical" and satay["sources"]   # likely, and still unsafe for a peanut allergy
    assert got["overall"] == "critical"


def test_nothing_to_watch_means_no_label_checks() -> None:
    assert assess(["2 tbsp house sauce"], "x", [])["by_confidence"]["unknown"] == []
