"""The profile in levels: every rule a person can set, its category and how serious a match is.

The safety gate (safety.check_recipe) still decides every allergy, medical screen, religious and ethical diet;
this module only sorts its answer by category and severity and adds the checks that are cautions, not blocks:

| Severity | Shown as | Categories |
|---|---|---|
| critical | stop sign: Unsafe for you | allergies, medical screens |
| major | warning diamond: Doesn't match your profile | religious practice, ethical diets, personal and cultural rules, how it's cooked |
| moderate | caution triangle: Doesn't suit your sensitivities or goals | sensitivities, goals |
| info | information circle: Good to know | foods you don't eat |

Medical entries are ingredient screens and nutrition limits, never advice: each says what it checks. A condition
is only offered when its check rests on a list or a limit the project already uses (diets.py, flags.py); GERD,
kidney disease and others wait for a sourced trigger list (a recorded policy, proposed by Claude for Team
EverGlow's review, 2026-11-16).
"""
from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any

from .confidence import Confidence, gate_confidence, may_contain_in, severity_for
from .cooking import methods_from_instructions
from .diets import NUTRITION_DIETS
from .flags import FLAG_RULES
from .preparation import PREP_RISKS, prep_risks, step_sentences
from .recipe_check import opaque_word
from .safety import UserProfile, check_recipe

__all__ = ["CATEGORIES", "RULES", "SEVERITIES", "Rule", "assess", "profile_for", "rule_ids_from_profile", "rules_in"]

# severity -> (the pixel sign the app shows, design/pixel-art sign_<severity>.png; its words). Never emoji.
SEVERITIES = {"critical": ("stop sign", "Unsafe for you"), "major": ("warning diamond", "Doesn't match your profile"),
              "moderate": ("caution triangle", "Doesn't suit your sensitivities or goals"),
              "info": ("information circle", "Good to know")}
_ORDER = list(SEVERITIES)
CATEGORIES = {  # category -> (label, severity), in the order the profile shows them
    "allergies": ("Allergies", "critical"),
    "medical": ("Medical screens", "critical"),
    "religious": ("Religious practice", "major"),
    "ethical": ("Ethical diets", "major"),
    "cultural": ("Personal and cultural rules", "major"),
    "preparation": ("How it's cooked", "major"),
    "sensitivities": ("Sensitivities", "moderate"),
    "goals": ("Goals", "moderate"),
}


@dataclass(frozen=True)
class Rule:
    category: str
    label: str
    kind: str                     # flag, diet, vegetarian, vegan, method, prep, nutrient
    targets: tuple[str, ...] = ()
    severity: str = ""            # empty: the category's own
    note: str = ""                # what is checked, shown with the rule
    prep: tuple[str, ...] = ()    # preparation risks a flag or diet rule also checks (pregnancy: undercooked)

    @property
    def level(self) -> str:
        return self.severity or CATEGORIES[self.category][1]


def _flag(category: str, label: str, *flags: str, note: str = "", severity: str = "") -> Rule:
    return Rule(category, label, "flag", flags, severity, note)


def _diet(category: str, label: str, diet: str, note: str = "") -> Rule:
    return Rule(category, label, "diet", (diet,), "", note)


