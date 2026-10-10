"""The CrewAI meal planner (roadmap step 6): a Chef agent writes, the code checks.

Flow for one request ("a Thai-style dinner"):

1. The Chef agent (CrewAI, local Ollama model) writes one recipe as structured data, with the tools
   recommend_recipes, find_substitutions, count_calories and check_recipe (agent_tools.py).
2. The code runs the safety gate on the Chef's own lines (`llm.check_and_explain`). A failed recipe goes
   back to the Chef with the problems, at most `max_retries` times; if it still fails, the user gets a
   safe dish from `recommend_recipes` instead (`fallback`). A safe recipe more than 25% over the
   calorie budget goes back too, to be lightened; the safe version is kept if that does not work.
3. Calories and where to buy come from the tools, called by the code: in live tests models invented
   stores and gave "0 kcal" for lines without amounts, so their words are not used for facts.

The profile comes from the app's form, never from the model (the proposal's Nutritionist & Preference
Agent is the form here). CrewAI is optional: it is imported only when a crew is built, so this module,
its tests and Colab work without it. Install for VS Code / Antigravity: config/requirements-app.txt.
"""
from __future__ import annotations

import json
import os
import time
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from .agent_tools import agent_tools, resolve_origin
from .llm import Tool, check_and_explain, ollama_url, profile_text
from .safety import UserProfile

__all__ = [
    "MAX_RETRIES",
    "chef_writer",
    "plan_meal",
    "to_crewai_tool",
]

MAX_RETRIES = 2          # times a failed recipe goes back to the Chef before the safe fallback
CHEF_MAX_STEPS = 6       # tool calls the Chef may make per attempt (a small model can loop)
SOURCING_ITEMS = 3       # ingredients to look up in where_to_buy
OVER_BUDGET = 0.25       # a safe recipe this far over the calorie budget goes back to the Chef once more

RecipeWriter = Callable[[str, Sequence[str]], Mapping[str, Any]]


def to_crewai_tool(tool: Tool) -> Any:
    """An EverFlavor `Tool` as a CrewAI tool: the same function and JSON schema, errors returned as text."""
    from crewai.tools import BaseTool
    from pydantic import BaseModel, Field, create_model

    types = {"string": str, "number": float, "integer": int, "array": list, "object": dict}
    props = dict(tool.parameters.get("properties", {}))   # type: ignore[call-overload]
    required = set(tool.parameters.get("required", []))   # type: ignore[call-overload]
    fields: dict[str, Any] = {}
    for key, spec in props.items():
        kind = types.get(spec.get("type"), str)
        fields[key] = (kind, Field(..., description=spec.get("description", ""))) if key in required else \
            (kind | None, Field(None, description=spec.get("description", "")))
    schema = create_model(f"{tool.name}_args", **fields)

    class Wrapped(BaseTool):
        name: str = tool.name
        description: str = tool.description
        args_schema: type[BaseModel] = schema

        def _run(self, **kwargs: Any) -> str:
            try:
                return json.dumps(tool.run(**{k: v for k, v in kwargs.items() if v is not None}), default=str)
            except (TypeError, ValueError, KeyError) as error:
                return json.dumps({"error": str(error)})

    return Wrapped()


def chef_writer(tools: Sequence[Tool], profile: UserProfile, model: str, url: str | None = None) -> RecipeWriter:
    """A CrewAI Chef agent on a local Ollama model, as a function: (request, problems to fix) -> recipe dict."""
    os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")   # CrewAI sends usage data by default
    os.environ.setdefault("OTEL_SDK_DISABLED", "true")
    from crewai import LLM, Agent, Crew, Process, Task
    from pydantic import BaseModel

    class Recipe(BaseModel):
        name: str
        servings: int
        ingredient_lines: list[str]
        steps: list[str]

    chef_tools = [to_crewai_tool(t) for t in tools
                  if t.name in ("recommend_recipes", "find_substitutions", "count_calories", "check_recipe")]
    local = LLM(model=f"ollama/{model}", base_url=url or ollama_url(), temperature=0)
    def chef(with_tools: bool) -> Any:
        return Agent(role="Chef", goal="Write one authentic recipe that fits the user's food rules and calorie budget.",
                     backstory=profile_text(profile) + (" You check every recipe with check_recipe before giving it."
                                                        if with_tools else ""),
                     tools=chef_tools if with_tools else [], llm=local, verbose=False, max_iter=CHEF_MAX_STEPS)

    chefs = {True: chef(True), False: chef(False)}

    def run(request: str, fix: str, with_tools: bool) -> Mapping[str, Any]:
        task = Task(description=f"The user wants: {request} Write one recipe with amounts for each ingredient line.{fix}",
                    expected_output="The recipe as JSON: name, servings, ingredient_lines, steps.",
                    agent=chefs[with_tools], output_pydantic=Recipe)
        Crew(agents=[chefs[with_tools]], tasks=[task], process=Process.sequential, verbose=False).kickoff()
        out = task.output.pydantic if task.output else None
        if out is None:
            raise ValueError("the Chef did not return a recipe")
        return out.model_dump()

    def write(request: str, problems: Sequence[str]) -> Mapping[str, Any]:
        fix = (" Your last recipe broke the user's rules; replace these ingredients: " + "; ".join(problems)
               if problems else "")
        try:
            return run(request, fix, with_tools=True)
        except ValueError:   # live: CrewAI's tool loop sometimes gets an empty reply from a small model
            pass
        except (OSError, TimeoutError) as error:   # Ollama down or restarting (it updates itself)
            raise RuntimeError(f"the Chef could not run: {type(error).__name__}: {error}") from error
        try:   # the same attempt without tools: the code checks the recipe anyway
            return run(request, fix, with_tools=False)
        except (OSError, TimeoutError, ValueError) as error:
            raise RuntimeError(f"the Chef could not run: {type(error).__name__}: {error}") from error

    return write


