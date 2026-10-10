"""Local language model through Ollama (roadmap step 6: agents without an API key).

Ollama (https://ollama.com) runs open models on the user's own computer: free, and the
user's allergies and diets never leave the machine. It only exists in VS Code and
Antigravity on a computer where Ollama is installed and running; in Colab, or when it is
not running, `ollama_status` says so and the agents fall back to the rule-based tools
(recommend.py). Nothing here is imported by the notebooks, so Colab is never affected.

The model only proposes. Every tool gets the user's profile from the code (`safety_tool`,
`recommend_tool`), never from the model's arguments. For a recipe the code already holds,
`check_and_explain` runs the gate itself and lets the model only explain a failure: a model
can drop lines when it copies a recipe into a tool (seen in a live test), and its words are
replaced unless they match the verdict (`faithful`). `choose_model` is the one place that picks a model.
"""
from __future__ import annotations

import json
import os
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import requests

from .environment import _in_colab
from .safety import UserProfile, check_recipe

__all__ = [
    "OLLAMA_URL",
    "TOOL_MODELS",
    "Tool",
    "chat",
    "check_and_explain",
    "choose_model",
    "faithful",
    "ollama_status",
    "ollama_url",
    "pick_model",
    "recommend_tool",
    "run_tools",
    "safety_tool",
    "tool_arguments",
    "verdict_text",
]

OLLAMA_URL = "http://localhost:11434"

# Small models with tool calling that run on a 16 GB laptop, best first (checked on
# ollama.com/search?c=tools, October 2026). Any other installed tool model also works.
TOOL_MODELS = ("granite4.1:3b", "llama3.2:latest", "tev1:4b", "granite4.1:8b")


def ollama_url() -> str:
    """The Ollama address: OLLAMA_HOST when set (as Ollama itself reads it), else OLLAMA_URL."""
    host = os.environ.get("OLLAMA_HOST", "").strip()
    if not host:
        return OLLAMA_URL
    if host.startswith("0.0.0.0"):   # a listen address, not one to call
        host = host.replace("0.0.0.0", "localhost", 1)
    return (host if "://" in host else f"http://{host}").rstrip("/")


def ollama_status(url: str | None = None, timeout: float = 2.0) -> dict:
    """Is Ollama usable here, and which installed models can call tools?

    Args:
        url: The Ollama address (default `ollama_url()`).
        timeout: Seconds to wait for each request.

    Returns:
        {"available", "reason" (why not, or ""), "version", "models" (all installed),
        "tool_models" (those that can call tools)}. Never raises: an unusable Ollama is
        an answer, not an error.
    """
    status: dict = {"available": False, "reason": "", "version": None, "models": [], "tool_models": []}
    if _in_colab():
        status["reason"] = "Colab: Ollama runs only on your own computer (VS Code / Antigravity)"
        return status
    url = url or ollama_url()
    try:
        status["version"] = requests.get(f"{url}/api/version", timeout=timeout).json().get("version")
        models = [m["name"] for m in requests.get(f"{url}/api/tags", timeout=timeout).json().get("models", [])]
    except (requests.RequestException, ValueError) as error:
        status["reason"] = f"Ollama is not running at {url} (start the Ollama app): {type(error).__name__}"
        return status
    status["models"] = models
    for name in models:
        try:
            info = requests.post(f"{url}/api/show", json={"model": name}, timeout=timeout).json()
        except (requests.RequestException, ValueError):
            continue
        if "tools" in info.get("capabilities", []):
            status["tool_models"].append(name)
    status["available"] = bool(status["tool_models"])
    if not status["available"]:
        status["reason"] = f"no installed model can call tools; try: ollama pull {TOOL_MODELS[0]}"
    return status


def pick_model(status: Mapping, preferred: Sequence[str] = TOOL_MODELS) -> str | None:
    """The first preferred model that is installed and can call tools, else any tool model, else None."""
    tool_models = list(status.get("tool_models", []))
    for name in preferred:
        if name in tool_models:
            return name
    return tool_models[0] if tool_models else None


