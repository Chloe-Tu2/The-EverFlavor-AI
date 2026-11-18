"""One interface to the entities, for the app, the safety engine's callers and Walter.

Walter owns no food facts: he reads a Dish, its Ingredients and nearby Places through this graph, and his safety
words only explain the engine's `RecipeAnalysis`. Dishes are matched to recipes the way the app does it today
(`waiter.Knowledge.find` on the clean dish name), so nothing changes for the person using the app.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path

import pandas as pd

from ..confidence import MayContain, load_may_contain
from ..places import load_place_evidence, load_specialty_ingredients
from ..waiter import Knowledge
from .entities import Dish, Ingredient, Place, Recipe
from .loaders import (
    dish_from_record,
    ingredient_from_name,
    load_pronunciations,
    place_from_row,
)

ROOT = Path(__file__).resolve().parents[3]


@dataclass
class KnowledgeGraph:
    """Dishes by id, the name index that finds a recipe's dish, and Ingredients and Places built on demand."""
    dishes: dict[str, Dish]
    knowledge: Knowledge | None = None
    may_contain: tuple[MayContain, ...] = ()
    specialty: pd.DataFrame | None = None
    places: dict[str, Place] = field(default_factory=dict)
    _ingredients: dict[str, Ingredient] = field(default_factory=dict, repr=False)

    @classmethod
    def load(cls, root: str | Path = ROOT, places: pd.DataFrame | None = None) -> KnowledgeGraph:
        """Read the knowledge notebook, the pronunciation, may-contain and specialty tables, and the places given
        (the map's table, already loaded by the caller; none by default)."""
        root = Path(root)
        notebook = root / "data" / "knowledge" / "dishes.jsonl"
        knowledge = Knowledge.load(notebook) if notebook.exists() else None
        spoken = load_pronunciations(root / "data" / "reference" / "dish_pronunciation.csv")
        dishes: dict[str, Dish] = {}
        for record in knowledge.dishes if knowledge else []:
            dish = dish_from_record(record, spoken)
            dishes.setdefault(dish.dish_id, dish)
        evidence = load_place_evidence(root / "data" / "reference" / "place_evidence.csv")
        found = {}
        for row in places.to_dict("records") if places is not None else []:
            place = place_from_row(row, evidence.get(str(row.get("osm_id")), []))
            found[place.place_id] = place
        return cls(dishes, knowledge, load_may_contain(root / "data" / "reference" / "may_contain.csv"),
                   load_specialty_ingredients(root / "data" / "reference" / "specialty_ingredients.csv"), found)

    def get_dish(self, dish_id: str) -> Dish | None:
        return self.dishes.get(dish_id)

    def find_dish(self, name: str, country: str | None = None) -> Dish | None:
        """The dish a name is about ("easy beef tacos" -> Taco), as the app finds it; None if unknown."""
        if not self.knowledge or not name:
            return None
        entry = self.knowledge.find(name, country or None)
        return self.dishes.get(str(entry.get("qid"))) if entry else None

    def link_dish(self, recipe: Recipe) -> Recipe:
        """The recipe with its `dish_id` set when its dish is known (else unchanged, `dish_id` empty)."""
        dish = self.find_dish(recipe.dish_name or recipe.title, recipe.origin_country)
        return replace(recipe, dish_id=dish.dish_id) if dish else recipe

    def dish_of(self, recipe: Recipe) -> Dish | None:
        return self.get_dish(recipe.dish_id) if recipe.dish_id else self.find_dish(recipe.dish_name or recipe.title,
                                                                                  recipe.origin_country)

    def where_from(self, recipe: Recipe) -> tuple[str, str]:
        """(country, region): Wikidata's country of origin of the recipe's dish when it has one, else the recipe's
        own, else the country of the cuisine list the dish was found in (the notebook's `country`, which is where
        the dish is eaten, not always where it began: Scone is on a Canadian list)."""
        dish = self.dish_of(recipe)
        if dish and dish.origin:
            same = dish.origin[0] == dish.country
            return dish.origin[0], dish.region if same else ""
        if recipe.origin_country:
            return recipe.origin_country, recipe.origin_region
        return (dish.country, dish.region) if dish else ("", "")

    def ingredient(self, name: str) -> Ingredient:
        """One Ingredient, with its risks computed now (and kept for this graph's life)."""
        made = ingredient_from_name(name, self.may_contain, self.specialty)
        return self._ingredients.setdefault(made.ingredient_id, made)

    def ingredients_of(self, recipe: Recipe) -> list[Ingredient]:
        return [self.ingredient(i) for i in recipe.ingredient_ids]

    def get_place(self, place_id: str) -> Place | None:
        return self.places.get(place_id)