SODIUM, CARBS = NUTRITION_DIETS["lower_sodium"], NUTRITION_DIETS["low_carb"]
RULES: dict[str, Rule] = {
    # Allergies: the gate's flags, hidden sources included
    "peanut": _flag("allergies", "Peanuts", "contains_peanut"),
    "tree_nut": _flag("allergies", "Tree nuts", "contains_tree_nut"),
    "shellfish": _flag("allergies", "Shellfish", "contains_shellfish"),
    "fish": _flag("allergies", "Fish", "contains_fish"),
    "egg": _flag("allergies", "Eggs", "contains_egg"),
    "milk": _flag("allergies", "Milk", "contains_dairy"),
    "soy": _flag("allergies", "Soy", "contains_soy"),
    "wheat": _flag("allergies", "Wheat and gluten", "contains_gluten"),
    "sesame": _flag("allergies", "Sesame", "contains_sesame"),
    "mustard": _flag("allergies", "Mustard", "contains_mustard"),
    "celery": _flag("allergies", "Celery", "contains_celery"),
    "lupin": _flag("allergies", "Lupin", "contains_lupin"),
    "buckwheat": _flag("allergies", "Buckwheat", "contains_buckwheat"),
    # Medical screens (ingredient screens and nutrition limits, not advice)
    "celiac": _flag("medical", "Celiac disease", "contains_gluten",
                    note="gluten in any form; separate from a gluten-free preference"),
    "alpha_gal": _diet("medical", "Alpha-gal syndrome", "alpha_gal_friendly", note="red meat and gelatin"),
    "g6pd": _diet("medical", "G6PD deficiency", "g6pd_friendly", note="fava beans"),
    "gout": _diet("medical", "Gout", "gout_friendly", note="high-purine foods"),
    "maoi": _diet("medical", "MAOI medicines", "low_tyramine", note="high-tyramine foods"),
    "pregnancy": _diet("medical", "Pregnancy", "pregnancy_friendly",
                       note="alcohol, high-mercury fish, raw animal foods, soft cheese"),
    "blood_pressure": Rule("medical", "High blood pressure", "nutrient", (SODIUM[0], str(SODIUM[1])), "moderate",
                           f"sodium over {SODIUM[1]} mg per serving"),
    "diabetes": Rule("medical", "Diabetes (carbohydrates)", "nutrient", (CARBS[0], str(CARBS[1])), "moderate",
                     f"carbohydrates over {CARBS[1]} g per serving"),
    "ibs": _flag("medical", "IBS (common triggers)", "contains_allium", "contains_gluten", severity="moderate",
                 note="garlic and onion family, wheat"),
    # Religious practice (each "-friendly": a screen of the ingredients, never the practice itself)
    "halal": _diet("religious", "Halal-friendly ingredients", "halal_friendly"),
    "kosher": _diet("religious", "Kosher-friendly ingredients", "kosher_friendly"),
    "hindu_no_beef": _diet("religious", "No beef (Hindu)", "no_beef"),
    "jain": _diet("religious", "Jain-friendly", "jain_friendly"),
    "vaishnava": _diet("religious", "Vaishnava-friendly", "vaishnava_friendly"),
    "buddhist": _diet("religious", "Buddhist vegetarian", "buddhist_vegetarian"),
    "adventist": _diet("religious", "Adventist-friendly", "adventist_friendly"),
    "lds": _diet("religious", "Latter-day Saint-friendly", "lds_friendly"),
    "orthodox_fast": _diet("religious", "Orthodox fasting", "orthodox_fasting"),
    "ital": _diet("religious", "Ital-friendly", "ital_friendly"),
    # Ethical diets
    "vegetarian": Rule("ethical", "Vegetarian", "vegetarian"),
    "vegan": Rule("ethical", "Vegan", "vegan"),
    "pescatarian": _diet("ethical", "Pescatarian", "pescatarian"),
    "lacto_vegetarian": _diet("ethical", "Lacto-vegetarian", "lacto_vegetarian"),
    # Personal and cultural rules
    "no_alcohol": _flag("cultural", "No alcohol", "contains_alcohol", "contains_alcohol_extract"),
    "no_pork": _flag("cultural", "No pork", "contains_pork"),
    "no_raw_animal": _flag("cultural", "No raw fish or meat", "contains_raw_animal"),
    "no_processed_meat": _flag("cultural", "No processed meat", "contains_processed_meat"),
    "no_gelatin": _flag("cultural", "No gelatin", "contains_gelatin"),
    # How it's cooked (read from the recipe's steps)
    "no_deep_fried": Rule("preparation", "No deep-fried food", "method", ("deep_fry",)),
    "no_fried": Rule("preparation", "No fried food", "method", ("deep_fry", "pan_fry", "stir_fry")),
    "no_grilled": Rule("preparation", "No grilled or charred food", "method", ("grill_broil",)),
    "no_smoked": Rule("preparation", "No smoked food", "method", ("smoke",)),
    "no_uncooked": Rule("preparation", "No uncooked dishes", "method", ("no_cook",)),
    # How it's made (everflavor.preparation): read from the name, the lines and the steps
    "no_undercooked": Rule("preparation", "No raw or undercooked food", "prep", ("undercooked",), "",
                           "medium-rare, runny yolks, sushi, tartare, ceviche..."),
    "no_fermented": Rule("preparation", "No fermented food", "prep", ("fermented",), "moderate"),
    # Sensitivities: cautions, never blocks
    "lactose": _flag("sensitivities", "Lactose", "contains_dairy", note="some aged cheeses have little lactose"),
    "caffeine": _flag("sensitivities", "Caffeine", "contains_coffee_or_tea"),
    "sulfites": _flag("sensitivities", "Sulfites", "contains_sulfites"),
    "nightshades": _flag("sensitivities", "Nightshades", "contains_nightshade"),
    "allium": _flag("sensitivities", "Garlic and onions", "contains_allium"),
    # Goals: they inform, never block
    "low_carb": Rule("goals", "Low carb", "nutrient", (CARBS[0], str(CARBS[1])), "", f"at most {CARBS[1]} g per serving"),
    "lower_sodium": Rule("goals", "Lower sodium", "nutrient", (SODIUM[0], str(SODIUM[1])), "",
                         f"at most {SODIUM[1]} mg per serving"),
    "high_protein": Rule("goals", "High protein", "nutrient_min", ("protein_g", "25"), "", "at least 25 g per serving"),
}