def _origin(request: str, countries: Sequence[str]) -> str | None:
    """The country a request names ("a Thai-style dinner" -> Thailand), else None."""
    words = request.replace("-", " ").split()
    for size in (2, 1):
        for i in range(len(words) - size + 1):
            try:
                return resolve_origin(" ".join(words[i:i + size]).strip(".,!?"), countries)[0]
            except ValueError:
                continue
    return None


def _over_budget(recipe: Mapping[str, Any], profile: UserProfile, tools: Mapping[str, Tool]) -> int | None:
    """kcal per serving when a safe recipe is more than OVER_BUDGET over the user's budget, else None.

    Live: the Chef's first Thai curry was 1,424 kcal per serving for a 600 kcal budget.
    """
    if not profile.calories_per_meal or "count_calories" not in tools:
        return None
    try:
        counted = tools["count_calories"].run(ingredient_lines=list(recipe.get("ingredient_lines", [])),
                                              servings=recipe.get("servings"))
    except (TypeError, ValueError):
        return None
    kcal = counted.get("kcal_per_serving")
    return int(kcal) if kcal and kcal > profile.calories_per_meal * (1 + OVER_BUDGET) else None


def plan_meal(request: str, profile: UserProfile, data: Mapping[str, Any], model: str | None = None,
              write_recipe: RecipeWriter | None = None, max_retries: int = MAX_RETRIES,
              url: str | None = None) -> dict:
    """One meal plan: a recipe that passed the safety gate, its calories and where to buy its ingredients.

    Args:
        request: What the user asked for ("a Thai-style dinner").
        profile: The user's restrictions (from the app's form).
        data: Tables from agent_tools.load_agent_data.
        model: The Ollama model for the Chef (llm.choose_model); not needed with `write_recipe`.
        write_recipe: (request, problems) -> {"name", "servings", "ingredient_lines", "steps"}; default
            the CrewAI Chef. Tests pass a plain function.
        max_retries: Times a failed recipe goes back to the Chef.
        url: The Ollama address.

    Returns:
        {"recipe", "gate" (check_and_explain on the final recipe), "attempts" (each try's name, passed,
        problems), "fallback" (True when the Chef never passed and a recommended dish was used),
        "calories" (count_calories), "where_to_buy" (where_to_buy per ingredient), "seconds"}.
    """
    start = time.time()
    tools = {t.name: t for t in agent_tools(data, profile)}
    if write_recipe is None:
        if not model:
            raise ValueError("a model (llm.choose_model) or write_recipe is needed")
        write_recipe = chef_writer(list(tools.values()), profile, model, url)
    attempts: list[dict] = []
    problems: list[str] = []
    recipe: Mapping[str, Any] | None = None
    gate: dict = {}
    for _ in range(max_retries + 1):
        try:
            draft = write_recipe(request, problems)
        except (RuntimeError, ValueError) as error:   # the model failed to produce a recipe
            attempts.append({"name": None, "passed": False, "problems": [str(error)]})
            continue
        draft_gate = check_and_explain(list(draft.get("ingredient_lines", [])), draft.get("name", ""), profile)
        problems = [f"{p['line']} ({p['rule']})" for p in draft_gate["problems"]]
        kcal = _over_budget(draft, profile, tools) if draft_gate["passed"] else None
        attempts.append({"name": draft.get("name"), "passed": draft_gate["passed"], "problems": problems,
                         "kcal_per_serving": kcal})
        if not draft_gate["passed"]:
            continue
        recipe, gate = draft, draft_gate          # safe: keep it even if a lighter retry fails
        if kcal is None:
            break
        problems = [(f"one serving is about {kcal} kcal; make it about {profile.calories_per_meal:.0f} kcal "
                    "(smaller portions, less oil, cream and sugar, more servings)")]
    fallback = recipe is None
    if fallback and "recommend_recipes" in tools:
        countries = data["recipes"]["origin_country"].unique().tolist() if "origin_country" in data["recipes"] else []
        place = _origin(request, countries)
        ideas = tools["recommend_recipes"].run(country=place, how_many=1) if place else []
        ideas = ideas or tools["recommend_recipes"].run(how_many=1)
        if ideas:
            recipe = {"name": ideas[0]["name"], "servings": None, "ingredient_lines": ideas[0]["ingredients"],
                      "steps": [], "calories_per_serving": ideas[0]["calories"]}
            gate = check_and_explain(recipe["ingredient_lines"], recipe["name"], profile)
    result: dict[str, Any] = {"recipe": recipe, "gate": gate, "attempts": attempts, "fallback": fallback,
                              "calories": None, "where_to_buy": []}
    if recipe and not fallback and "count_calories" in tools:
        try:
            result["calories"] = tools["count_calories"].run(ingredient_lines=list(recipe["ingredient_lines"]),
                                                             servings=recipe.get("servings"))
        except (TypeError, ValueError) as error:
            result["calories"] = {"error": str(error)}
    if recipe and "where_to_buy" in tools and "recipes" in data:
        countries = data["recipes"]["origin_country"].unique().tolist() if "origin_country" in data["recipes"] else []
        place = _origin(request, countries)
        if place:
            for line in list(recipe["ingredient_lines"]):   # live: fish sauce was line 13
                try:
                    found = tools["where_to_buy"].run(ingredient=line, origin_country=place)
                except ValueError:
                    continue
                if found["home_brands"]:   # stores alone match any ingredient (a Thai market for rice)
                    result["where_to_buy"].append(found)
                if len(result["where_to_buy"]) == SOURCING_ITEMS:
                    break
    result["seconds"] = round(time.time() - start, 1)
    return result