def chat(messages: Sequence[Mapping], model: str, tools: Sequence[Mapping] | None = None,
         url: str | None = None, timeout: float = 180, temperature: float = 0.0) -> dict:
    """Send one chat turn to Ollama and return the model's message.

    Args:
        messages: The conversation so far ({"role", "content"} dicts).
        model: An installed model name.
        tools: Tool schemas the model may call (see `Tool.schema`).
        url: The Ollama address (default `ollama_url()`).
        timeout: Seconds to wait (small models on a laptop CPU take 5-30 s).
        temperature: 0 makes answers repeatable.

    Returns:
        The message dict: "content", and "tool_calls" when the model calls a tool.

    Raises:
        RuntimeError: If Ollama cannot be reached or answers with an error.
    """
    body: dict = {"model": model, "messages": list(messages), "stream": False,
                  "options": {"temperature": temperature}}
    if tools:
        body["tools"] = list(tools)
    try:
        response = requests.post(f"{url or ollama_url()}/api/chat", json=body, timeout=timeout)
        data = response.json()
    except (requests.RequestException, ValueError) as error:
        raise RuntimeError(f"Ollama did not answer: {error}") from error
    if "error" in data or "message" not in data:
        raise RuntimeError(f"Ollama error: {data.get('error', data)}")
    return data["message"]


def tool_arguments(call: Mapping) -> dict:
    """A tool call's arguments as plain values.

    Small models often send lists as JSON text ('["a", "b"]') or the whole argument
    object as text; both are decoded. Other text stays as it is.
    """
    args = call.get("function", {}).get("arguments", {})
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except ValueError:
            return {}
    clean = {}
    for key, value in dict(args).items():
        if isinstance(value, str) and value.strip()[:1] in ("[", "{"):
            try:
                value = json.loads(value)
            except ValueError:
                pass
        clean[key] = value
    return clean


@dataclass(frozen=True)
class Tool:
    """A function the model may call: its name, what it does, its JSON-schema parameters."""

    name: str
    description: str
    parameters: Mapping[str, object]
    run: Callable[..., Any]

    def schema(self) -> dict:
        """The tool as Ollama's /api/chat expects it."""
        return {"type": "function", "function": {"name": self.name, "description": self.description,
                                                 "parameters": dict(self.parameters)}}


def safety_tool(profile: UserProfile) -> Tool:
    """The safety gate as a tool. The profile is fixed here: the model only sends the recipe."""
    def run(recipe_name: object = "", ingredient_lines: object = (), **_ignored: object) -> dict:
        # _ignored: restrictions the model adds on its own ("avoid": ["peanuts"]) never count
        if isinstance(ingredient_lines, str):
            lines: list[object] = list(ingredient_lines.splitlines())
        elif isinstance(ingredient_lines, (list, tuple)):
            lines = list(ingredient_lines)
        else:   # never pass a recipe whose lines could not be read
            raise TypeError(f"ingredient_lines must be a list of strings, got {type(ingredient_lines).__name__}")
        return check_recipe(lines, recipe_name, profile)

    return Tool(
        name="check_recipe",
        description="Check a recipe against the user's food restrictions. Returns passed and, for "
                    "each problem, the ingredient line and the rule it breaks.",
        parameters={"type": "object", "required": ["recipe_name", "ingredient_lines"], "properties": {
            "recipe_name": {"type": "string", "description": "The dish name"},
            "ingredient_lines": {"type": "array", "items": {"type": "string"},
                                 "description": "One ingredient per item, with amounts"}}},
        run=run,
    )


def run_tools(messages: Sequence[Mapping], model: str, tools: Sequence[Tool], url: str | None = None,
              max_rounds: int = 4, timeout: float = 180) -> dict:
    """Let the model call tools until it answers in words (one agent's loop).

    Args:
        messages: The conversation so far.
        model: An installed model that can call tools.
        tools: The tools it may use.
        url: The Ollama address (default `ollama_url()`).
        max_rounds: Most model turns before stopping (a small model can loop).
        timeout: Seconds to wait for each model turn.

    Returns:
        {"answer" (the last text, "" if the rounds ran out), "calls" ([{"name", "arguments",
        "result"}] in order), "messages" (the whole conversation)}. A tool that fails or does
        not exist sends the model an error message instead of stopping the loop.
    """
    if max_rounds < 1:
        raise ValueError(f"max_rounds must be at least 1, got {max_rounds}")
    by_name = {tool.name: tool for tool in tools}
    history: list[dict] = [dict(m) for m in messages]
    calls: list[dict] = []
    for _ in range(max_rounds):
        reply = chat(history, model, [t.schema() for t in tools], url=url, timeout=timeout)
        history.append(reply)
        if not reply.get("tool_calls"):
            return {"answer": reply.get("content", ""), "calls": calls, "messages": history}
        for call in reply["tool_calls"]:
            name, args = call.get("function", {}).get("name", ""), tool_arguments(call)
            if name not in by_name:
                result: object = {"error": f"unknown tool {name!r}; tools: {sorted(by_name)}"}
            else:
                try:
                    result = by_name[name].run(**args)
                except (TypeError, ValueError, KeyError, AttributeError) as error:  # bad arguments: tell the model
                    result = {"error": f"{type(error).__name__}: {error}"}
            calls.append({"name": name, "arguments": args, "result": result})
            history.append({"role": "tool", "tool_name": name, "content": json.dumps(result, default=str)})
    return {"answer": "", "calls": calls, "messages": history}


