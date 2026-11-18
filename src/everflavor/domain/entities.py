"""The five entities of roadmap phase 1: Dish, Recipe, Ingredient, Place (and Walter, who reads them).

Each fact has one owner: a dish's origin and story are the Dish's, amounts and steps are the Recipe's, allergy risks
are the Ingredient's, diet claims are the Place's. Entities link to each other by id, never by copying data. They
are frozen dataclasses (plain Python, the same in Colab, VS Code and Antigravity); the loaders in `loaders.py`
build them from today's tables and check them there.

Safety is computed, never stored as truth: an Ingredient's `risks` come from the flag rules and the may-contain
table each time it is built, and a Recipe carries no flags of its own (the safety engine reads its lines).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..confidence import Confidence


@dataclass(frozen=True)
class Source:
    """Where a fact comes from, with its licence (Wikipedia text needs the credit; Wikidata is CC0)."""
    name: str
    url: str = ""
    licence: str = ""
    credit: str = ""


@dataclass(frozen=True)
class Fact:
    """One sourced sentence Walter may say (from the knowledge notebook; never invented)."""
    text: str
    topic: str      # about, origin, history, culture, inspiration
    source: str     # "Wikipedia: Taco", "Wikidata"


@dataclass(frozen=True)
class Link:
    """A reading link for "learn more": quick, more or deep."""
    level: str
    title: str
    url: str


@dataclass(frozen=True)
class Pronunciation:
    """How to say a dish's name (data/reference/dish_pronunciation.csv), with a native speaker's recording if any."""
    lang: str
    native_name: str
    respelling: str
    audio_file: str = ""
    audio_license: str = ""
    audio_author: str = ""
    note: str = ""


@dataclass(frozen=True)
class Dish:
    """What a dish *is*, whoever cooks it. No amounts, steps or nutrition: those are a Recipe's."""
    dish_id: str                        # the Wikidata QID ("Q191655"), else "<country>-<name>" (never changes)
    name: str
    kind: str                           # "dish" or "food or drink"
    country: str = ""
    region: str = ""
    regions: tuple[str, ...] = ()
    summary: str = ""
    facts: tuple[Fact, ...] = ()        # the best first (fun facts), then the rest
    origin: tuple[str, ...] = ()        # Wikidata's country of origin
    made_from: tuple[str, ...] = ()     # usual ingredients, as ingredient ids
    not_to_confuse: tuple[str, ...] = ()
    learn_more: tuple[Link, ...] = ()
    sources: tuple[Source, ...] = ()
    reviewed: bool = False
    pronunciation: Pronunciation | None = None


@dataclass(frozen=True)
class RecipeLine:
    """One ingredient line as written, with what the parser read from it (amount and unit may be unknown)."""
    text: str
    amount: float | None
    unit: str | None
    ingredient_id: str                  # "" when no food name was found on the line


@dataclass(frozen=True)
class Nutrition:
    """Per serving, as the recipe's source gives it (Edamam) or as estimated (marked)."""
    calories: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    sodium_mg: float | None = None
    estimated: bool = False
    plausible: bool = True


@dataclass(frozen=True)
class Recipe:
    """One written way to cook a dish. Origin and cuisine are the Dish's (through `dish_id`); a recipe with no
    known dish keeps its own `origin_country` and `origin_region` until its dish is known. No allergy flags here:
    the safety engine computes them from the lines."""
    recipe_id: str                      # the recipe's URL (unique in our tables)
    title: str                          # as posted
    source: str
    url: str
    lines: tuple[RecipeLine, ...] = ()
    steps: str = ""
    servings: float | None = None
    minutes: float | None = None
    prep_minutes: float | None = None
    cook_minutes: float | None = None
    nutrition: Nutrition = field(default_factory=Nutrition)
    photo_url: str = ""
    dish_id: str = ""                   # empty when the dish is not known
    dish_name: str = ""                 # the clean dish name from the title ("Lasagna")
    origin_country: str = ""
    origin_region: str = ""

    @property
    def ingredient_ids(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(line.ingredient_id for line in self.lines if line.ingredient_id))


@dataclass(frozen=True)
class Risk:
    """A flag an ingredient sets, how sure that is, and why."""
    flag: str                           # contains_gluten, contains_alcohol...
    confidence: Confidence              # verified (the name says it) or likely / possible (may-contain)
    reason: str = ""
    source: str = ""


@dataclass(frozen=True)
class Specialty:
    """Where a specialty ingredient comes from and where to buy it (data/reference/specialty_ingredients.csv)."""
    note: str
    cuisines: tuple[str, ...] = ()
    store_kinds: tuple[str, ...] = ()
    source_url: str = ""
    licence: str = ""


@dataclass(frozen=True)
class Ingredient:
    """A food, the same everywhere it appears. Until the merge review is signed off, the id is the normalized
    name (one name, one id); merged names will later share one id."""
    ingredient_id: str
    name: str
    aliases: tuple[str, ...] = ()
    risks: tuple[Risk, ...] = ()
    specialty: Specialty | None = None

    @property
    def flags(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(r.flag for r in self.risks))


@dataclass(frozen=True)
class Claim:
    """A diet claim about a place (halal, kosher, vegan, vegetarian), with how sure it is and why."""
    tag: str
    level: str                          # verified or likely
    label: str
    reason: str
    source: str


@dataclass(frozen=True)
class Place:
    """Somewhere to eat or buy food (OpenStreetMap, ODbL: credit "OpenStreetMap contributors")."""
    place_id: str                       # the OpenStreetMap id ("node/123")
    name: str
    lat: float
    lng: float
    category: str                       # grocery, restaurant, butcher...
    cuisines: tuple[str, ...] = ()
    claims: tuple[Claim, ...] = ()
    address: str = ""
    postcode: str = ""
    website: str = ""
    phone: str = ""
    hours: str = ""
    source: str = "OpenStreetMap contributors (ODbL)"
