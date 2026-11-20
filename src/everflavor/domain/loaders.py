"""Build the entities from today's tables (no change to the tables or the app).

Each function reads one record as the pipelines store it and returns one entity, checking the fields it needs.
Nothing is invented: a value the table does not have stays empty (None, "" or ()).
"""
from __future__ import annotations

import math
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import pandas as pd

from ..calories import parse_ingredient_line
from ..confidence import Confidence, MayContain
from ..dish_names import clean_title
from ..flags import flags_for_term
from ..ingredients import normalize_ingredient
from ..parsing import parse_list_string
from ..places import _cuisines, diet_evidence
from .entities import (
    Claim,
    Dish,
    Fact,
    Ingredient,
    Link,
    Nutrition,
    Place,
    Pronunciation,
    Recipe,
    RecipeLine,
    Risk,
    Source,
    Specialty,
)

PRONUNCIATION_FILE = Path(__file__).resolve().parents[3] / "data" / "reference" / "dish_pronunciation.csv"
_QID = re.compile(r"^Q[1-9]\d*$")


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _number(value: object) -> float | None:
    """A real number, or None for missing, NaN and text."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return None if math.isnan(value) else float(value)


def _strings(values: object) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        return ()
    return tuple(str(v).strip() for v in values if str(v).strip() and not str(v).startswith("http"))


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


# ------------------------------------------------------------------ Dish
def dish_id_for(qid: object, name: str, country: object = "") -> str:
    """The Wikidata QID when there is one; else a slug with the country ("mexico-chiles-en-nogada").

    Raises:
        ValueError: when there is neither a QID nor a name to make the slug from.
    """
    if isinstance(qid, str) and _QID.match(qid.strip()):
        return qid.strip()
    parts = [slug(_text(country)), slug(name)]
    if not parts[1]:
        raise ValueError("a dish needs a Wikidata QID or a name")
    return "-".join(p for p in parts if p)


def ingredient_id_for(name: object) -> str:
    """The id an ingredient name has today: its normalized name ("Plain Flour" -> "flour"); "" if none.

    Merged names (roadmap phase 1, step 2, after the team's review) will later share one id."""
    names = normalize_ingredient(name)
    return names[0] if names else ""


def load_pronunciations(path: str | Path = PRONUNCIATION_FILE) -> dict[str, Pronunciation]:
    """How to say each dish's name, by Wikidata QID; {} when the file is missing."""
    path = Path(path)
    if not path.exists():
        return {}
    table = pd.read_csv(path, dtype=str, keep_default_na=False)
    out: dict[str, Pronunciation] = {}
    for r in table.to_dict("records"):
        qid = r.get("wikidata_qid", "").strip()
        if _QID.match(qid) and r.get("native_name", "").strip():
            out.setdefault(qid, Pronunciation(r["lang"].strip(), r["native_name"].strip(), r["respelling"].strip(),
                                              r["audio_file"].strip(), r["audio_license"].strip(),
                                              r["audio_author"].strip(), r["note"].strip()))
    return out


def dish_from_record(record: Mapping[str, Any], pronunciations: Mapping[str, Pronunciation] | None = None) -> Dish:
    """A Dish from one knowledge-notebook entry (data/knowledge/dishes.jsonl, best after `tidy_dish`, which picks
    the facts Walter may say; a raw entry gives no facts)."""
    name = _text(record.get("name"))
    if not name:
        raise ValueError("a dish needs a name")
    dish_id = dish_id_for(record.get("qid"), name, record.get("country"))
    facts = tuple(Fact(str(f["text"]), str(f.get("topic", "")), str(f.get("source", "")))
                  for f in [*record.get("fun_facts", []), *record.get("more_fun_facts", [])]
                  if isinstance(f, Mapping) and f.get("text"))
    sources = tuple(Source(str(s.get("name", "")), str(s.get("url", "")), str(s.get("licence", "")),
                           str(s.get("credit", ""))) for s in record.get("sources", []) if isinstance(s, Mapping))
    links = tuple(Link(str(x.get("level", "")), str(x.get("title", "")), str(x["url"]))
                  for x in record.get("learn_more", []) if isinstance(x, Mapping) and x.get("url"))
    made_from = tuple(dict.fromkeys(i for i in (ingredient_id_for(m) for m in _strings(record.get("made_from"))) if i))
    return Dish(dish_id=dish_id, name=name, kind=_text(record.get("kind")) or "dish",
                country=_text(record.get("country")), region=_text(record.get("region")),
                regions=_strings(record.get("regions")), summary=_text(record.get("summary")), facts=facts,
                origin=_strings(record.get("origin")), made_from=made_from,
                not_to_confuse=_strings(record.get("not_to_confuse")), learn_more=links, sources=sources,
                reviewed=bool(record.get("reviewed")),
                pronunciation=(pronunciations or {}).get(dish_id))


# ------------------------------------------------------------------ Recipe
def recipe_line(text: str) -> RecipeLine:
    parsed = parse_ingredient_line(text)
    unit = parsed.get("unit")
    return RecipeLine(text=text, amount=_number(parsed.get("amount")), unit=unit if isinstance(unit, str) else None,
                      ingredient_id=ingredient_id_for(text))


def recipe_from_row(row: Mapping[Any, Any] | pd.Series) -> Recipe:
    """A Recipe from one row of the recipe tables (data/processed or data/demo). The dish is not linked here:
    `KnowledgeGraph.link_dish` does that, so a recipe whose dish is unknown keeps `dish_id` empty."""
    url = _text(row.get("url"))
    title = _text(row.get("recipe_name"))
    if not url or not title:
        raise ValueError("a recipe needs a url (its id) and a name")
    lines = tuple(recipe_line(str(t)) for t in parse_list_string(row.get("ingredient_lines")) if str(t).strip())
    nutrition = Nutrition(calories=_number(row.get("calories_per_serving")), protein_g=_number(row.get("protein_g")),
                          carbs_g=_number(row.get("carbs_g")), fat_g=_number(row.get("fat_g")),
                          sodium_mg=_number(row.get("sodium_mg")),
                          estimated=row.get("calories_estimated") is True,
                          plausible=row.get("nutrition_plausible", True) is not False)
    country = _text(row.get("origin_country"))
    return Recipe(recipe_id=url, title=title, source=_text(row.get("source")), url=url, lines=lines,
                  steps=_text(row.get("instructions")), servings=_number(row.get("servings")),
                  minutes=_number(row.get("minutes")), prep_minutes=_number(row.get("prep_minutes")),
                  cook_minutes=_number(row.get("cook_minutes")), nutrition=nutrition,
                  photo_url=_text(row.get("image_url")), dish_name=str(clean_title(title)["dish_name"]),
                  origin_country="" if country == "Unknown" else country,
                  origin_region=_text(row.get("origin_region")))


# ------------------------------------------------------------------ Ingredient
def ingredient_from_name(name: str, may_contain: Iterable[MayContain] = (),
                         specialty: pd.DataFrame | None = None) -> Ingredient:
    """An Ingredient with its risks computed now: the flags its name sets (verified), then what the may-contain
    table says a prepared food usually has (likely or possible, with its source). Flags only ever add cautions."""
    ingredient_id = ingredient_id_for(name) or _text(name).lower()
    if not ingredient_id:
        raise ValueError("an ingredient needs a name")
    risks = [Risk(flag, Confidence.VERIFIED, "the name says it", "flag rules") for flag in flags_for_term(ingredient_id)]
    aliases: list[str] = []
    for row in may_contain:
        if ingredient_id in row.names:
            aliases += [n for n in row.names if n != ingredient_id]
            risks += [Risk(flag, row.confidence, row.note, row.source) for flag in row.flags
                      if flag not in {r.flag for r in risks}]
    found = None
    if specialty is not None:
        for entry in specialty.to_dict("records"):
            if ingredient_id == entry["ingredient"] or ingredient_id in entry["aliases"]:
                aliases += [a for a in entry["aliases"] if a != ingredient_id]
                found = Specialty(entry["note"], tuple(entry["cuisines"]), tuple(entry["store_kinds"]),
                                  entry["source_url"], entry["licence"])
                break
    return Ingredient(ingredient_id, ingredient_id, tuple(dict.fromkeys(aliases)), tuple(risks), found)


# ------------------------------------------------------------------ Place
def place_from_row(row: Mapping[Any, Any] | pd.Series, verified: Iterable[Mapping] = ()) -> Place:
    """A Place from the map's table (notebook 03), with its diet claims and their evidence (places.py)."""
    place_id, lat, lng = _text(row.get("osm_id")), _number(row.get("lat")), _number(row.get("lng"))
    if not place_id or lat is None or lng is None:
        raise ValueError("a place needs an OpenStreetMap id and a location")
    series = row if isinstance(row, pd.Series) else pd.Series(dict(row))
    claims = tuple(Claim(e["tag"], e["level"], e["label"], e["reason"], e["source"])
                   for e in diet_evidence(series, verified))
    category = _text(row.get("category")) or "place"
    return Place(place_id=place_id, name=_text(row.get("name")) or f"Unnamed {category}", lat=lat, lng=lng,
                 category=category, cuisines=tuple(_cuisines(row)), claims=claims, address=_text(row.get("address")),
                 postcode=_text(row.get("postcode")), website=_text(row.get("website")), phone=_text(row.get("phone")),
                 hours=_text(row.get("opening_hours")))
