"""The waiter's dish knowledge: tidy the collected facts and write the readable knowledge notebook.

The facts come from `scripts/knowledge/fetch_knowledge.py` (Wikipedia lists and intros, Wikidata), one dish per
line in `data/knowledge/dishes.jsonl`. Nothing here invents a fact: the rules only shorten, clean and rank the
sentences the sources wrote, and every dish keeps its sources (Wikipedia text is CC BY-SA 4.0: credit and link).
"""
from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path

# Translations and romanisations in brackets: "(Swedish: Britatarta)", "(Chinese: ...)", "(lit. 'black beans')"
_LANGUAGE_BRACKET = re.compile(r"\s*\((?:[A-Z][a-z]+(?:[ -][A-Za-z]+)?:|lit\.|literally|pronounced|IPA)[^()]*\)")
# Brackets that hold another script (Chinese, Arabic, Greek ...): a name the reader cannot use
_SCRIPT_BRACKET = re.compile(r"\s*\([^()]*[^\x00-ɏ‐-‧][^()]*\)")
_SPACES = re.compile(r"\s+")

# What makes a fact worth telling first (stories, origins, records), and what makes it dull (company news)
_STRONG = re.compile(r"\b(legend|named after|named for|invent|originat|believed|story|UNESCO|emperor|king|queen|"
                     r"dynasty|[0-9]{1,2}(st|nd|rd|th) century|1[0-9]{3}|first|national dish|festival|record)",
                     re.IGNORECASE)
_DULL = re.compile(r"\b(announced|company|subsidiary|trademark|brand|closed|acquired|marketed|stock|sales of|"
                   r"headquarter|is produced by|manufactur)", re.IGNORECASE)
_PRONOUN_START = re.compile(r"^(It|The dish)\b(?=\s+(is|was|has|had|can|became|originated|remains|comes))")

# "It is unknown where ...", "It is thought that ...": a placeholder "it", not the dish
_PLACEHOLDER_IT = re.compile(r"^It (is|was) (not )?(unknown|unclear|uncertain|thought|believed|said|claimed|likely|"
                             r"possible|probable|common|customary|known that|reported|estimated|often|generally|"
                             r"widely|commonly|traditional to|usual)\b")


def clean_fact(text: str, name: str) -> str:
    """One source sentence made easy to read on its own: brackets of translations and other scripts removed,
    a leading "It is ..." given the dish's name. The words of the source stay as written."""
    text = _LANGUAGE_BRACKET.sub("", text)
    text = _SCRIPT_BRACKET.sub("", text)
    text = _SPACES.sub(" ", text).strip()
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    if _PLACEHOLDER_IT.match(text):
        return text
    return _PRONOUN_START.sub(name, text, count=1)


def fact_score(text: str) -> int:
    """Higher for stories and origins, lower for company news; used to order the facts."""
    return 2 * len(_STRONG.findall(text)) - 3 * len(_DULL.findall(text))


# What a fact is about, so the waiter can answer "what inspired it?" or "where is it from?" and mix topics
TOPICS = {
    "inspiration": re.compile(r"\b(inspired|named after|named for|in hono[u]?r of|invented by|created by|"
                              r"based on|adapted from|dedicated to|legend|story|myth)", re.IGNORECASE),
    "origin": re.compile(r"\b(originat|comes from|native to|first (made|served|appeared|created|cooked)|"
                         r"introduced|brought (to|by)|immigrants|birthplace)", re.IGNORECASE),
    "culture": re.compile(r"\b(festival|tradition|celebrat|ritual|holiday|wedding|symbol|national dish|UNESCO|"
                          r"street food|religio|ceremon)", re.IGNORECASE),
    "history": re.compile(r"\b([0-9]{1,2}(st|nd|rd|th) century|1[0-9]{3}|dynasty|empire|war|colonial|ancient|"
                          r"medieval)", re.IGNORECASE),
}


def fact_topic(text: str) -> str:
    """The first topic whose words the fact has (inspiration, origin, culture, history), else "about"."""
    return next((topic for topic, words in TOPICS.items() if words.search(text)), "about")


def wikidata_lines(dish: dict, name: str) -> list[str]:
    """Short lines made from the dish's Wikidata facts (CC0); they only restate the recorded values."""
    lines = []
    if dish.get("named_after"):
        lines.append(f"{name} is named after {', '.join(dish['named_after'])}.")
    if dish.get("origin"):
        lines.append(f"{name} comes from {', '.join(dish['origin'])}.")
    if dish.get("inception"):
        lines.append(f"{name} dates from {dish['inception'][0]}.")
    if dish.get("heritage"):
        lines.append(f"{name} is listed as {', '.join(dish['heritage'])}.")
    if dish.get("inventor"):
        lines.append(f"{name} was first made by {', '.join(dish['inventor'])}.")
    if dish.get("created_in"):
        lines.append(f"{name} was first made in {', '.join(dish['created_in'])}.")
    if dish.get("based_on"):
        lines.append(f"{name} is based on {', '.join(dish['based_on'])}.")
    if dish.get("not_to_confuse"):
        lines.append(f"Not to be confused with {', '.join(dish['not_to_confuse'])}.")
    return lines


