"""A recipe's steps broken down for the dish page: for each step, the time written in it, whether it is on the heat,
the pan, pot or oven it uses, the cooking method and which of the recipe's ingredients go in.

Everything comes from the recipe's own words (no model): a step without a written time has no time, and the
total time still comes from the recipe or the estimate (cooking_time.py). The split shown on the dish page is
"on the heat" (the times written in steps that cook) and "the rest" (preparation, resting and waiting).
"""
from __future__ import annotations

import re
from collections.abc import Iterable

from .cooking import COOKING_METHODS, METHOD_PATTERNS, methods_from_instructions
from .cooking_time import parse_step_minutes

__all__ = ["VESSELS", "cookware", "methods_of", "split_minutes", "step_breakdown"]

# What a step cooks in or uses, first match wins (more specific names first)
VESSELS: list[tuple[str, str]] = [
    # The kitchens' own cookware first (Moroccan, Mexican, Chinese, Japanese, Mediterranean, Middle Eastern). Names
    # that are also dishes (a tagine) count only as a thing to cook in: "in the tagine", "tagine pot", "its lid"
    ("tagine", r"\b(?:in|into|to|from|of) (?:a|the|your) (?:clay |earthenware )?ta[gj]ine\b|ta[gj]ine (?:pot|dish|base|lid)"),
    ("couscoussier", r"couscoussier|couscous steamer|top of the steamer"),
    ("comal", r"\bcomal\b"), ("molcajete", r"molcajete"), ("tortilla press", r"tortilla press"),
    ("bamboo steamer", r"bamboo steamer"), ("rice cooker", r"rice cooker"),
    ("clay pot", r"clay pot|donabe|earthenware pot|sand pot"), ("sushi mat", r"sushi mat|bamboo mat|makisu"),
    ("paella pan", r"paella pan|paellera"), ("cezve", r"\bcezve\b|\bibrik\b|turkish coffee pot"),
    ("mortar and pestle", r"mortar|pestle"), ("tandoor", r"\btandoor\b"),
    ("slow cooker", r"slow[- ]?cooker|crock[- ]?pot"), ("pressure cooker", r"pressure[- ]?cooker|instant ?pot"),
    ("deep fryer", r"deep[- ]?fryer"), ("roasting pan", r"roasting pan|roasting tin"),
    ("baking dish", r"baking (?:dish|pan)|casserole|\d+ ?x ?\d+ (?:inch )?(?:pan|dish)|loaf pan|pie (?:plate|dish)"),
    ("baking sheet", r"baking sheet|cookie sheet|sheet pan|baking tray"),
    ("wok", r"\bwok\b"), ("griddle", r"griddle|plancha"), ("skillet", r"skillet|frying pan|fry pan|saut[eé] pan"),
    ("steamer", r"steamer basket|\bsteamer\b"), ("dutch oven", r"dutch oven"),
    ("saucepan", r"saucepan|sauce pan"), ("pot", r"\b(?:stock ?pot|soup pot|pot)\b"),
    ("grill", r"\bgrill\b|barbecue|\bbbq\b"), ("oven", r"\boven\b|\bbake\b|\broast\b"),
    ("microwave", r"microwave"), ("blender", r"blender|food processor"),
    ("stand mixer", r"stand mixer|electric mixer|hand mixer|\bmixer\b"),
    ("bowl", r"\bbowl\b"), ("pan", r"\bpan\b"),
]
_HEAT = re.compile(r"\b(?:bak\w*|roast\w*|boil\w*|simmer\w*|fr(?:y|ied|ies|ying)|saut\w*|grill\w*|broil\w*|"
                   r"steam\w*|cook\w*|heat\w*|brown\w*|sear\w*|toast\w*|melt\w*|poach\w*|braise\w*|microwav\w*)\b",
                   re.IGNORECASE)
_NO_HEAT = re.compile(r"\b(?:cool\w*|chill\w*|refrigerat\w*|let (?:it )?(?:stand|rest|sit)|marinat\w*|"
                      r"set aside|freez\w*|remove from (?:the )?heat|take off (?:the )?heat)\b", re.IGNORECASE)
# Words that name a dish, tool or ingredient, not a way of cooking ("baking dish", "baking soda")
_NOT_A_METHOD = re.compile(r"\bbaking (?:dish|pan|sheet|tray|soda|powder|paper|mix)\b"
                           r"|\b(?:cookie|cooking) (?:sheet|spray|oil)\b"
                           r"|\b(?:boiling|boiled) water\b|\broasted (?:red )?peppers?\b", re.IGNORECASE)
# The last word of an ingredient that says which part of a food, not what it is: "chicken breast half" is also
# found by "chicken". ("Chicken broth" is not: a step's "chicken" means the chicken.)
_PART_WORDS = {"breast", "breasts", "thigh", "thighs", "fillet", "fillets", "half", "halves", "leaves", "leaf",
               "clove", "cloves", "slices", "chunks", "pieces", "steak", "steaks", "wings", "drumsticks"}
