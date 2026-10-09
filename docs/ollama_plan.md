# Local Models With Ollama: Plan

How the agents run on a free local model in VS Code and Antigravity, without touching Colab.
Code: `src/everflavor/llm.py`; tests: `tests/test_llm.py` (fake answers, no Ollama needed).

## Why

- **Free:** no API key, no cost per message.
- **Private:** the user's allergies and diets never leave the computer.
- **Same safety:** the model only proposes; `safety.check_recipe` decides, and the model cannot change the
  user's restrictions (the profile comes from the code, not from the model's tool arguments).

## Where it runs

| Environment | Ollama | What the agents use |
|---|---|---|
| VS Code / Antigravity, Ollama running | Yes | Local model (`pick_model`) |
| VS Code / Antigravity, Ollama not running | No | Hosted model if a key is in `config/.env`, else rule-based tools |
| Colab | Never checked | Hosted model if a key is in Colab Secrets, else rule-based tools |

`ollama_status()` never raises: in Colab it answers "not available" without making a request, so no
notebook or Colab run can fail because of Ollama. The notebooks do not import `llm.py`.

## Setup (once per computer)

1. Install Ollama: <https://ollama.com/download> (Windows, macOS, Linux; Windows on ARM included).
2. Download a model that can call tools: `ollama pull granite4.1:3b` (about 2 GB).
3. Check: `ollama list`, then in Python:

   ```python
   from everflavor.llm import ollama_status, pick_model
   status = ollama_status()
   print(status["available"], status["tool_models"], pick_model(status))
   ```

Optional: set `OLLAMA_HOST` (as Ollama itself reads it) when Ollama runs on another address.

## Models

Only models tagged **tools** on <https://ollama.com/search?c=tools> can be agents. Checked October 2026
on a 16 GB Windows ARM laptop (CPU only):

| Model | Size | Tools | Live test (3 recipes, safety tool) | Time per answer |
|---|---|---|---|---|
| `granite4.1:3b` (default) | 2.1 GB | Yes | 3 of 3 right, tool called every time | 10-21 s |
| `llama3.2` (3B) | 2.0 GB | Yes | 3 of 3 right, tool called every time | 10-22 s |
| `tev1:4b` | about 3 GB | Yes | not tested yet | |
| `granite4.1:8b` | about 5 GB | Yes | not tested; slower, needs a GPU or patience | |
| `gemma3:4b` | 3.3 GB | **No** (vision only) | cannot call tools: not usable as an agent | |

Small models send lists as text (`'["rice"]'`) and invent extra arguments (`"avoid": ["peanuts"]`):
`tool_arguments` decodes the text and the safety tool ignores extra arguments.

## Steps

| # | Step | Status |
|---|---|---|
| 1 | `llm.py`: status, model choice, chat, tool loop, safety tool | Done (8 tests, live test 6 of 6) |
| 2 | The other agent tools as `Tool`s: recommend, calories, where to buy, substitutions | Next (roadmap step 3) |
| 3 | Choose the model in one place: Ollama, else hosted key, else rule-based | Next |
| 4 | CrewAI agents on the same choice (`LLM(model="ollama/granite4.1:3b", base_url=ollama_url())`) | Roadmap step 6 |
| 5 | Starter app: show which model answered, and always show the gate's result, not the model's words | After 3 |
| 6 | Evaluation: the same recipe set on each model; tool-call rate, gate agreement, time | Roadmap step 7 |

## What goes on GitHub

- **Yes:** `llm.py`, its tests, this plan.
- **No:** the models (2-5 GB each, downloaded with `ollama pull`), Ollama itself, and `config/.env`.
  Ollama needs no key, so there is nothing secret to store or encrypt.
