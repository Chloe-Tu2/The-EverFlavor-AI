"""The Food Discovery Map's claims (places.py): every diet or cuisine claim has evidence; certified needs a record."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor.places import (
    UNKNOWN_LABEL,
    cuisine_indicators,
    diet_evidence,
    diet_label,
    place_facts,
)


def test_certified_only_with_a_checked_record() -> None:
    row = pd.Series({"name": "Al-Aqsa Halal Meat", "diet_halal": True})
    assert [(e["level"], e["label"]) for e in diet_evidence(row)] == [("likely", "Likely halal-friendly")]
    record = {"tag": "halal", "source": "https://example.org/certified-list", "checked": "2026-11-11",
              "checked_by": "a teammate"}
    got = diet_evidence(row, [record])
    assert got[0]["level"] == "verified" and got[0]["label"] == "Halal-certified"
    assert diet_evidence(row, [dict(record, source="a phone call")])[0]["level"] == "likely"   # no link, no verified


def test_name_and_tags_are_likely_and_say_why_and_no_is_never_shown() -> None:
    by_name = diet_evidence(pd.Series({"name": "Trendy Vegan"}))
    assert by_name == [{"tag": "vegan", "level": "likely", "label": "Likely vegan-friendly",
                        "reason": "Its name says \"vegan\"", "source": "the business's name"}]
    assert diet_evidence(pd.Series({"name": "Joe's Grill", "diet_halal": False})) == []
    assert diet_evidence(pd.Series({"name": "Vegetables Galore"})) == []       # "vegetables" is not "vegetarian"


def test_words_never_claim_more_than_the_level() -> None:
    for tag in ("halal", "kosher", "vegetarian", "vegan"):
        assert "likely" in diet_label(tag, "likely").lower()
        assert diet_label(tag, "unknown") == UNKNOWN_LABEL
    with pytest.raises(ValueError):
        diet_label("organic", "verified")


def test_cuisine_is_reported_with_its_source_never_judged() -> None:
    row = pd.Series({"cuisine": np.array(["lebanese", "middle_eastern"]), "name_hint": "halal"})
    texts = [i["text"] for i in cuisine_indicators(row)]
    assert texts == ["OpenStreetMap lists its cuisine as lebanese, Middle Eastern", "Its name suggests halal food"]
    assert not any("authentic" in t.lower() or "best" in t.lower() for t in texts)
    facts = place_facts(pd.Series({"name": None, "category": "grocery"}))
    assert facts["name"] == "Unnamed grocery" and facts["hours"] == "Hours not listed" and facts["diet"] == []
