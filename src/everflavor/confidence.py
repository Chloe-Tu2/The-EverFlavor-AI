"""How sure a finding is, kept apart from how serious it is: one contract for Check my recipe, the map and Walter.

Severity (restrictions.SEVERITIES) says what a match means for the person: unsafe, not their profile, worth a
look. Confidence says how sure we are that the thing is there at all:

| Confidence | Means | Example |
|---|---|---|
| verified | the recipe lists it | "1 tbsp mirin" for no alcohol |
| likely | a food that is usually made with it, with a source | "teriyaki sauce" (usually mirin, sake) |
| possible | a food that is only sometimes made with it, with a source | "tiramisu" (some recipes add liqueur) |
| unknown | a ready-made product whose contents the name does not show | "house sauce" |

Confidence comes from the words and the may-contain table (`data/reference/may_contain.csv`), never from a
guess. The two meet in `severity_for`, which reads both and the person's answer for the rule: confidence never
softens what the safety gate decided (an allergy match stays critical however it was found); it only says how
sure the match is, and it lets a likely or possible item add a caution the gate does not make. A recorded
policy, proposed by Claude for Team EverGlow's review, 2026-11-16.
"""
from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from functools import cache
from pathlib import Path

import pandas as pd

__all__ = ["CONFIDENCE", "MAY_CONTAIN_FILE", "Confidence", "MayContain", "ProfileResponse", "gate_confidence",
           "load_may_contain", "may_contain_in", "severity_for"]

MAY_CONTAIN_FILE = Path(__file__).resolve().parents[2] / "data" / "reference" / "may_contain.csv"


class Confidence(str, Enum):
    VERIFIED = "verified"
    LIKELY = "likely"
    POSSIBLE = "possible"
    UNKNOWN = "unknown"


# confidence -> (mark, heading), in the order the results show them
CONFIDENCE = {Confidence.VERIFIED: ("✗", "Listed in the recipe"),
              Confidence.LIKELY: ("◐", "Usually made with it"),
              Confidence.POSSIBLE: ("○", "Sometimes made with it"),
              Confidence.UNKNOWN: ("?", "Contents not shown: check the label")}


class ProfileResponse(str, Enum):
    """What the person asked us to do when a rule matches (alcohol levels and beyond). Allergies and medical
    screens are always STRICT: nobody gets "warn me" for a peanut allergy."""
    STRICT = "strict"   # strictly avoid
    AVOID = "avoid"     # avoid when possible
    WARN = "warn"       # tell me, nothing more
    IGNORE = "ignore"   # no restriction


ALWAYS_STRICT = frozenset({"allergies", "medical"})
_DOWN = {"critical": "major", "major": "moderate", "moderate": "moderate", "info": "info"}


def severity_for(base: str, confidence: Confidence, response: ProfileResponse = ProfileResponse.STRICT,
                 category: str = "", from_gate: bool = False) -> str | None:
    """The severity of one match: the rule's own level (`base`), how sure the match is, and the person's answer.

    - STRICT: verified and likely keep the rule's level; possible and unknown are a look (moderate), unless the
      safety gate itself matched it, which always keeps the rule's level.
    - AVOID: one step lighter (major -> moderate). WARN: good to know (info). IGNORE: no finding (None).
    - Allergies and medical screens are always STRICT, whatever `response` says.
    """
    if category in ALWAYS_STRICT:
        response = ProfileResponse.STRICT
    if response is ProfileResponse.IGNORE:
        return None
    if response is ProfileResponse.WARN:
        return "info"
    level = base if from_gate or confidence in (Confidence.VERIFIED, Confidence.LIKELY) else \
        ("info" if base == "info" else "moderate")
    return _DOWN[level] if response is ProfileResponse.AVOID else level


