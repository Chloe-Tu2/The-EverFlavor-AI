"""Tests for the Ollama helpers (src/everflavor/llm.py) with fake answers: no Ollama needed.

Run with `python -m pytest tests`, or alone:

    python tests/test_llm.py
"""
import json
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor import llm
from everflavor.safety import UserProfile


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data


def fake_ollama(monkeypatch, replies=(), capabilities=None):
    """Answer like Ollama: /api/version, /api/tags, /api/show, then `replies` for /api/chat."""
    capabilities = capabilities or {"llama3.2:latest": ["completion", "tools"], "gemma3:4b": ["completion"]}
    replies, sent = list(replies), []

    def get(url, timeout):
        if url.endswith("/api/version"):
            return FakeResponse({"version": "0.40.2"})
        return FakeResponse({"models": [{"name": n} for n in capabilities]})

    def post(url, json, timeout):
        if url.endswith("/api/show"):
            return FakeResponse({"capabilities": capabilities[json["model"]]})
        sent.append(json)
        return FakeResponse({"message": replies.pop(0)})

    monkeypatch.setattr(llm, "_in_colab", lambda: False)
    monkeypatch.setattr(llm.requests, "get", get)
    monkeypatch.setattr(llm.requests, "post", post)
    return sent


def test_status_lists_tool_models_and_picks_one(monkeypatch):
    fake_ollama(monkeypatch)
    status = llm.ollama_status()
    assert status["available"] and status["version"] == "0.40.2"
    assert status["tool_models"] == ["llama3.2:latest"]
    assert llm.pick_model(status) == "llama3.2:latest"
    assert llm.pick_model({"tool_models": []}) is None


def test_status_is_an_answer_not_an_error(monkeypatch):
    monkeypatch.setattr(llm, "_in_colab", lambda: True)
    assert "Colab" in llm.ollama_status()["reason"]

    def refuse(url, timeout):
        raise requests.ConnectionError("refused")

    monkeypatch.setattr(llm, "_in_colab", lambda: False)
    monkeypatch.setattr(llm.requests, "get", refuse)
    status = llm.ollama_status("http://localhost:1")
    assert not status["available"] and "not running" in status["reason"]

    fake_ollama(monkeypatch, capabilities={"gemma3:4b": ["completion"]})
    status = llm.ollama_status()
    assert not status["available"] and "ollama pull" in status["reason"]


def test_ollama_url_reads_ollama_host(monkeypatch):
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    assert llm.ollama_url() == llm.OLLAMA_URL
    monkeypatch.setenv("OLLAMA_HOST", "0.0.0.0:11434")
    assert llm.ollama_url() == "http://localhost:11434"


def test_tool_arguments_decode_lists_sent_as_text():
    call = {"function": {"arguments": {"recipe_name": "Bowl", "ingredient_lines": '["rice", "satay sauce"]'}}}
    assert llm.tool_arguments(call) == {"recipe_name": "Bowl", "ingredient_lines": ["rice", "satay sauce"]}
    assert llm.tool_arguments({"function": {"arguments": '{"a": 1}'}}) == {"a": 1}
    assert llm.tool_arguments({"function": {"arguments": "not json"}}) == {}


def test_safety_tool_takes_the_profile_from_code_not_the_model():
    tool = llm.safety_tool(UserProfile(avoid=("contains_peanut",)))
    assert not tool.run(recipe_name="Bowl", ingredient_lines=["2 cups rice", "3 tbsp satay sauce"])["passed"]
    # the model trying to change the restrictions has no effect
    assert not tool.run(recipe_name="Bowl", ingredient_lines="3 tbsp peanut butter", avoid=[])["passed"]
    assert tool.schema()["function"]["name"] == "check_recipe"


def test_run_tools_calls_the_gate_and_returns_the_answer(monkeypatch):
    call = {"function": {"name": "check_recipe",
                         "arguments": {"recipe_name": "Thai Bowl", "ingredient_lines": '["3 tbsp satay sauce"]'}}}
    sent = fake_ollama(monkeypatch, replies=[{"role": "assistant", "content": "", "tool_calls": [call]},
                                             {"role": "assistant", "content": "Not safe: satay sauce."}])
    result = llm.run_tools([{"role": "user", "content": "Is it safe?"}], "llama3.2:latest",
                           [llm.safety_tool(UserProfile(avoid=("contains_peanut",)))])
    assert result["answer"] == "Not safe: satay sauce."
    assert result["calls"][0]["result"]["passed"] is False
    tool_message = sent[1]["messages"][-1]
    assert tool_message["role"] == "tool" and json.loads(tool_message["content"])["passed"] is False


