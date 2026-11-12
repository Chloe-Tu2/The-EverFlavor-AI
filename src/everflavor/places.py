"""Places on the Food Discovery Map, with what we know about each and how sure we are (docs/plans/MAP.md).

Trust first: every diet or cultural claim carries an evidence level and the reason, and nothing is claimed
without one. Unknown is fine; wrong is not.

- **verified**: a certifier's or a government's record, or the business's own website, entered by a person with
  the link and the date checked (`data/reference/place_evidence.csv`). Only these may say "certified".
- **likely**: OpenStreetMap's tags (contributors' reports), or the business's own name ("Al-Aqsa Halal Meat").
- **unknown**: everything else ("Please check with the business").

Never claimed at all: authenticity scores, freshness, quality, "best", or that a store carries one product.

    >>> place_facts(row)["diet"]    # [{"tag": "halal", "level": "likely", "label": "Likely halal-friendly", ...}]
"""
from __future__ import annotations

import re
from collections.abc import Iterable

import pandas as pd

__all__ = ["DIET_TAGS", "LEVELS", "cuisine_indicators", "diet_evidence", "diet_label", "place_facts"]

LEVELS = ("verified", "likely", "unknown")
DIET_TAGS = ("halal", "kosher", "vegetarian", "vegan")
# How each tag reads at each level (never the bare word: "halal" alone would sound like a certification)
_LABELS = {
    "halal": {"verified": "Halal-certified", "likely": "Likely halal-friendly"},
    "kosher": {"verified": "Kosher-certified", "likely": "Likely kosher-friendly"},
    "vegetarian": {"verified": "Vegetarian-only (confirmed)", "likely": "Likely vegetarian-friendly"},
    "vegan": {"verified": "Vegan-only (confirmed)", "likely": "Likely vegan-friendly"},
}
UNKNOWN_LABEL = "Diet status unknown: please check with the business"
_NAME_WORDS = {"halal": r"\bhalal\b", "kosher": r"\bkosher\b", "vegetarian": r"\bvegetarian\b", "vegan": r"\bvegan\b"}
# OpenStreetMap cuisine values that name a country's or region's food, shown as written there
_CUISINE_NAMES = {"tex-mex": "Tex-Mex", "steak_house": "steakhouse", "middle_eastern": "Middle Eastern",
                  "latin_american": "Latin American"}


def diet_label(tag: str, level: str) -> str:
    """The words for one diet tag at one evidence level ("Likely halal-friendly"); unknown has one sentence."""
    if level not in LEVELS or tag not in _LABELS:
        raise ValueError(f"unknown diet tag or level: {tag}, {level}")
    return _LABELS[tag].get(level, UNKNOWN_LABEL)


def diet_evidence(row: pd.Series, verified: Iterable[dict] = ()) -> list[dict[str, str]]:
    """What is known about a place's diets, strongest evidence first, one entry per tag, each with its reason.

    Args:
        row: A place (name, diet_<tag> as OpenStreetMap reports it: True, False or missing).
        verified: Rows from the team's evidence table for this place (tag, source, checked, checked_by); only these
            make a tag "verified".

    A tag with no evidence has no entry (the page shows UNKNOWN_LABEL); OpenStreetMap's "no" is not shown either:
    a missing "yes" is not a "no" we could stand behind.
    """
    out: dict[str, dict[str, str]] = {}
    for record in verified:
        tag = str(record.get("tag", ""))
        if tag in _LABELS and str(record.get("source", "")).startswith("https://"):
            out[tag] = {"tag": tag, "level": "verified", "label": diet_label(tag, "verified"),
                        "reason": f"Checked {record.get('checked', '')} by {record.get('checked_by', 'the team')}",
                        "source": str(record["source"])}
    raw_name = row.get("name")
    name = raw_name if isinstance(raw_name, str) else ""
    for tag in DIET_TAGS:
        if tag in out:
            continue
        if row.get(f"diet_{tag}") is True:
            out[tag] = {"tag": tag, "level": "likely", "label": diet_label(tag, "likely"),
                        "reason": f"OpenStreetMap contributors list it as {tag}", "source": "OpenStreetMap"}
        elif re.search(_NAME_WORDS[tag], name, re.IGNORECASE):
            out[tag] = {"tag": tag, "level": "likely", "label": diet_label(tag, "likely"),
                        "reason": f"Its name says \"{tag}\"", "source": "the business's name"}
    return sorted(out.values(), key=lambda e: LEVELS.index(e["level"]))


def cuisine_indicators(row: pd.Series) -> list[dict[str, str]]:
    """The place's food focus as facts with their source, never a judgement ("authentic" is not one of them)."""
    out = []
    cuisines = row.get("cuisine")
    listed = [str(c) for c in cuisines] if cuisines is not None and len(cuisines) else []
    if listed:
        names = ", ".join(_CUISINE_NAMES.get(c, c.replace("_", " ")) for c in listed)
        out.append({"text": f"OpenStreetMap lists its cuisine as {names}", "source": "OpenStreetMap"})
    hint = str(row.get("name_hint") or "")
    if hint and hint not in listed:
        out.append({"text": f"Its name suggests {hint} food", "source": "the business's name"})
    return out


def place_facts(row: pd.Series, verified: Iterable[dict] = ()) -> dict[str, object]:
    """Everything the place card shows, each claim with its evidence: kind, diets, cuisine indicators, hours."""
    hours, name = row.get("opening_hours"), row.get("name")
    return {"name": name.strip() if isinstance(name, str) and name.strip() else f"Unnamed {row.get('category', 'place')}",
            "kind": str(row.get("category") or "place"),
            "diet": diet_evidence(row, verified),
            "indicators": cuisine_indicators(row),
            "hours": str(hours) if isinstance(hours, str) and hours.strip() else "Hours not listed",
            "note": "From OpenStreetMap: unverified unless marked verified. Check with the business before you go."}