# ---------------------------------------------------------------- the may-contain table
@dataclass(frozen=True)
class MayContain:
    item: str                       # "teriyaki sauce"
    also_called: tuple[str, ...]    # other names on a recipe line
    contains: tuple[str, ...]       # what it is usually made with, as ingredient names the gate reads
    flags: tuple[str, ...]          # the flags those ingredients set (checked by the tests)
    confidence: Confidence          # likely or possible
    note: str                       # what the source says, in plain words
    source: str                     # where it says it (a URL)

    @property
    def names(self) -> tuple[str, ...]:
        return (self.item, *self.also_called)


def _split(value: object) -> tuple[str, ...]:
    return tuple(p.strip() for p in str(value or "").split(";") if p.strip())


@cache
def load_may_contain(path: str | Path = MAY_CONTAIN_FILE) -> tuple[MayContain, ...]:
    """Read and check the table: every row likely or possible, with what it contains, its flags and a source.

    Raises:
        ValueError: listing every problem, so a bad edit is caught by the tests.
    """
    from .flags import FLAG_RULES
    table = pd.read_csv(path, dtype=str, keep_default_na=False)
    rows, problems = [], []
    for r in table.to_dict("records"):
        item = r["item"].strip().lower()
        if r["confidence"] not in (Confidence.LIKELY.value, Confidence.POSSIBLE.value):
            problems.append(f"{item}: confidence must be likely or possible")
            continue
        flags = _split(r["flags"])
        if not flags or set(flags) - set(FLAG_RULES):
            problems.append(f"{item}: unknown flags {sorted(set(flags) - set(FLAG_RULES)) or 'none'}")
        if not r["source"].startswith("https://") or not _split(r["contains"]):
            problems.append(f"{item}: needs what it contains and a source URL")
        rows.append(MayContain(item, tuple(a.lower() for a in _split(r["also_called"])), _split(r["contains"]),
                               flags, Confidence(r["confidence"]), r["note"].strip(), r["source"].strip()))
    pairs = [(n, f) for row in rows for n in row.names for f in row.flags]
    if len(set(pairs)) != len(pairs):   # an item may have one row per flag (tiramisu: coffee likely, alcohol possible)
        problems.append("a name and flag are in two rows")
    if problems:
        raise ValueError("; ".join(problems))
    return tuple(rows)


@cache
def _pattern(name: str) -> re.Pattern[str]:
    return re.compile(r"(?<![\w-])" + re.escape(name) + r"(e?s)?(?![\w-])", re.IGNORECASE)


def may_contain_in(line: str, table: Iterable[MayContain] | None = None) -> list[MayContain]:
    """The table rows a recipe line names ("2 tbsp teriyaki sauce" -> the teriyaki sauce row), one per flag."""
    return [row for row in (load_may_contain() if table is None else table)
            if any(_pattern(name).search(line) for name in row.names)]


@cache
def _prepared_names() -> frozenset[str]:
    """Names the flags read as a prepared food or product made with something (not the thing itself)."""
    from .flags import COMPOUND_INGREDIENTS, FLAG_RULES, named_foods, product_names
    out = set(COMPOUND_INGREDIENTS)
    for flag in FLAG_RULES:
        out |= set(named_foods(flag)) | set(product_names(flag))
    return frozenset(n.lower() for n in out)


def gate_confidence(line: str, flag: str, matched: object,
                    table: Iterable[MayContain] | None = None) -> tuple[Confidence, str, str]:
    """How sure one of the safety gate's matches is, with the words that say why and a source (or "").

    The gate's decision stands either way; this only labels it: the dish name, a may-contain row for the same
    flag, or a prepared food the flags know (Worcestershire sauce, pesto) is likely or possible; an ingredient
    named outright is verified.
    """
    words = [str(w).lower() for w in (matched if isinstance(matched, list) else [matched]) if w]
    for row in may_contain_in(line, table):
        if flag in row.flags and set(row.names) & set(words):
            return row.confidence, row.note, row.source
    if line.startswith("(dish name)"):
        return Confidence.LIKELY, "the dish name says " + ", ".join(words), ""
    if words and all(w in _prepared_names() for w in words):
        return Confidence.LIKELY, ", ".join(words) + " is usually made with it", ""
    return Confidence.VERIFIED, "listed: " + ", ".join(words), ""
