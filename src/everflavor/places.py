"""Places on the Food Discovery Map, with what we know about each and how sure we are (docs/plans/MAP.md).

Trust first: every diet or cultural claim carries an evidence level and the reason, and nothing is claimed
without one. Unknown is fine; wrong is not.

- **verified**: a certifier's or a government's record, or the business's own website, entered by a person with
  the link and the date checked (`data/reference/place_evidence.csv`). Only these may say "certified".
- **likely**: OpenStreetMap's tags (contributors' reports), or the business's own name ("Al-Aqsa Halal Meat").
- **unknown**: everything else ("Please check with the business").

Never claimed at all: authenticity scores, freshness, quality, "best", or that a store carries one product.

The recipe -> ingredient -> store link: `specialty_in` finds a recipe's specialty ingredients in the team's table
(`data/reference/specialty_ingredients.csv`, each row with its source) and `find_stores_for` lists the stores
whose own cuisine or name says they likely carry that kind of food, each with the reason.

    >>> place_facts(row)["diet"]    # [{"tag": "halal", "level": "likely", "label": "Likely halal-friendly", ...}]
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .confidence import Confidence
from .stores import COUNTRY_CUISINES, COUNTRY_REGIONS

__all__ = [
    "DIET_TAGS",
    "LEVELS",
    "SPECIALTY_FILE",
    "STORE_KINDS",
    "cuisine_indicators",
    "cuisine_name",
    "diet_evidence",
    "diet_label",
    "find_stores_for",
    "load_place_evidence",
    "load_specialty_ingredients",
    "map_places",
    "place_facts",
    "specialty_in",
]

# The same confidence scale as Check my recipe and Walter (everflavor.confidence): a place is verified (a
# checked record), likely (OpenStreetMap tags, its own name) or unknown; "possible" is not used on the map
LEVELS = (Confidence.VERIFIED.value, Confidence.LIKELY.value, Confidence.UNKNOWN.value)
DIET_TAGS = ("halal", "kosher", "vegetarian", "vegan")
# How each tag reads at each level (never the bare word: "halal" alone would sound like a certification)
_LABELS = {
    "halal": {"verified": "Halal-certified", "likely": "Likely halal-friendly"},
    "kosher": {"verified": "Kosher-certified", "likely": "Likely kosher-friendly"},
    "vegetarian": {"verified": "Vegetarian-only (confirmed)", "likely": "Likely vegetarian-friendly"},
    "vegan": {"verified": "Vegan-only (confirmed)", "likely": "Likely vegan-friendly"},
}
# A verified row whose source is the business itself (its own website), not a certifier: confirmed that the
# business says so, never "certified"
_STATED_LABELS = {tag: f"{tag.capitalize()}: stated by the business" for tag in DIET_TAGS}
UNKNOWN_LABEL = "Diet status unknown: please check with the business"
# "Non-Halal Deli", "No Pork, Not Kosher", "Kosher-style Deli" (kosher-style is not kosher) or "Halal-free" must
# never read as a diet claim
_NAME_WORDS = {tag: rf"(?<![\w-])(?<!non-)(?<!non )(?<!not )(?<!no ){tag}\b(?![ -]?(?:style|free)\b)"
               for tag in DIET_TAGS}
# OpenStreetMap cuisine values that name a country's or region's food, shown as written there
_CUISINE_NAMES = {"tex-mex": "Tex-Mex", "steak_house": "steakhouse", "middle_eastern": "Middle Eastern",
                  "latin_american": "Latin American"}
ROOT = Path(__file__).resolve().parents[2]
SPECIALTY_FILE = ROOT / "data" / "reference" / "specialty_ingredients.csv"
EVIDENCE_FILE = ROOT / "data" / "reference" / "place_evidence.csv"
# Kinds of place where ingredients are bought (the map's categories; convenience stores are left out on purpose)
STORE_KINDS = ("grocery", "butcher", "seafood", "bakery", "spices", "marketplace")
NOTE = "From OpenStreetMap: unverified unless marked verified. Check with the business before you go."
_SHOP_WORDS = {"bakery": "bakery", "butcher": "butcher", "seafood": "seafood market"}


def _flag(value: object) -> bool:
    """True only for a real yes (Python's or NumPy's True); missing, NaN and False are all "not said"."""
    return value is True or (isinstance(value, np.bool_) and bool(value))


def diet_label(tag: str, level: str) -> str:
    """The words for one diet tag at one evidence level ("Likely halal-friendly"); unknown has one sentence."""
    if level not in LEVELS or tag not in _LABELS:
        raise ValueError(f"unknown diet tag or level: {tag}, {level}")
    return _LABELS[tag].get(level, UNKNOWN_LABEL)


def diet_evidence(row: pd.Series, verified: Iterable[Mapping] = ()) -> list[dict[str, str]]:
    """What is known about a place's diets, strongest evidence first, one entry per tag, each with its reason.

    Args:
        row: A place (name, diet_<tag> as OpenStreetMap reports it: True, False or missing).
        verified: Rows from the team's evidence table for this place (tag, source, checked, checked_by, basis); only
            these make a tag "verified". basis "certifier" (the default) reads "Halal-certified"; basis "business"
            (the business's own website) reads "Halal: stated by the business".

    A tag with no evidence has no entry (the page shows UNKNOWN_LABEL); OpenStreetMap's "no" is not shown either:
    a missing "yes" is not a "no" we could stand behind. But a "no" is never overruled by the business's name.
    """
    out: dict[str, dict[str, str]] = {}
    for record in verified:
        tag = str(record.get("tag", ""))
        if tag in _LABELS and str(record.get("source", "")).startswith("https://"):
            stated = str(record.get("basis") or "").strip().lower() == "business"
            out[tag] = {"tag": tag, "level": Confidence.VERIFIED.value,
                        "label": _STATED_LABELS[tag] if stated else diet_label(tag, "verified"),
                        "reason": f"Checked {record.get('checked', '')} by {record.get('checked_by') or 'the team'}",
                        "source": str(record["source"])}
    raw_name = row.get("name")
    name = raw_name if isinstance(raw_name, str) else ""
    for tag in DIET_TAGS:
        if tag in out:
            continue
        said = row.get(f"diet_{tag}")
        if _flag(said):
            out[tag] = {"tag": tag, "level": Confidence.LIKELY.value, "label": diet_label(tag, "likely"),
                        "reason": f"OpenStreetMap contributors list it as {tag}", "source": "OpenStreetMap"}
        elif said is False or isinstance(said, np.bool_):   # OpenStreetMap says no: the name does not overrule it
            continue
        elif re.search(_NAME_WORDS[tag], name, re.IGNORECASE):
            out[tag] = {"tag": tag, "level": Confidence.LIKELY.value, "label": diet_label(tag, "likely"),
                        "reason": f"Its name says \"{tag}\"", "source": "the business's name"}
    return sorted(out.values(), key=lambda e: LEVELS.index(e["level"]))


def _cuisines(row: Mapping | pd.Series) -> list[str]:
    """The cuisine values OpenStreetMap lists for a place, as plain strings."""
    cuisines = row.get("cuisine")
    if cuisines is None or isinstance(cuisines, (str, float)):
        return [cuisines] if isinstance(cuisines, str) and cuisines else []
    return [str(c) for c in cuisines]


def cuisine_name(value: str) -> str:
    """An OpenStreetMap cuisine value as words ("middle_eastern" -> "Middle Eastern", "steak_house" -> "steakhouse")."""
    return _CUISINE_NAMES.get(value, value.replace("_", " "))


_cuisine_name = cuisine_name


def cuisine_indicators(row: pd.Series) -> list[dict[str, str]]:
    """The place's food focus as facts with their source, never a judgement ("authentic" is not one of them)."""
    out = []
    listed = _cuisines(row)
    if listed:
        out.append({"text": "OpenStreetMap lists its cuisine as " + ", ".join(_cuisine_name(c) for c in listed),
                    "source": "OpenStreetMap"})
    hint = str(row.get("name_hint") or "")
    tagged = {_cuisine_name(c).lower() for c in listed}
    if hint and hint not in tagged and hint not in DIET_TAGS:   # a diet in the name is a diet claim, shown there
        out.append({"text": f"Its name suggests {hint} food", "source": "the business's name"})
    return out


def place_facts(row: pd.Series, verified: Iterable[Mapping] = ()) -> dict[str, object]:
    """Everything the place card shows, each claim with its evidence: kind, diets, cuisine indicators, hours."""
    hours, name = row.get("opening_hours"), row.get("name")
    text = {key: row.get(key) for key in ("address", "phone", "website")}
    return {"name": name.strip() if isinstance(name, str) and name.strip() else f"Unnamed {row.get('category', 'place')}",
            "kind": str(row.get("category") or "place"),
            "diet": diet_evidence(row, verified),
            "indicators": cuisine_indicators(row),
            "hours": str(hours) if isinstance(hours, str) and hours.strip() else "Hours not listed",
            **{key: value.strip() if isinstance(value, str) else "" for key, value in text.items()},
            "osm_url": f"https://www.openstreetmap.org/{row['osm_id']}" if isinstance(row.get("osm_id"), str) else "",
            "note": NOTE}


# ------------------------------------------------------------------ the team's tables
def load_specialty_ingredients(path: str | Path = SPECIALTY_FILE) -> pd.DataFrame:
    """The specialty ingredients table, checked: every row has aliases, a known store kind and an https source.

    Returns:
        One row per ingredient with aliases, cuisines and store_kinds as lists, note, source_url, licence and
        reviewed (False until a team member's name is in reviewed_by; the page says so).

    Raises:
        ValueError: listing every problem, so a bad edit to the table is caught by the tests, not by a visitor.
    """
    table = pd.read_csv(path, dtype=str, keep_default_na=False)
    problems = []
    for column in ("ingredient", "aliases", "cuisines", "store_kinds", "note", "source_url", "licence", "reviewed_by"):
        if column not in table:
            problems.append(f"missing column {column}")
    if problems:
        raise ValueError("; ".join(problems))
    for column in ("aliases", "cuisines", "store_kinds"):
        table[column] = table[column].map(lambda v: [p.strip().lower() for p in v.split(";") if p.strip()])
    seen: dict[str, str] = {}
    for row in table.to_dict("records"):
        name = str(row["ingredient"])
        if not row["aliases"] or not row["cuisines"]:
            problems.append(f"{name}: needs aliases and cuisines")
        if not str(row["source_url"]).startswith("https://"):
            problems.append(f"{name}: the source must be an https link")
        problems += [f"{name}: unknown store kind {k}" for k in row["store_kinds"] if k not in STORE_KINDS]
        for alias in row["aliases"]:
            if alias in seen:
                problems.append(f"{name}: alias {alias} is also {seen[alias]}'s")
            seen[alias] = name
    if problems:
        raise ValueError("; ".join(problems))
    table["reviewed"] = table["reviewed_by"].str.strip().ne("")
    return table


def load_place_evidence(path: str | Path = EVIDENCE_FILE) -> dict[str, list[dict[str, Any]]]:
    """The team's verified rows (place, tag, source, checked, checked_by), by OpenStreetMap id; {} when none."""
    path = Path(path)
    if not path.exists():
        return {}
    rows = pd.read_csv(path, dtype=str, keep_default_na=False)
    out: dict[str, list[dict[str, Any]]] = {}
    for record in rows.to_dict("records"):
        if record.get("osm_id") and str(record.get("source", "")).startswith("https://"):
            out.setdefault(str(record["osm_id"]), []).append({str(k): v for k, v in record.items()})
    return out


# ------------------------------------------------------------------ recipe -> ingredient -> store
def specialty_in(ingredients: Iterable[str], table: pd.DataFrame) -> list[dict[str, Any]]:
    """The recipe's specialty ingredients ("Look for"), in the table's order, each with its note and source."""
    names = [str(i).lower() for i in ingredients if isinstance(i, str)]
    out = []
    for row in table.to_dict("records"):
        if any(re.search(rf"(?<![\w']){re.escape(a)}(?![\w'])", n) for a in row["aliases"] for n in names):
            out.append({"ingredient": row["ingredient"], "note": row["note"], "source": row["source_url"],
                        "licence": row["licence"], "cuisines": list(row["cuisines"]),
                        "store_kinds": list(row["store_kinds"]), "reviewed": bool(row["reviewed"])})
    return out


def _focus(row: Mapping) -> tuple[set[str], str]:
    """A place's cuisine words from OpenStreetMap (spaces, lower case) and its name hint."""
    return {_cuisine_name(c).lower() for c in _cuisines(row)}, str(row.get("name_hint") or "")


def _match(row: Mapping, words: Sequence[str]) -> tuple[int, str] | None:
    """How a place matches the wanted cuisine words, best first: (rank, reason), or None.

    The rank is the word's position in `words` times two, plus one when only the name says so (a tag is a
    contributor's report; a name is a weaker hint).
    """
    tagged, hint = _focus(row)
    for i, word in enumerate(words):
        if word in tagged:
            return 2 * i, f"OpenStreetMap lists its cuisine as {word}"
        if word == hint:
            return 2 * i + 1, f"its name suggests {word} food"
    return None


def _title(word: str) -> str:
    return " ".join(w.capitalize() for w in word.split())


def find_stores_for(ingredients: Iterable[str], origin_country: str | None, places: pd.DataFrame,
                    table: pd.DataFrame, n: int = 10) -> dict[str, Any]:
    """Where to look for a recipe's ingredients and where to eat its cuisine, each place with its reason.

    Args:
        ingredients: The recipe's ingredient names.
        origin_country: The recipe's country ("Morocco"), or None.
        places: The map's places (notebook 03).
        table: load_specialty_ingredients().
        n: At most this many stores and this many restaurants.

    Returns:
        {"look_for": specialty_in(...), "cuisine": the cuisine word used, "stores": [...], "eat": [...],
        "note": ...}. Each store or restaurant is place_facts plus osm_id, lat, lng and "why", a sentence that says
        "likely carries ... ingredients" with its source, never that it has one product. A store only appears when
        its own cuisine tag or name matches, or when it is a supermarket (for the everyday items), so an empty list
        is a correct answer.
    """
    look_for = specialty_in(ingredients, table)
    words: list[str] = []
    for word in [COUNTRY_CUISINES.get(origin_country or ""), *[c for item in look_for for c in item["cuisines"]],
                 COUNTRY_REGIONS.get(origin_country or "")]:
        if isinstance(word, str) and word and word not in words:
            words.append(word)
    own = COUNTRY_CUISINES.get(origin_country or "", "")   # the dish's own cuisine word, the only one to eat
    result: dict[str, Any] = {"look_for": look_for, "cuisine": own or (words[0] if words else ""), "stores": [],
                              "eat": [], "note": NOTE}
    if places.empty:
        return result
    ranked_stores, ranked_eat = [], []
    for row in places.to_dict("records"):
        kind = row.get("category")
        found = _match(row, words) if words else None
        if kind == "restaurant":
            if own and found and found[0] <= 1:   # words[0] is `own`: "where can I eat this?"
                ranked_eat.append((found[0], row, f"{found[1][0].upper()}{found[1][1:]}"))
        elif kind in STORE_KINDS:
            if found and kind in _SHOP_WORDS:   # a bakery or a butcher is said to be one, not to carry groceries
                ranked_stores.append((found[0], row,
                                      f"A {_title(words[found[0] // 2])} {_SHOP_WORDS[kind]} ({found[1]})"))
            elif found:
                why = f"Likely carries {_title(words[found[0] // 2])} ingredients ({found[1]})"
                ranked_stores.append((found[0], row, why))
            elif row.get("osm_kind") == "supermarket" and str(row.get("name") or "").strip():
                ranked_stores.append((1000, row, "A supermarket, for the everyday ingredients"))
            elif kind == "spices" and any("spices" in item["store_kinds"] for item in look_for):
                ranked_stores.append((999, row, "A spice shop: ask there for the spices on your list"))
    for key, ranked in (("stores", ranked_stores), ("eat", ranked_eat)):
        ranked.sort(key=lambda r: (r[0], str(r[1].get("name") or "~")))
        seen: set[str] = set()   # one row per name: a chain's branches would fill the list
        kept = []
        for rank, row, why in ranked:
            name = str(row.get("name") or "").strip().lower()
            if name and name in seen:
                continue
            seen.add(name)
            kept.append((rank, row, why))
        result[key] = [{**place_facts(pd.Series(row)), "osm_id": row.get("osm_id"), "lat": row.get("lat"),
                        "lng": row.get("lng"), "why": why} for _, row, why in kept[:n]]
    return result


# ------------------------------------------------------------------ the map's rows
def map_places(places: pd.DataFrame, kinds: Iterable[str], cuisine: str | None = None, diet: str | None = None,
               level: str = "likely", evidence: Mapping[str, list] | None = None) -> pd.DataFrame:
    """The places the map draws, filtered, each with its card's words already decided here (not in the page).

    Args:
        places: The map's places.
        kinds: Categories to show ("grocery", "restaurant", ...).
        cuisine: A cuisine word ("moroccan"): only places whose OpenStreetMap cuisine or name says so.
        diet: A diet tag: only places with evidence for it at `level` or stronger ("verified" or "likely").
        evidence: load_place_evidence().

    Returns:
        The rows kept, plus label (the name, or "Unnamed ..."), cuisine_text, diet_text (each diet's label) and
        level (the strongest evidence for `diet`, or for any diet, else "unknown").
    """
    evidence = evidence or {}
    shown = places[places["category"].isin(list(kinds))].dropna(subset=["lat", "lng"])
    if cuisine:
        shown = shown.loc[[_match(r, [cuisine]) is not None for r in shown.to_dict("records")]]
    diets = [diet_evidence(r, evidence.get(str(r.get("osm_id")), [])) for _, r in shown.iterrows()]
    if diet:
        allowed = LEVELS[:LEVELS.index(level) + 1]
        keep = [any(e["tag"] == diet and e["level"] in allowed for e in d) for d in diets]
        shown, diets = shown.loc[keep], [d for d, k in zip(diets, keep) if k]
    out = shown.copy()
    out["label"] = [n.strip() if isinstance(n, str) and n.strip() else f"Unnamed {k}"
                    for n, k in zip(shown["name"], shown["category"])]
    out["cuisine_text"] = [", ".join(_cuisine_name(c) for c in _cuisines(r)) for r in shown.to_dict("records")]
    out["diet_text"] = ["; ".join(e["label"] for e in d) or "Diet status unknown" for d in diets]
    out["level"] = [next((e["level"] for e in d if not diet or e["tag"] == diet), Confidence.UNKNOWN.value) for d in diets]
    return out
