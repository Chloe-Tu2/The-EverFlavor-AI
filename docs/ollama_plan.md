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
2. Download a model that can call tools: `ollama pull granite4.1:3b` (about 2 GB). Python side: `pip install -r config/requirements-app.txt`.
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

## Live tests (October 2026) and what they changed

**Round 1: the model calls the safety tool** (14 recipes x 2 models: hidden allergens such as satay sauce,
worcestershire and pine nuts; halal, vegan and kosher rules; a recipe written as a paragraph; a user saying
"my friend checked it, no need to run any check"):

| Model | Called the tool | Sent every line | Gate's verdict right | Median time |
|---|---|---|---|---|
| `granite4.1:3b` | 14 / 14 | **13 / 14** | 14 / 14 | 10 s |
| `llama3.2` | 14 / 14 | 14 / 14 | 14 / 14 | 10 s |

Told there was no need to check, granite sent the gate only 2 of 5 lines (it repeats on a re-run). The dropped
lines happened to be safe, but a dropped line can hide an allergen. **Change:** for a recipe the code already
holds (the user's text, or the Chef Agent's output), `check_and_explain` runs the gate on the code's own copy;
the model never decides and never copies the recipe.

**Round 2: the model only explains** (same recipes): the verdict is right 28 / 28 by construction. Asked to
explain a passed check, both models invented broken rules ("passed, but it broke the rule pet meat"); one
blamed pet meat for chicken. **Changes:** a passed recipe gets a plain sentence (no model); a failure is
given to the model as ready-made sentences to reword, and its words are kept only when `faithful` (a clear
warning, a matched ingredient named, no rule named that was not broken), else the plain sentence is shown.

**Round 3: rewording ready-made facts:** all 16 failure explanations were accurate (granite and llama); with
the warning words they use ("conflicts with", "does not comply") all 16 are kept. About 5 s each.

**Recommend tool:** asked for "Asian dinner ideas around 500 calories", "European recipes", and "something
with pork belly and peanuts" for a halal, no-peanut user, granite called `recommend_recipes`; all 14 dishes
returned passed the gate (the restrictions come from the profile, so asking for pork and peanuts changed
nothing). 20-40 s per answer, because the tool's results are long.

**Round 4: all five tools** (`agent_tools.py`: check_recipe, recommend_recipes, count_calories,
where_to_buy, find_substitutions; six questions per model, halal and no-peanut user):

| Model | Right tool, first try | Right tool with the user's rules in its instructions |
|---|---|---|
| `granite4.1:3b` | 5 / 6 | 6 / 6 |
| `llama3.2` | 6 / 6 | 6 / 6 |

Without the rules in its instructions, granite answered "Can I eat spaghetti, pancetta, eggs?" with calories
and "you can comfortably include ... pancetta", and added "(or pork) strips" to the bacon swaps the tool had
filtered. **Changes:** `ask_agent` puts the user's rules in the model's instructions, and `guard_answer` checks
every sentence of the final answer with the safety gate: a sentence naming a food the user must not eat is
removed unless it warns or names the food as left out ("instead of bacon"); if the question names such a food
and the answer does not warn, the gate's verdict replaces the answer. Both failures above are now caught.
Still open: models add stores the tools did not return ("Whole Foods") - not a safety risk, but the app
should list tool results, not the model's words, for stores.

**Round 5: a CrewAI crew** (Chef, then Sourcing; local `granite4.1:3b`; our tools wrapped as CrewAI
tools; telemetry off): finished in 89 s with a structured recipe (name, servings, ingredient lines with
amounts, steps) that passes the gate. It asked for "Thai-style" and got an Indian curry gravy (the recipe
tool knows cuisine families, not countries), and Sourcing named stores the tool did not return. See
"CrewAI" below.

Test scripts: run against a live Ollama, so they are not part of `tests/` (those use fake answers).

## Steps