RULES["nightshade_free"] = _diet("cultural", "Nightshade-free", "nightshade_free")
# Pregnancy also screens how the dish is made: raw or undercooked animal food named in the name, lines or steps
RULES["pregnancy"] = replace(RULES["pregnancy"], prep=("undercooked",),
                             note=RULES["pregnancy"].note + ", raw or undercooked dishes")
# Every other flag the profile can pick is a personal or cultural rule ("No beef", "No carmine" is the insect dye)
_COVERED = {t for r in RULES.values() if r.kind == "flag" for t in r.targets} | {"contains_pet_meat"}
for _name in sorted(set(FLAG_RULES) - _COVERED):
    RULES[f"no_{_name.removeprefix('contains_')}"] = _flag(
        "cultural", "No " + _name.removeprefix("contains_").replace("_", " "), _name)


def rule_ids_from_profile(avoid: Iterable[str] = (), diets: Iterable[str] = (), vegetarian: bool = False,
                          vegan: bool = False) -> list[str]:
    """The levels' rule ids for a profile set the classic way (allergy flags, diets, vegetarian, vegan): each flag
    goes to its allergy when it has one ("contains_gluten" is the wheat allergy; celiac is chosen on its own)."""
    out: list[str] = []
    for flag in avoid:
        flag_rules = [(r, rule) for r, rule in RULES.items() if rule.kind == "flag" and flag in rule.targets
                      and rule.category != "medical"]
        rid = next((r for r, rule in flag_rules if rule.targets == (flag,)), None) or             next((r for r, _ in flag_rules), None)
        if rid:
            out.append(rid)
    for diet in diets:
        out += [r for r, rule in RULES.items() if rule.kind == "diet" and rule.targets == (diet,)][:1]
    out += (["vegetarian"] if vegetarian else []) + (["vegan"] if vegan else [])
    return list(dict.fromkeys(out))


def rules_in(category: str) -> list[str]:
    """The rule ids of one category, in the profile's order."""
    return [rid for rid, rule in RULES.items() if rule.category == category]


def profile_for(rule_ids: Iterable[str], skip: Sequence[str] = (), calories: float | None = None) -> UserProfile:
    """The safety gate's profile for the blocking rules (critical and major); cautions and goals stay out of it."""
    avoid: list[str] = []
    diets: list[str] = []
    vegetarian = vegan = False
    for rid in rule_ids:
        rule = RULES[rid]
        if rule.level not in ("critical", "major"):
            continue
        if rule.kind == "flag":
            avoid += [f for f in rule.targets if f not in avoid]
        elif rule.kind == "diet":
            diets += [d for d in rule.targets if d not in diets]
        vegetarian |= rule.kind == "vegetarian"
        vegan |= rule.kind == "vegan"
    return UserProfile(avoid=tuple(avoid), diets=tuple(diets), vegetarian=vegetarian, vegan=vegan,
                       calories_per_meal=calories, skip=tuple(skip))


def _rules_for_problem(problem: Mapping[str, Any], chosen: Sequence[str]) -> list[str]:
    """Which of the user's rules a gate problem belongs to (a flag can serve two: wheat allergy and celiac)."""
    name = str(problem.get("rule", ""))
    out = []
    for rid in chosen:
        rule = RULES[rid]
        if (rule.kind == "flag" and name in rule.targets) or (rule.kind == "diet" and name in rule.targets) \
                or (rule.kind in ("vegetarian", "vegan") and name == rule.kind):
            out.append(rid)
    return out