# ---------------------------------------------------------------- code decides, the model explains
# Live tests (October 2026, 14 recipes x 2 models):
# 1. Both models called the safety tool every time, but granite4.1:3b, told "no need to check", sent the
#    gate only 2 of 5 ingredient lines. A dropped line can hide an allergen, so the verdict comes from the
#    recipe the code holds, never from the model's copy (`check_and_explain`).
# 2. Asked to explain a passed check, both models invented broken rules ("passed, but it broke the rule
#    pet meat"); a passed recipe gets the plain sentence. For a failed one the model's words are kept only
#    when they warn clearly, name a matched ingredient and mention no rule that was not broken.
# cspell:disable
_WARNING = re.compile(r"\bnot (?:safe|suitable|fine|halal|kosher|vegan|vegetarian|allowed|ok)\b|\bunsafe\b"
                      r"|\bavoid\b|\bcannot\b|\bcan.t\b|\bshould ?n.t\b|\bbr(?:eaks?|oke|oken)\b"
                      r"|\bfail(?:s|ed)?\b|\bviolat\w*|\bdo(?:es)?(?: not|n.t) (?:fit|meet|comply|align)\b"
                      r"|\bisn.t (?:safe|suitable)\b|\bnon-(?:halal|kosher|vegan|vegetarian)\b|\bconflicts?\b"
                      r"|\bincompatible\b|\bunsuitable\b", re.IGNORECASE)
# cspell:enable
EXPLAIN_SYSTEM = ("Rewrite the facts below as a short, friendly warning to the user, in at most two sentences. "
                  "Keep every fact exactly, add nothing, and never say the recipe is safe.")


def _rule_name(rule: str) -> str:
    """'contains_tree_nut' -> 'tree nut', 'halal_friendly' -> 'halal'."""
    return rule.removeprefix("contains_").removesuffix("_friendly").replace("_", " ")


def verdict_text(report: Mapping, recipe_name: object) -> str:
    """The gate's answer in plain words, without a model (the fallback, and what the model must agree with)."""
    name = str(recipe_name or "This recipe").strip()
    if report.get("passed"):
        rules = ", ".join(_rule_name(r) for r in report.get("checked", []) if r != "contains_pet_meat")
        return f"{name} fits your profile: no ingredient breaks your rules" + (f" ({rules})." if rules else ".")
    parts = [f"{p['line']} ({_rule_name(p['rule'])}: {', '.join(map(str, p.get('matched') or [])) or p['flag']})"
             for p in report.get("problems", [])]
    return f"{name} does not fit your profile: " + "; ".join(parts) + "."


def _facts(report: Mapping, recipe_name: object) -> str:
    """The failure as plain sentences, so a small model only rewords them (it reasons badly from raw data:
    "it incorrectly listed satay sauce instead of a peanut ingredient")."""
    lines = [f"{recipe_name} does not fit the user's food rules."]
    for p in report.get("problems", []):
        what = ", ".join(map(str, p.get("matched") or [])) or _rule_name(p["flag"])
        line = str(p["line"])
        where = (f"The dish name '{line.removeprefix('(dish name) ')}'" if line.startswith("(dish name)")
                 else f"The ingredient '{line}'")
        lines.append(f"{where} contains {what}, which breaks the user's {_rule_name(p['rule'])} rule.")
    return "\n".join(lines)


