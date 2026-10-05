"""Safety gate for recipes the agents write (roadmap steps 2 and 4).

`UserProfile` holds one person's restrictions in one place (the proposal keeps them in a
structured profile, not only in the chat). `check_recipe` checks free-text ingredient lines
and the dish name against it, with the same keyword rules (flags.py) and diet rules
(diets.py) as the dataset and `recommend.passes_safety_filter`, and says which line broke
which rule, so the Chef Agent can rewrite the recipe instead of only being told "no".
The gate runs outside the language model and its answer cannot be overridden.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field

from .diets import DIET_PROFILES
from .flags import FLAG_RULES, explain_flag, keyword_flag, name_text

__all__ = [
    "UserProfile",
    "check_recipe",
]

_DIET_FLAGS = {"vegetarian", "vegan"}


@dataclass(frozen=True)
class UserProfile:
    """One person's restrictions and preferences, as the agents and the front end pass them.

    Attributes:
        avoid: Flag columns that must be False ("contains_peanut", "contains_pork" ...).
        diets: Diet profiles to follow (DIET_PROFILES keys: "halal_friendly" ...).
        vegetarian: No meat, poultry, fish or shellfish.
        vegan: No animal products.
        calories_per_meal: The calorie budget for one serving, or None.
        cuisines: Preferred cuisine families ("Asian" ...); empty means any.
        area: Where to look for stores ("Houston, TX"); empty means not asked.
    """

    avoid: tuple[str, ...] = ()
    diets: tuple[str, ...] = ()
    vegetarian: bool = False
    vegan: bool = False
    calories_per_meal: float | None = None
    cuisines: tuple[str, ...] = ()
    area: str = ""
    extra: Mapping[str, object] = field(default_factory=dict)   # front-end fields the back end ignores

    def __post_init__(self) -> None:
        unknown_flags = [f for f in self.avoid if f not in FLAG_RULES]
        unknown_diets = [d for d in self.diets if d not in DIET_PROFILES]
        if unknown_flags or unknown_diets:
            raise ValueError(f"unknown restriction(s): {unknown_flags + unknown_diets}; flags are FLAG_RULES "
                             f"keys, diets are DIET_PROFILES keys")
        if self.calories_per_meal is not None and not self.calories_per_meal > 0:
            raise ValueError(f"calories_per_meal must be positive, got {self.calories_per_meal!r}")

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> UserProfile:
        """Build a profile from JSON-like data (lists become tuples; unknown keys go to `extra`)."""
        known = {"avoid", "diets", "vegetarian", "vegan", "calories_per_meal", "cuisines", "area"}
        values: dict[str, object] = {k: tuple(v) if isinstance(v, list) else v for k, v in data.items() if k in known}
        return cls(**values, extra={k: v for k, v in data.items() if k not in known})  # type: ignore[arg-type]

    def to_dict(self) -> dict:
        """The profile as JSON-ready data (tuples become lists; `extra` fields back at the top level)."""
        data = {k: list(v) if isinstance(v, tuple) else v for k, v in asdict(self).items() if k != "extra"}
        return {**data, **self.extra}


def _problems(texts: Sequence[tuple[str, str]], column: str, rule: str) -> list[dict]:
    """One problem per text where `column` rules the recipe out ("vegetarian" / "vegan": when it does not fit)."""
    found = []
    for label, text in texts:
        bad = not keyword_flag(text, column) if column in _DIET_FLAGS else keyword_flag(text, column)
        if bad:
            found.append({"line": label, "rule": rule, "flag": column, "matched": explain_flag(text, column)})
    return found


def check_recipe(ingredient_lines: Sequence[object], recipe_name: object, profile: UserProfile) -> dict:
    """Check one recipe, as written, against a user profile.

    Args:
        ingredient_lines: The recipe's ingredient lines ("2 slices bacon, chopped").
        recipe_name: The dish name (names count too: "Bacon Pasta" fails "no pork").
        profile: The user's restrictions.

    Returns:
        {"passed": True only when nothing breaks a rule, "problems": one entry per broken rule
        and line, {"line", "rule" (the flag, diet or "vegetarian" / "vegan" the user asked for),
        "flag" (the flag that fired), "matched" (the words that set it)}, "checked": the rules
        checked}. Pet meat is always checked (policy P24), whatever the profile says.
    """
    texts = [(str(line), str(line).lower()) for line in ingredient_lines if line is not None and str(line).strip()]
    name = name_text(recipe_name)
    if name.strip():
        texts.append((f"(dish name) {recipe_name}", name))
    problems = _problems(texts, "contains_pet_meat", "never served (P24)")
    for flag in profile.avoid:
        problems += _problems(texts, flag, flag)
    if profile.vegetarian:
        problems += _problems(texts, "vegetarian", "vegetarian")
    if profile.vegan:
        problems += _problems(texts, "vegan", "vegan")
    for diet in profile.diets:
        rule = DIET_PROFILES[diet]
        for column in rule.get("require", []):
            problems += _problems(texts, column, diet)
        for column in rule.get("without", []):
            problems += _problems(texts, column, diet)
        for first, second in rule.get("not_together", []):
            a, b = _problems(texts, first, diet), _problems(texts, second, diet)
            if a and b:   # kosher: meat and dairy in the same dish
                problems += a + b
    return {"passed": not problems, "problems": problems,
            "checked": ["contains_pet_meat", *profile.avoid, *(["vegetarian"] if profile.vegetarian else []),
                        *(["vegan"] if profile.vegan else []), *profile.diets]}
