"""Local language model through Ollama (roadmap step 6: agents without an API key).

Ollama (https://ollama.com) runs open models on the user's own computer: free, and the
user's allergies and diets never leave the machine. It only exists in VS Code and
Antigravity on a computer where Ollama is installed and running; in Colab, or when it is
not running, `ollama_status` says so and the agents fall back to the rule-based tools
(recommend.py). Nothing here is imported by the notebooks, so Colab is never affected.

The model only proposes. Every tool that touches safety gets the user's profile from the
code (`safety_tool(profile)`), never from the model's arguments, and its answer comes from
`safety.check_recipe`, which the model cannot override.
"""
from __future__ import annotations

import json
import os
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
    "ollama_status",
    "ollama_url",
    "pick_model",
    "run_tools",
    "safety_tool",
    "tool_arguments",
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