_METHOD_NAMES = {"deep_fry": "deep-fry", "pan_fry": "pan-fry or sauté", "stir_fry": "stir-fry",
                 "bake_roast": "bake or roast", "grill_broil": "grill or broil", "boil_simmer": "boil or simmer",
                 "steam": "steam", "slow_cook": "slow cook", "pressure_cook": "pressure cook",
                 "microwave": "microwave", "smoke": "smoke", "no_cook": "no heat"}
if set(_METHOD_NAMES) != set(COOKING_METHODS):   # a real check, kept even when Python runs with -O
    raise RuntimeError("dish_steps._METHOD_NAMES must name every cooking method")


def _steps(instructions: object) -> list[str]:
    if not isinstance(instructions, str):
        return []
    steps = [re.sub(r"\s+([,.;:!?])", r"\1", s).strip(" -*") for s in re.split(r"\r?\n+", instructions)]
    return [s for s in steps if s and not re.fullmatch(r"(?i)step\s*\d+[.:)]?", s)]


def _keys(name: str) -> set[str]:
    """The words a step may use for an ingredient: its whole name and its last word, or the word before a part
    word ("boneless skinless chicken breast half" -> "chicken")."""
    words = name.split()
    keys = {name, words[-1]}
    for i in range(len(words) - 1, 0, -1):
        if words[i] not in _PART_WORDS:
            break
        keys.add(words[i - 1])
    return {k for k in keys if len(k) > 2 and k not in _PART_WORDS}


def _mentioned(step: str, ingredients: Iterable[object]) -> list[str]:
    """The recipe's ingredients a step names, by their whole name or their key words (see _keys)."""
    lower = step.lower()
    found = []
    for item in ingredients:
        name = str(item).lower().strip()
        if name and any(re.search(rf"\b{re.escape(k)}e?s?\b", lower) for k in _keys(name)):
            found.append(str(item))
    return found


def step_breakdown(instructions: object, ingredients: Iterable[object] | None = None) -> list[dict[str, object]]:
    """Each step of a recipe with what it does.

    Args:
        instructions: The recipe's steps (Food.com: one per line; TheMealDB: paragraphs).
        ingredients: The recipe's ingredient names, to say which go into each step.

    Returns:
        One dict per step: text, minutes (the largest time written in it, or None), on_heat (it cooks and does
        not only cool, rest or come off the heat), vessel (the pan, pot, oven... it names, or None), methods
        (readable names of the cooking methods it names) and ingredients (the recipe's ingredients it names).
    """
    items = list(ingredients) if ingredients is not None else []
    out: list[dict[str, object]] = []
    for step in _steps(instructions):
        minutes = parse_step_minutes(step)["dur_maxsum"] or None
        vessel = next((name for name, pattern in VESSELS if re.search(pattern, step, re.IGNORECASE)), None)
        plain = _NOT_A_METHOD.sub(" ", step)
        methods = [m for m in COOKING_METHODS if m != "no_cook" and re.search(METHOD_PATTERNS[m], plain.lower())]
        on_heat = bool(_HEAT.search(plain)) and not _NO_HEAT.search(plain)
        out.append({"text": step[0].upper() + step[1:], "minutes": minutes, "on_heat": on_heat, "vessel": vessel,
                    "methods": [_METHOD_NAMES[m] for m in methods], "ingredients": _mentioned(step, items)})
    return out


# Names a more specific one already covers: a recipe with a skillet does not also need "a pan"
_COVERED = {"pan": ("skillet", "saucepan", "wok", "paella pan", "roasting pan", "griddle", "baking dish",
                    "baking sheet", "comal"),
            "pot": ("dutch oven", "clay pot", "slow cooker", "pressure cooker", "rice cooker"),
            "steamer": ("bamboo steamer", "couscoussier"), "oven": ("tandoor",)}
_SMALL = {"bowl"}   # every kitchen has bowls: not listed as something to get out


def cookware(instructions: object) -> list[str]:
    """Everything a recipe cooks in or with, in the order its steps first name it ("tagine", "saucepan",
    "oven"), from the recipe's own words. A general name a more specific one covers is left out ("pan" next to
    "skillet"), and so are bowls."""
    found: dict[str, int] = {}
    text = " ".join(_steps(instructions))
    for name, pattern in VESSELS:
        hit = re.search(pattern, text, re.IGNORECASE)
        if hit and name not in _SMALL:
            found[name] = hit.start()
    for general, specific in _COVERED.items():
        if general in found and any(name in found for name in specific):
            del found[general]
    # "pan" inside "paella pan" or "frying pan" is the same pan
    return sorted(found, key=found.__getitem__)


def split_minutes(breakdown: list[dict[str, object]], total: float | None) -> dict[str, float | None]:
    """How a recipe's time divides: the minutes written in steps on the heat, and the rest of the total
    (preparation, resting, waiting). None where it cannot be said (no total, or no times written)."""
    heat = sum(float(str(s["minutes"])) for s in breakdown if s["on_heat"] and s["minutes"])
    rest = float(total) - heat if heat and total is not None and total >= heat else None
    return {"on_heat": heat or None, "rest": rest, "total": total}


def methods_of(instructions: object) -> list[str]:
    """The recipe's cooking methods, readable (from cooking.methods_from_instructions)."""
    return [_METHOD_NAMES[m] for m in methods_from_instructions(instructions)]