def assess(lines: Sequence[str], name: str, rule_ids: Iterable[str], skip: Sequence[str] = (),
           instructions: object = None, nutrition: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Check a recipe against the whole profile, level by level.

    Args:
        lines: Ingredient lines.
        name: The dish name (names count too).
        rule_ids: The user's rules (keys of RULES).
        skip: Foods the user doesn't eat (info only).
        instructions: The steps, for "How it's cooked" (not checked without them).
        nutrition: Per-serving values (sodium_mg, carbs_g, protein_g) for goals (not checked without them).

    Every finding also carries `items`, one per line, each with its confidence (everflavor.confidence): the gate's
    own matches keep their rule's severity and are labelled verified, likely or possible; a food from the
    may-contain table adds a likely or possible caution the gate does not make; a ready-made product no rule
    explains is unknown ("check the label").

    Returns:
        {"findings": [{"rule", "label", "category", "severity", "lines", "why", "items": [{"line", "why",
        "confidence", "note", "source", "severity"}]}], "ok": [labels checked and fine], "not_checked": [labels
        with why], "overall": the worst severity found, or "clear", "by_confidence": {confidence: [{"line",
        "rules", "notes", "sources", "severity"}]} for the lines with something to say, "no_issue": [the other
        lines]}.
    """
    chosen = [r for r in dict.fromkeys(rule_ids) if r in RULES]
    findings: list[dict[str, Any]] = []
    not_checked: list[str] = []
    profile = profile_for(chosen, skip)
    gate = check_recipe(lines, name, profile)   # the gate decides the blocking rules
    for problem in gate["problems"]:
        conf, note, source = gate_confidence(str(problem["line"]), problem["flag"], problem["matched"])
        owners = _rules_for_problem(problem, chosen)
        if not owners:   # pet meat (P24): always checked, always unsafe
            _add(findings, "pet_meat", problem["line"], problem["matched"], conf, note, source, "critical")
        for rid in owners:
            _add(findings, rid, problem["line"], problem["matched"], conf, note, source)
    cautions = [r for r in chosen if RULES[r].kind == "flag" and RULES[r].level == "moderate"]
    caution_flags = tuple(dict.fromkeys(f for r in cautions for f in RULES[r].targets))
    if cautions:   # sensitivities and moderate screens: the same reading of the names, shown as cautions
        for problem in check_recipe(lines, name, UserProfile(avoid=caution_flags))["problems"]:
            conf, note, source = gate_confidence(str(problem["line"]), problem["flag"], problem["matched"])
            for rid in cautions:
                if problem["rule"] in RULES[rid].targets:
                    _add(findings, rid, problem["line"], problem["matched"], conf, note, source)
    named = [*lines, *([f"(dish name) {name}"] if str(name or "").strip() else [])]
    for line in named:   # foods usually or sometimes made with something the profile watches
        for row in may_contain_in(line):
            hits = [(p, _rules_for_problem(p, chosen)) for p in check_recipe(list(row.contains), "", profile)["problems"]]
            hits += [(p, [r for r in cautions if p["rule"] in RULES[r].targets]) for p in
                     check_recipe(list(row.contains), "", UserProfile(avoid=caution_flags))["problems"]] if cautions else []
            for problem, owners in hits:
                for rid in owners:
                    if problem["flag"] in row.flags and not _has(findings, rid, line):
                        level = severity_for(RULES[rid].level, row.confidence, category=RULES[rid].category)
                        _add(findings, rid, line, [f"{row.item} ({', '.join(row.contains)})"], row.confidence,
                             row.note, row.source, level)
    if chosen:   # a ready-made product nothing above explains: its contents are unknown
        explained = {i["line"] for f in findings for i in f["items"]}
        for line in lines:
            word = opaque_word(line)
            if word and line not in explained:
                _add(findings, "label_check", line, [word], Confidence.UNKNOWN,
                     f"a {word} whose ingredients the name does not show", "", "moderate")
    if instructions:   # foods the steps bring in that the lines don't show (beer for the batter, wine to deglaze)
        for problem in check_recipe(step_sentences(instructions), "", profile)["problems"]:
            for rid in _rules_for_problem(problem, chosen):
                words = set(problem["matched"] if isinstance(problem["matched"], list) else [problem["matched"]])
                if not any(set(i["why"]) & words for f in findings if f["rule"] == rid for i in f["items"]):
                    _add(findings, rid, problem["line"], problem["matched"], Confidence.POSSIBLE,
                         "the steps mention it: check whether it goes into the dish", "",
                         severity_for(RULES[rid].level, Confidence.POSSIBLE, category=RULES[rid].category),
                         kind="preparation")
    methods = set(methods_from_instructions(instructions)) if instructions else set()
    risks = prep_risks("\n".join([str(name or ""), *lines, str(instructions or "")]))
    for rid in chosen:
        rule = RULES[rid]
        targets = rule.targets if rule.kind == "prep" else rule.prep
        for risk in targets:   # raw or undercooked, fermented: named in the dish name, a line or the steps
            if risk in risks:
                _add(findings, rid, f"(how it's made) {PREP_RISKS[risk][0]}", risks[risk],
                     note="the recipe says " + ", ".join(risks[risk]), kind="preparation")
            elif rule.kind == "prep" and not instructions:
                not_checked.append(f"{rule.label} (no steps to read)")
        if rule.kind == "method":
            if not instructions:
                not_checked.append(f"{rule.label} (no steps to read)")
            elif methods & set(rule.targets):
                used = [m.replace("_", " ") for m in sorted(methods & set(rule.targets))]
                _add(findings, rid, "(how it's made) " + ", ".join(used), used,
                     note="the steps say so", kind="preparation")
        elif rule.kind in ("nutrient", "nutrient_min"):
            column, limit = rule.targets[0], float(rule.targets[1])
            value = _number((nutrition or {}).get(column))
            if value is None:
                not_checked.append(f"{rule.label} (no nutrition for this recipe)")
            elif (rule.kind == "nutrient" and value > limit) or (rule.kind == "nutrient_min" and value < limit):
                _add(findings, rid, "per serving", [f"{column.split('_')[0]} {value:.0f}"])
    for item in gate.get("skipped", []):
        findings.append({"rule": "skip", "label": "Foods you don't eat", "category": "dislikes", "severity": "info",
                         "lines": [item["line"]], "why": list(item["foods"]), "items": []})
    hit = {f["rule"] for f in findings}
    ok = [RULES[r].label for r in chosen if r not in hit
          and not any(n.startswith(RULES[r].label + " (") for n in not_checked)]
    worst = min((_ORDER.index(f["severity"]) for f in findings), default=None)
    by_confidence = _by_confidence(findings)
    said = {row["line"] for rows in by_confidence.values() for row in rows}
    preparation = [row for rows in _by_confidence(findings, "preparation").values() for row in rows]
    return {"findings": findings, "ok": ok, "not_checked": not_checked,
            "overall": _ORDER[worst] if worst is not None else "clear",
            "by_confidence": by_confidence, "preparation": preparation,
            "no_issue": [line for line in lines if line not in said]}


def _by_confidence(findings: list[dict[str, Any]], kind: str = "ingredient") -> dict[str, list[dict[str, Any]]]:
    """The findings' lines grouped by how sure they are: each line once, under its most certain match, with every
    rule it touches."""
    order = list(Confidence)
    lines: dict[str, dict[str, Any]] = {}
    for found in findings:
        for item in found["items"]:
            if item["kind"] != kind:
                continue
            row = lines.setdefault(str(item["line"]), {"line": str(item["line"]), "rules": [], "notes": [],
                                                       "sources": [], "severity": item["severity"],
                                                       "confidence": item["confidence"]})
            row["rules"] = list(dict.fromkeys([*row["rules"], found["label"]]))
            row["notes"] = list(dict.fromkeys([*row["notes"], item["note"]]))
            row["sources"] = list(dict.fromkeys([*row["sources"], *([item["source"]] if item["source"] else [])]))
            row["severity"] = min(row["severity"], item["severity"], key=_ORDER.index)
            row["confidence"] = min(row["confidence"], item["confidence"], key=order.index)
    out: dict[str, list[dict[str, Any]]] = {c.value: [] for c in order}
    for row in lines.values():
        out[Confidence(row.pop("confidence")).value].append(row)
    return out


def _number(value: object) -> float | None:
    """A per-serving value as a number, or None when it is missing or not a number (NaN included)."""
    try:
        number = float(value)   # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return None if math.isnan(number) else number


# findings that belong to no rule of the profile: pet meat (P24, always checked) and a product to check the label of
_SPECIAL = {"pet_meat": ("Never served", "cultural"), "label_check": ("Check the label", "unknown")}


def _has(findings: list[dict[str, Any]], rid: str, line: str) -> bool:
    return any(f["rule"] == rid and any(str(i["line"]) == line for i in f["items"]) for f in findings)


def _add(findings: list[dict[str, Any]], rid: str, line: object, why: object,
         confidence: Confidence = Confidence.VERIFIED, note: str = "", source: str = "",
         severity: str | None = None, kind: str = "ingredient") -> None:
    """Add one line to a rule's finding (one finding per rule; its severity is the worst of its lines)."""
    label, category = _SPECIAL[rid] if rid in _SPECIAL else (RULES[rid].label, RULES[rid].category)
    level = severity or RULES[rid].level
    words = why if isinstance(why, list) else [why]
    item = {"line": line, "why": words, "confidence": confidence.value, "note": note, "source": source,
            "severity": level, "kind": kind}
    for found in findings:
        if found["rule"] == rid:
            found["lines"].append(line)
            found["why"] = list(dict.fromkeys([*found["why"], *words]))
            found["items"].append(item)
            found["severity"] = min(found["severity"], level, key=_ORDER.index)
            return
    findings.append({"rule": rid, "label": label, "category": category, "severity": level,
                     "lines": [line], "why": list(words), "items": [item]})
