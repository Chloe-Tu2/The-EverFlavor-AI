"""Check my recipe, the back end: read anything pasted, find its ingredient lines, and give one of three levels.

- `extract_ingredients` takes what people paste (an ingredient list, or a whole recipe from a website, a family
  card or a chat, with headings, bullets, numbers and steps) and keeps the ingredient lines, saying what it left
  out. It reads only what is written; it never adds an ingredient.
- `review` turns the safety gate's report (safety.check_recipe, through llm.check_and_explain) into a level:

  - **conflict**: a rule of the profile is broken (the gate's own problems);
  - **review**: nothing broke a rule, but a line is a ready-made product (a sauce, a mix, a paste, a stock...)
    whose contents the name does not show, and the profile has something to watch for: "check its label";
  - **clear**: no conflict found in the ingredient names (never "safe": the check reads names, not labels).

The level is decided here, from the rules; Walter and the local AI only explain it.
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

__all__ = ["OPAQUE_WORDS", "extract_ingredients", "review"]

# Headings that open and close the ingredient part of a pasted recipe
_INGREDIENTS_HEADING = re.compile(r"^\W*(ingredients?|you('ll| will) need|what you need)\b[^a-z]*$", re.IGNORECASE)
_OTHER_HEADING = re.compile(r"^\W*(instructions?|directions?|method|steps?|preparation|how to make( it)?|notes?|"
                            r"nutrition( facts)?|equipment|serves|servings?|yield|prep time|cook time|total time)"
                            r"\b.*$", re.IGNORECASE)
# A sub-heading inside the ingredients ("For the sauce:", "Marinade"): kept as a label, not checked
_SUB_HEADING = re.compile(r"^\W*(for the\b.*|[a-z ]{2,30}):\s*$", re.IGNORECASE)
_BULLET = re.compile(r"^\s*(?:[-*•·▢☐□✓✔◦‣>]+|\(?\d{1,2}[.)]|step \d+[:.)]?)\s+", re.IGNORECASE)
# A step reads like a sentence that tells you to do something
_STEP_VERBS = re.compile(r"^(add|bake|bring|combine|cook|cover|cut|drain|fold|fry|garnish|grill|heat|let|mix|"
                         r"place|pour|preheat|put|reduce|remove|roast|saute|sauté|season|serve|simmer|sprinkle|"
                         r"stir|transfer|whisk|in a|once|when|meanwhile|then)\b", re.IGNORECASE)
# Ready-made products whose name does not show what is in them (a recorded policy, proposed by Claude for Team
# EverGlow's review, 2026-11-16): a line with one of these words and no rule fired is "check its label"
OPAQUE_WORDS = ("sauce", "mix", "paste", "seasoning", "dressing", "marinade", "stock cube", "bouillon", "broth",
                "stock", "spice blend", "spice rub", "rub", "glaze", "gravy", "ketchup", "relish", "chutney",
                "curry powder", "store-bought", "store bought", "ready-made", "premade", "pre-made", "instant",
                "packet", "canned soup", "cream of")
_OPAQUE = re.compile(r"\b(" + "|".join(re.escape(w) for w in OPAQUE_WORDS) + r")s?\b", re.IGNORECASE)


def extract_ingredients(text: str) -> dict[str, Any]:
    """The ingredient lines in anything pasted.

    Returns:
        {"ingredients": the lines to check (bullets and numbering removed), "ignored": lines left out (steps,
        headings, notes), "sections": sub-headings seen ("For the sauce"), "mode": "recipe" when an Ingredients
        heading was found, else "list"}.
    """
    lines = [line.rstrip() for line in str(text or "").splitlines()]
    has_heading = any(_INGREDIENTS_HEADING.match(line.strip()) for line in lines)
    inside = not has_heading
    ingredients: list[str] = []
    ignored: list[str] = []
    sections: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if _INGREDIENTS_HEADING.match(line):
            inside = True
            continue
        if _OTHER_HEADING.match(line) and len(line.split()) <= 6:
            inside = False
            ignored.append(line)
            continue
        if not inside:
            ignored.append(line)
            continue
        if _SUB_HEADING.match(line) and not re.search(r"\d", line):
            sections.append(line.strip(" :").strip())
            continue
        item = _BULLET.sub("", line).strip()
        if _looks_like_step(item):
            ignored.append(line)
            continue
        if item:
            ingredients.append(item)
    return {"ingredients": ingredients, "ignored": ignored, "sections": sections,
            "mode": "recipe" if has_heading else "list"}


def _looks_like_step(line: str) -> bool:
    """A cooking step, not an ingredient: it starts with a cooking verb and reads like a sentence, or it is long."""
    words = line.split()
    if len(words) >= 14:
        return True
    return bool(_STEP_VERBS.match(line)) and len(words) >= 4 and not re.match(r"^\d", line)


def review(report: Mapping[str, object], ingredients: Iterable[str], watching: bool) -> dict[str, Any]:
    """The level for a checked recipe, with what needs a look.

    Args:
        report: The safety gate's report (passed, problems, checked).
        ingredients: The lines that were checked.
        watching: True when the profile avoids or follows something (allergies, diets); without that, a sauce has
            nothing to hide from the user and is not flagged.

    Returns:
        {"level": "conflict" | "review" | "clear", "to_check": [{"line", "word"}] (ready-made products no rule
        caught), "conflict_lines": the lines with a problem}.
    """
    problems: list[Any] = list(report.get("problems") or [])   # type: ignore[call-overload]
    conflict_lines = {str(p["line"]) for p in problems}
    to_check = []
    if watching:
        for line in ingredients:
            found = _OPAQUE.search(line)
            if found and line not in conflict_lines:
                to_check.append({"line": line, "word": found.group(1).lower()})
    level = "conflict" if problems else "review" if to_check else "clear"
    return {"level": level, "to_check": to_check, "conflict_lines": sorted(conflict_lines)}