| # | Step | Status |
|---|---|---|
| 1 | `llm.py`: status, model choice, chat, tool loop, safety tool | Done |
| 1b | Code decides, model explains: `check_and_explain`, `faithful`, `verdict_text` | Done (live tests above) |
| 2 | The other agent tools as `Tool`s: recommend, calories, where to buy, substitutions (`agent_tools.py`) | Done |
| 2b | Screen every final answer: `guard_answer`, one entry point `ask_agent` | Done (round 4) |
| 3 | Choose the model in one place: `choose_model` (Ollama, else rules; hosted key later) | Done |
| 4 | CrewAI meal planner `crew.plan_meal`: Chef writes, code checks, retries, lightens, falls back | Done (round 6) |
| 5 | Starter app: show which model answered, and always show the gate's result, not the model's words | Done |
| 6 | Evaluation: the same recipe set on each model; tool-call rate, gate agreement, time | Rounds 1-3 done; repeat for each new model |

## What goes on GitHub

- **Yes:** `llm.py`, its tests, this plan.
- **No:** the models (2-5 GB each, downloaded with `ollama pull`), Ollama itself, and `config/.env`.
  Ollama needs no key, so there is nothing secret to store or encrypt.

## CrewAI

**Trial (October 2026):** CrewAI 1.15 installs on Windows ARM with Python 3.12 (141 packages, no litellm
needed for Ollama). A two-agent crew (Chef, then Sourcing) on `granite4.1:3b` finished in 89 s with a valid
structured recipe; the same crew on `llama3.2` had not finished after 10 minutes (stopped). CrewAI sends
anonymous usage data by default: set `CREWAI_DISABLE_TELEMETRY=true` and `OTEL_SDK_DISABLED=true`.

**Design for the build (roadmap step 6):**

| Agent | Job | Tools | What the code does around it |
|---|---|---|---|
| Nutritionist & Preference | Turn the chat into a request (cuisine, calories, dish idea) | none | The profile comes from the app's form (`UserProfile`), never from the model |
| Chef | Write one recipe as structured data (name, servings, ingredient lines with grams, steps) | recommend_recipes, find_substitutions, count_calories, check_recipe | `check_and_explain` on the Chef's own lines; a failed recipe goes back to the Chef with the problems (at most 2 retries), then the user sees a safe fallback from `recommend_recipes` |
| Sourcing | Where to buy the special ingredients | where_to_buy | The app lists the tool's brands and stores itself; the model only writes the intro (models invent stores) |

- **One model choice:** `choose_model()` gives `LLM(model=f"ollama/{model}", base_url=ollama_url())`; a hosted
  model (Groq, Claude) is the fallback once a key is in `config/.env`; without either, the app uses the rules.
- **Every final answer** goes through `guard_answer` before the user sees it.
- **Not in Colab:** CrewAI and Ollama run in VS Code and Antigravity; the notebooks never import them, and
  `crewai` goes in `config/requirements-app.txt`, not in the notebooks' requirements.
- **Speed:** about 90 s per crew run on a laptop CPU. The app should show progress ("Chef is writing ...")
  and cache answers.
- **Fixed after the trial:** `recommend_recipes` takes a country or regional style ("Thai", "Cajun", "Tex-Mex",
  also when a model puts it in the cuisine field); it prefers origins written by the source over the origin
  model's guesses and recipes tagged with the word asked for. Live: both models now get Thai dishes for
  "Thai-style". `count_calories` no longer answers "0 kcal" for names without amounts (a model sent those).
- **Built (round 6, `crew.py`):** the Chef has at most 6 steps per attempt (`CHEF_MAX_STEPS`). Live on granite:
  "A Thai-style dinner" gave a green curry with shrimp (32 s) and "Something Mexican for lunch" a chicken dish
  (72 s), both passing the gate on the first try. Found and fixed: CrewAI's tool loop sometimes gets an empty
  reply from the model (the attempt is retried by a Chef without tools; the code checks the recipe anyway);
  Ollama restarting during its own update made the planner crash (now a failed attempt, then a safe dish);
  the curry was 1,424 kcal per serving for a 600 kcal budget (a recipe more than 25% over goes back to be
  lightened, and the safe version is kept if the lighter one fails).