def faithful(text: str, report: Mapping) -> bool:
    """Do these words say what the gate said?

    Passed: no warning words. Failed: a clear warning ("not safe", "violates", "avoid" ...), at least one
    matched ingredient named, and no rule named that the recipe did not break (a model once blamed "pet
    meat" for chicken). Anything else is replaced by `verdict_text`.
    """
    warns = bool(_WARNING.search(text))
    if report.get("passed"):
        return not warns
    lower = text.lower()
    matched = {str(m).lower() for p in report.get("problems", []) for m in (p.get("matched") or [])}
    broken = {_rule_name(p["rule"]) for p in report.get("problems", [])}
    unbroken = {_rule_name(r) for r in report.get("checked", [])} - broken
    names_cause = any(m and m in lower for m in matched)
    wrong_rule = any(re.search(rf"\b{re.escape(rule)}\b", lower) for rule in unbroken)
    return warns and names_cause and not wrong_rule


def check_and_explain(ingredient_lines: Sequence[object], recipe_name: object, profile: UserProfile,
                      model: str | None = None, url: str | None = None, timeout: float = 180) -> dict:
    """Check a recipe with the safety gate, then (optionally) let a local model explain a failure.

    The verdict always comes from `safety.check_recipe` on the lines given here. A passed recipe gets
    the plain `verdict_text`; for a failed one the model writes the explanation, which is kept only when
    `faithful` (else, or when Ollama fails, the plain text is used).

    Returns:
        check_recipe's report plus "text" (what to show), "explained_by" (the model, or "rules") and
        "model_text" (the model's own words, kept even when they were replaced).
    """
    report = check_recipe(ingredient_lines, recipe_name, profile)
    result = {**report, "text": verdict_text(report, recipe_name), "explained_by": "rules", "model_text": ""}
    if not model or report["passed"]:
        return result
    try:
        reply = chat([{"role": "system", "content": EXPLAIN_SYSTEM},
                      {"role": "user", "content": _facts(report, recipe_name)}], model, url=url, timeout=timeout)
    except RuntimeError:
        return result
    words = str(reply.get("content", "")).strip()
    result["model_text"] = words
    if words and faithful(words, report):
        result.update(text=words, explained_by=model)
    return result


def choose_model(url: str | None = None, preferred: Sequence[str] = TOOL_MODELS) -> dict:
    """The one place that decides what answers: a local Ollama model when one can call tools, else the rules.

    Returns:
        {"kind": "ollama" | "rules", "model" (or None), "reason" (why not Ollama, or "")}.
        A hosted model (Groq, Claude) becomes the middle choice once a key and its client are added.
    """
    status = ollama_status(url)
    model = pick_model(status, preferred) if status["available"] else None
    if model:
        return {"kind": "ollama", "model": model, "reason": ""}
    return {"kind": "rules", "model": None, "reason": status["reason"]}


def recommend_tool(recipes: Any, profile: UserProfile, max_results: int = 5) -> Tool:
    """Recipe ideas as a tool. Like the safety tool, the restrictions come from the profile, not the model."""
    from .recommend import baseline_recommend

    families = sorted(str(f) for f in recipes["cuisine_family"].dropna().unique())

    def run(cuisine: object = None, calories: object = None, how_many: object = 3, **_ignored: object) -> list[dict]:
        # _ignored: restrictions the model adds on its own never count; the profile decides
        target = float(str(calories)) if calories not in (None, "") else (profile.calories_per_meal or 500.0)
        family = None if str(cuisine or "").strip().lower() in ("", "any", "none") else str(cuisine)
        count = max(1, min(int(float(str(how_many or 3))), max_results))
        found = baseline_recommend(recipes, cuisine_family=family, calorie_target=target,
                                   vegetarian_only=profile.vegetarian, vegan_only=profile.vegan,
                                   avoid=profile.avoid, diets=profile.diets, top_n=count)
        return [{"name": str(r["recipe_name"]), "cuisine": str(r["cuisine_family"]),
                 "calories": round(float(r["calories_per_serving"])),
                 "ingredients": [str(i) for i in list(r["ingredient_list"])[:15]]} for _, r in found.iterrows()]

    return Tool(
        name="recommend_recipes",
        description="Find recipes that already fit the user's food restrictions. Returns name, cuisine, "
                    "calories per serving and ingredients.",
        parameters={"type": "object", "properties": {
            "cuisine": {"type": "string", "enum": ["any", *families], "description": "Cuisine family, or any"},
            "calories": {"type": "number", "description": "Target calories per serving"},
            "how_many": {"type": "integer", "description": f"How many recipes, 1 to {max_results}"}}},
        run=run,
    )
