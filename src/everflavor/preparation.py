"""How a dish is made, as a risk of its own: raw or undercooked, fermented, and foods the steps bring in.

The ingredient check reads what is in a dish; some restrictions are about how it is made. Sushi is a problem in
pregnancy because the fish is raw, not because it is fish; beer-battered fish brings alcohol in through the
batter. This module reads the steps (and the dish name and lines, for "tartare" or "medium-rare steak") for:

- `undercooked`: raw or undercooked animal food named outright (medium-rare, runny yolk, ceviche, tartare...);
- `fermented`: fermenting, named outright;
- foods the steps mention that the ingredient lines don't (`step_sentences` feeds them to the same safety gate).

Cooking methods (fried, grilled, smoked, no heat) stay in cooking.py. The word lists only name what the text
says; they never guess. A recorded policy, proposed by Claude for Team EverGlow's review, 2026-11-16.
"""
from __future__ import annotations

import re

__all__ = ["PREP_RISKS", "prep_risks", "step_sentences"]

# risk -> (what it means, the words that show it)
PREP_RISKS: dict[str, tuple[str, str]] = {
    "undercooked": ("raw or undercooked", (r"\b(medium[- ]rare|rare (?:steak|beef|tuna|lamb|duck)|cooked rare|"
                                          r"runny yolks?|soft[- ]boiled|sunny[- ]side[- ]up|over[- ]easy|"
                                          r"raw (?:eggs?|egg yolks?|fish|salmon|tuna|beef|meat|oysters?|shellfish)|"
                                          r"serve(?:d)? raw|eat(?:en)? raw|sushi|sashimi|sushi[- ]grade|tartare|"
                                          r"carpaccio|ceviche|poke bowl|steak tartare|kibbeh nayeh|"
                                          r"pink in the (?:middle|centre|center))\b")),
    "fermented": ("fermented", r"\b(ferment(?:ed|ing|s|ation)?|lacto[- ]fermented)\b"),
}
_PATTERNS = {risk: re.compile(words, re.IGNORECASE) for risk, (_, words) in PREP_RISKS.items()}
# words that undo a match: "not raw", "until no longer pink", "fully cooked", "cooked sushi rice"
_NOT = re.compile(r"\b(not|no longer|never|until (?:the )?(?:eggs? (?:are|is) )?(?:set|firm|cooked through)|"
                  r"fully cooked|cooked through|vegetarian|vegan|veggie|cucumber|avocado|sushi rice)\b", re.IGNORECASE)


def prep_risks(text: object) -> dict[str, list[str]]:
    """The preparation risks a text names, with the words that show each: {"undercooked": ["medium-rare"]}.

    A sentence that also says the food is not raw ("cook until no longer pink", "vegetarian sushi") is left out.
    """
    if not isinstance(text, str) or not text.strip():
        return {}
    found: dict[str, list[str]] = {}
    for sentence in re.split(r"(?<=[.!?;\n])\s*", text):
        if _NOT.search(sentence):
            continue
        for risk, pattern in _PATTERNS.items():
            for match in pattern.finditer(sentence):
                found.setdefault(risk, [])
                if match.group(0).lower() not in found[risk]:
                    found[risk].append(match.group(0).lower())
    return found


def step_sentences(text: object, limit: int = 80) -> list[str]:
    """The steps as short sentences, each marked "(steps)", for the safety gate to read like ingredient lines."""
    if not isinstance(text, str):
        return []
    out = []
    for sentence in re.split(r"(?<=[.!?;\n])\s*", text):
        sentence = sentence.strip()
        if len(sentence) > 3:
            out.append("(steps) " + (sentence if len(sentence) <= limit else sentence[:limit - 1] + "…"))
    return out
