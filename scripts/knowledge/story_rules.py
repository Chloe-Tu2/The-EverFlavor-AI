"""The story rule (review item 34, decided by med27-coder, 2026-11-25, option A): besides the sentences from an
article's History, Origin, Culture and similar sections (story_candidates), a sentence of the dish's own Wikipedia
intro counts as story material when it states an origin, historical context, a traditional association, a date or
a cultural significance. Ingredient descriptions, preparation, serving suggestions, advertising language and
popularity claims never count. The fact check is not loosened and no new sections are read.

Shared by the counting scripts (country scores, coverage, impact, Walter) so they follow one rule. Nothing is
written into the knowledge: the sentence is read from the dish's `summary`, which the app already shows.
"""
from __future__ import annotations

import re

# what makes an intro sentence story material
STORY_SIGNAL = re.compile(
    r"\b(originat\w*|national dish|dates? (back|from)|first (made|recorded|mentioned|described|served)|"
    r"\d{1,2}(st|nd|rd|th) centur(y|ies)|centur(y|ies) ago|\b1\d{3}s?\b|\b20[0-2]\d\b|ancient|medieval|colonial|"
    r"introduced (by|to|in|into)|invented|named (after|for)|brought (by|to)|heritage|symbol\w*|"
    r"(eaten|served|prepared|made) (during|at|for) (the )?(festival|feast|celebration|holiday|wedding|ramadan|"
    r"christmas|easter|eid|new year)|traditional(ly)? \w+(?: \w+)? (from|of) (the )?[A-Z]\w+)")
# sentences that only describe, sell or rank a dish (rejected unless a strong signal is also there)
WEAK_ONLY = re.compile(r"\b(popular|famous|delicious|best|favou?rite|made (with|from|of)|consists of|served with|"
                       r"ingredients?|recipe|prepared by|cooked (in|with))\b", re.IGNORECASE)
STRONG = re.compile(r"\b(originat\w*|national dish|dates? (back|from)|first (made|recorded|mentioned)|centur(y|ies)|"
                    r"\b1\d{3}s?\b|introduced|invented|named (after|for)|heritage)\b", re.IGNORECASE)


def intro_story(d: dict) -> str:
    """The first sentence of the dish's intro that is story material by the rule, or ""."""
    for sentence in re.split(r"(?<=[.!?])\s+", d.get("summary") or ""):
        if STORY_SIGNAL.search(sentence) and (STRONG.search(sentence) or not WEAK_ONLY.search(sentence)):
            return sentence.strip()
    return ""


def has_story(d: dict) -> bool:
    """A dish has a story: a sentence from a story section, or an intro sentence by the rule."""
    return bool(d.get("story_candidates")) or bool(intro_story(d))