def test_run_tools_survives_unknown_tools_and_stops(monkeypatch):
    loop = {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "nope", "arguments": {}}}]}
    fake_ollama(monkeypatch, replies=[loop, loop])
    result = llm.run_tools([{"role": "user", "content": "hi"}], "m", [], max_rounds=2)
    assert result["answer"] == "" and "unknown tool" in result["calls"][0]["result"]["error"]
    with pytest.raises(ValueError):
        llm.run_tools([], "m", [], max_rounds=0)


def test_chat_reports_ollama_errors(monkeypatch):
    monkeypatch.setattr(llm.requests, "post", lambda url, json, timeout: FakeResponse({"error": "model not found"}))
    with pytest.raises(RuntimeError, match="model not found"):
        llm.chat([{"role": "user", "content": "hi"}], "missing")


def test_the_verdict_comes_from_the_code_and_passed_recipes_skip_the_model(monkeypatch):
    sent = fake_ollama(monkeypatch, replies=[])
    peanut = UserProfile(avoid=("contains_peanut",))
    report = llm.check_and_explain(["2 cups rice", "1 lemon"], "Lemon Rice", peanut, model="llama3.2:latest")
    assert report["passed"] and report["explained_by"] == "rules" and sent == []   # no model call for a pass
    assert "fits your profile" in report["text"]


def test_a_faithful_explanation_is_kept_and_an_unfaithful_one_replaced(monkeypatch):
    peanut = UserProfile(avoid=("contains_peanut",))
    lines = ["2 cups rice", "3 tbsp satay sauce"]
    fake_ollama(monkeypatch, replies=[{"role": "assistant", "content": "Avoid it: the satay sauce breaks your peanut rule."}])
    good = llm.check_and_explain(lines, "Satay Bowl", peanut, model="llama3.2:latest")
    assert not good["passed"] and good["explained_by"] == "llama3.2:latest" and "satay" in good["text"]
    for words in ["This recipe looks great, enjoy!",                              # no warning
                  "It is not safe because of the rice.",                          # names the wrong cause
                  "It breaks the pet meat rule because of the satay sauce."]:     # names a rule it did not break
        fake_ollama(monkeypatch, replies=[{"role": "assistant", "content": words}])
        bad = llm.check_and_explain(lines, "Satay Bowl", peanut, model="llama3.2:latest")
        assert bad["explained_by"] == "rules" and bad["model_text"] == words
        assert bad["text"] == "Satay Bowl does not fit your profile: 3 tbsp satay sauce (peanut: satay sauce)."


def test_ollama_failing_falls_back_to_the_plain_text(monkeypatch):
    def broken(url, json, timeout):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(llm.requests, "post", broken)
    report = llm.check_and_explain(["3 tbsp satay sauce"], "Bowl", UserProfile(avoid=("contains_peanut",)), model="m")
    assert not report["passed"] and report["explained_by"] == "rules"


def test_choose_model_falls_back_to_rules(monkeypatch):
    fake_ollama(monkeypatch)
    assert llm.choose_model() == {"kind": "ollama", "model": "llama3.2:latest", "reason": ""}
    monkeypatch.setattr(llm, "_in_colab", lambda: True)
    choice = llm.choose_model()
    assert choice["kind"] == "rules" and choice["model"] is None and "Colab" in choice["reason"]


def test_recommend_tool_keeps_the_profile_whatever_the_model_asks():
    import pandas as pd
    recipes = pd.DataFrame({
        "recipe_name": ["peanut noodles", "lemon rice", "pork belly"],
        "cuisine_family": ["Asian", "Asian", "Asian"],
        "ingredient_list": [["noodles", "peanuts"], ["rice", "lemon"], ["pork belly", "soy sauce"]],
        "calories_per_serving": [500.0, 450.0, 520.0], "nutrition_plausible": [True] * 3,
        "contains_peanut": [True, False, False], "contains_pork": [False, False, True],
        "vegetarian": [True, True, False], "vegan": [True, True, False], "contains_gluten": [True, False, True]})
    tool = llm.recommend_tool(recipes, UserProfile(avoid=("contains_peanut", "contains_pork")))
    found = tool.run(cuisine="Asian", calories="500", how_many="9", avoid=[])   # the model tries to drop the rules
    assert [d["name"] for d in found] == ["lemon rice"]
    assert tool.schema()["function"]["parameters"]["properties"]["cuisine"]["enum"] == ["any", "Asian"]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