def tidy_dish(dish: dict, keep: int = 3) -> dict:
    """The dish with its facts tidied and sorted by topic:
    - `fun_facts`: the best `keep`, from different topics where it can (an inspiration, an origin, a story);
    - `more_fun_facts`: the rest, for a user who asks for more (before the "learn more" links).
    Each fact is {"text", "topic", "source"}; dull ones (company news) are dropped."""
    name = dish["name"].split(" (")[0]
    article = next((src["name"] for src in dish.get("sources", []) if src["name"].startswith("Wikipedia:")),
                   "Wikipedia")
    texts = [clean_fact(c, name) for c in dish.get("fun_fact_candidates", []) + dish.get("story_candidates", [])]
    facts = [{"text": t, "topic": fact_topic(t), "source": article}
             for t in dict.fromkeys(texts) if fact_score(t) >= 0]
    facts += [{"text": t, "topic": fact_topic(t), "source": "Wikidata"} for t in wikidata_lines(dish, name)]
    facts.sort(key=lambda f: fact_score(f["text"]), reverse=True)
    best: list[dict] = []
    for f in facts:   # one per topic first, then the next best
        if len(best) < keep and f["topic"] not in {b["topic"] for b in best}:
            best.append(f)
    best += [f for f in facts if f not in best][:keep - len(best)]
    summary = clean_fact(dish.get("summary", ""), name)
    return {**dish, "summary": summary, "fun_facts": best, "more_fun_facts": [f for f in facts if f not in best],
            "review": "auto-cleaned" if dish.get("reviewed") is False else dish.get("review", "reviewed")}


def load_dishes(path: str | Path) -> list[dict]:
    with Path(path).open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def dish_card(dish: dict) -> str:
    """One dish as a Markdown section of the knowledge notebook (the spec's sections, sources last)."""
    lines = [f"### {dish['name']}", ""]
    where = ", ".join(x for x in [dish.get("region"), dish.get("country")] if x)
    facts = []
    if where:
        facts.append(f"From: {where}")
    if dish.get("origin"):
        facts.append(f"Origin (Wikidata): {', '.join(dish['origin'])}")
    if dish.get("inception"):
        facts.append(f"Since: {', '.join(dish['inception'])}")
    if dish.get("named_after"):
        facts.append(f"Named after: {', '.join(dish['named_after'])}")
    if dish.get("heritage"):
        facts.append(f"Heritage: {', '.join(dish['heritage'])}")
    ingredients = dish.get("made_from", []) + [p for p in dish.get("parts", []) if p not in dish.get("made_from", [])]
    if ingredients:
        facts.append(f"Ingredients (Wikidata): {', '.join(ingredients[:10])}")
    if dish.get("summary"):
        lines += [dish["summary"], ""]
    lines += [f"- {f}" for f in facts]
    if dish.get("fun_facts"):
        lines += ["", "Fun facts:", ""] + [f"- ({f['topic']}) {f['text']}" for f in dish["fun_facts"]]
    if dish.get("more_fun_facts"):
        lines += ["", "More fun facts (when the user asks for more):", ""]
        lines += [f"- ({f['topic']}) {f['text']}" for f in dish["more_fun_facts"]]
    if dish.get("learn_more"):
        lines += ["", "Learn more:", ""] + [f"- {link['level']}: [{link['title']}]({link['url']})"
                                            for link in dish["learn_more"]]
    credit = "; ".join(f"[{s['name']}]({s['url']}) ({s['licence']})" for s in dish.get("sources", []) if s.get("url"))
    lines += ["", f"Sources: {credit}. Review: {dish.get('review', 'not reviewed')}.", ""]
    return "\n".join(lines)


def write_notebook(dishes: Iterable[dict], folder: str | Path) -> dict[str, int]:
    """Write one Markdown page per country (dishes first, then foods and drinks) and an index; returns the counts."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    by_country: dict[str, list[dict]] = {}
    for d in dishes:
        by_country.setdefault(d.get("country") or "Other", []).append(d)
    for country, items in by_country.items():
        items.sort(key=lambda d: (d.get("kind") != "dish", d.get("region") or "", d["name"].lower()))
        text = [f"# {country}: dish knowledge", "",
                ("Collected from Wikipedia (CC BY-SA 4.0, credit per dish) and Wikidata (CC0) by "
                 "`scripts/knowledge/fetch_knowledge.py`, tidied by `everflavor.dish_knowledge`. "
                 "Facts are the sources' words; nothing is invented."), ""]
        text += [dish_card(d) for d in items]
        (folder / f"{slug(country)}.md").write_text("\n".join(text), encoding="utf-8")
    counts = {c: len(v) for c, v in sorted(by_country.items(), key=lambda kv: -len(kv[1]))}
    index = ["# Dish knowledge by country", "", "| Country | Entries |", "|---|---|"]
    index += [f"| [{c}]({slug(c)}.md) | {n} |" for c, n in counts.items()]
    (folder / "README.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    return counts
