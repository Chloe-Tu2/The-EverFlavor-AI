"""Foods a person doesn't eat: not allergies, just things they skip (picky eating, taste, habit).

They are kept apart from the allergy and diet checks (flags.py, safety.py) on purpose:

- an allergy is a safety check: it knows hidden sources (Worcestershire sauce has fish) and explains each warning;
- a skipped food is matched by its name only ("mushroom" also matches "mushrooms" and "button mushrooms"), so it
  narrows the results but is never a safety promise. Someone whose reason is an allergy should use the allergies.

    >>> drop_skipped(recipes, ["mushroom", "olive"])       # recipes that mention neither
"""
from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable

import pandas as pd

from .parsing import parse_list_string

__all__ = ["MAX_FOODS", "clean_names", "common_ingredients", "drop_skipped", "found_in", "pattern", "simplest"]

MAX_FOODS = 200          # a list longer than this is cut (each name is at most 40 characters)


def clean_names(names: Iterable[object]) -> tuple[str, ...]:
    """The names as lowercase words, without blanks, repeats or anything that is not a food name."""
    seen: dict[str, None] = {}
    for name in names:
        text = re.sub(r"[^\w' -]", " ", str(name)).strip().lower()
        text = re.sub(r"\s+", " ", text)[:40]
        if len(text) >= 2:
            seen.setdefault(text, None)
    return tuple(seen)[:MAX_FOODS]


def simplest(names: Iterable[object]) -> tuple[str, ...]:
    """The names without the ones another name already covers: with "mushroom" chosen, "mushroom soup" adds
    nothing (a name matches as a word, so "mushroom" finds it too)."""
    words = clean_names(names)
    return tuple(name for name in words
                 if not any(other != name and re.search(rf"\b{re.escape(other)}(?:e?s)?\b", name) for other in words))


def pattern(names: Iterable[object]) -> re.Pattern[str] | None:
    """One pattern that finds any of the names as whole words, singular or plural ("tomato", "tomatoes")."""
    words = clean_names(names)
    if not words:
        return None
    longest_first = sorted(words, key=len, reverse=True)
    return re.compile(r"\b(?:" + "|".join(re.escape(w) + r"(?:e?s)?" for w in longest_first) + r")\b",
                      re.IGNORECASE)


def found_in(text: object, names: Iterable[object]) -> list[str]:
    """Which of the names one text mentions (each once, as the user wrote it)."""
    found = pattern(names)
    if found is None or not isinstance(text, str):
        return []
    hits = {m.group(0).lower() for m in found.finditer(text)}
    return [name for name in clean_names(names)
            if any(hit == name or hit.rstrip("s").rstrip("e") == name.rstrip("s").rstrip("e") for hit in hits)]


def drop_skipped(df: pd.DataFrame, names: Iterable[object],
                 columns: tuple[str, ...] = ("ingredient_list", "recipe_name")) -> pd.DataFrame:
    """The recipes that mention none of the names in their ingredients or their name."""
    found = pattern(names)
    if found is None or df.empty:
        return df
    text = pd.Series("", index=df.index)
    for column in columns:
        if column in df:
            text = text + " " + df[column].astype(str)
    return df[~text.str.contains(found, na=False)]


# A last word that makes a different food: "olive oil" is not "olive", "soy sauce" is not "soy"
OWN_FOODS = {"oil", "sauce", "powder", "juice", "stock", "broth", "paste", "flour", "milk", "butter", "cheese",
             "vinegar", "cream", "extract", "seed", "seeds", "syrup", "zest", "leaves", "leaf", "water", "wine",
             "soup", "bread", "jam", "sugar", "salt", "meal", "starch", "liqueur", "noodles", "pasta", "rice"}


def common_ingredients(df: pd.DataFrame, top: int = 4000) -> list[str]:
    """The foods recipes use most, most common first (the choices for "Foods I don't eat").

    Variants fold into their food: "button mushroom" and "dried porcini mushroom" are covered by "mushroom" (a
    skipped name matches as a word), so only "mushroom" is offered. A name whose last word makes a different food
    ("olive oil", "soy sauce") stays its own choice.
    """
    counts: Counter[str] = Counter()
    if "ingredient_list" not in df:
        return []
    for value in df["ingredient_list"]:
        counts.update(clean_names(parse_list_string(value)))
    names = [name for name, _ in counts.most_common()]
    singles = set(names)
    kept: list[str] = []
    kept_phrases: set[str] = set()
    for name in sorted(names, key=lambda n: len(n.split())):   # shorter names first; stable keeps the counts' order
        words = name.split()
        variant = len(words) > 1 and words[-1] not in OWN_FOODS and any(
            w in singles or w.rstrip("s") in singles for w in words)
        # "condensed cream of mushroom soup" is covered by the kept, shorter "cream of mushroom soup"
        inside = any(" ".join(words[i:j]) in kept_phrases
                     for i in range(len(words)) for j in range(i + 2, len(words) + 1) if j - i < len(words))
        if not variant and not inside:
            kept.append(name)
            if len(words) > 1:
                kept_phrases.add(name)
    rank = {name: i for i, name in enumerate(names)}
    return sorted(kept, key=rank.__getitem__)[:top]
