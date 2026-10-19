# Reliability: Hallucinations, Photos and the AI Models

What can go wrong between the data and what a person reads on the page, what already protects them, and the options
for 0.6.0 with their pros and cons. Part of the [planner](README.md).

## What is already in place

- **The rules decide, the AI only explains.** The safety gate (`safety.check_recipe`) and the recommender's final
  check read every ingredient line; a local model may only explain a failure, and its words are replaced by a plain
  sentence when they do not match the gate (`llm.check_and_explain`).
- **The answer guard** screens the agents' answers; 202 red-team checks run on every push; notebook 09 asks every
  local model the same 33 questions (13 of them attacks): 0 problems in 66 answers on the last run.
- **Labels say how sure they are:** estimated nutrition is marked `estimated`; predicted countries say "probably".
- **Photos** come from the recipe's own website (no AI makes or chooses them), with a credit that links there; a dish
  without a photo shows a placeholder.

## 1. Hallucinations

Where they can still happen: the local model's explanation of a problem, the agents' chat answers, and the meal
planner's recipes (all screened, but a screened answer can still be vague or wrong about a detail).

| Option | Pros | Cons |
|---|---|---|
| **Ground every answer in our data:** give the model the recipe lines and the gate's findings, and reject any answer that names a food that is not in them | Removes invented ingredients and invented reasons | More code in the guard; some correct general advice ("check the label") must stay allowed |
| **Structured answers** (JSON fields such as `line`, `rule`, `why`) checked field by field, then turned into sentences | Easy to verify; the wording stays friendly | Small local models sometimes break the format (needs a retry and the plain-sentence fallback) |
| **Bigger evaluation set:** multi-turn attacks, two or three restrictions at once, repeated runs, a usefulness score | Finds failures before users do; tracks progress per model | More run time (notebook 09 already takes a while on this PC) |
| **A bigger or newer model** (for example qwen2.5-7b on this PC's NPU through Foundry Local) | Usually fewer mistakes | Slower, more memory; must pass notebook 09 before it is used |
| **Say "I don't know"** (the prompt and the guard prefer no answer to a guess) | Safer | Less helpful on hard questions |
| **Fine-tune a model on our own answers** | Fits our tasks closely | Needs thousands of checked examples, a GPU, and re-testing; risky for a class project. Not now |

Recommended for 0.6.0: grounding, structured answers for explanations, and the bigger evaluation set.

## 2. Recipe photos

What happened: a photo that looked wrong (Bean Casserole: the recipe's own photo, bread baked on the beans) and a
dish with no photo (Poblano Posole: none in the data). The demo data has photos for 99% of its recipes; the full
data has none yet; and the photos' license is not recorded.

| Option | Pros | Cons |
|---|---|---|
| **Credit and link** (done) | Anyone can check the photo against the recipe page | Does not catch a wrong photo by itself |
| **"Wrong photo?" button** that hides the photo and saves only the recipe's id | Real people find real mistakes; cheap | Needs a small shared store and a review step; must save nothing about the person (privacy rules) |
| **Automatic image-text check:** a local model that scores how well a photo matches the dish name (for example CLIP), run once in a notebook; low scores get hidden or flagged | Checks thousands of photos at once | Unusual or homemade dishes may score low (Bean Casserole might); needs a hand-checked sample to choose the cutoff |
| **Broken-link check** in a notebook (each photo link answers?) | Removes empty frames | Sites change; needs a re-run before each release |
| **Pixel-art dish pictures** for dishes without a photo (a bowl for soups, a plate for mains) | Every card looks complete, in the app's style | Must be clearly an illustration, never passed off as the dish |
| **AI-generated food photos** | A photo for every dish | **Not recommended:** a made-up picture of a real recipe is a hallucination by design and can mislead about what the dish is |
| **Photos only from licensed sources** (TheMealDB, sources that allow reuse) | Safe to publish | Fewer photos |

Recommended for 0.6.0: the broken-link check, the "Wrong photo?" button, and the image-text check on a 200-photo
hand-checked sample before deciding on a cutoff. Confirm the demo photos' license before a public launch.

## 3. The AI models

| Model | Where it stands | Next |
|---|---|---|
| **Freshness from photos** (notebook 05) | Test split: fish 87.4%, produce 98.8%; 0.8% and 0.1% of spoiled photos called fresh. One fish source (Fish Eyes FFE) scores 0.76 against 0.97 | More FFE-style photos or source-aware weighting; meat and bread photos; the team's own photos as a final test |
| **Country of origin** (notebook 01) | About 89% right on validation; African and Middle Eastern recipes get confused (F1 0.33 and 0.35 for the baseline classifier) | More African recipes (CulinaryDB has 22 regions); predict the family first, then the country; show only confident predictions |
| **Restriction flags** (rules) | Hand-checked rounds: gluten 94%, dairy 95%, fish 93%, tree nuts 95% caught (round 4) | Keep adding review rounds; per-language word lists |
| **Local language models** (Ollama, `llm.py`) | llama3.2 default; 0 problems in 66 answers (notebook 09) | Time Foundry Local models on this PC's NPU and GPU; adopt one only if it passes notebook 09 |

## 4. Should regions be specialized?

The question: would separate models or rules per region (Asia, Africa, Europe...) lower hallucinations?

| Approach | Pros | Cons |
|---|---|---|
| **One shared model + regional knowledge** (local ingredient names, regional word lists for the flags, regional examples in the prompt) | Every region gains from all the data; one thing to test; matches how the flags already read foreign words | Rare regions can still be crowded out by common ones |
| **One model per region** | Each sees only its own labels (fewer African-vs-Middle-Eastern mix-ups) | Far less data each (African: 3,179 recipes; European: 48,151), so the small regions get worse; five things to train, test and keep in sync |
| **Two steps: family first, then country inside the family** | Targets exactly the confusion we see; small extra cost | Two models to keep; a wrong first step cannot be fixed by the second |
| **Regional evaluation sets** (questions and recipes from each region, checked by someone from there) | Shows where the AI is weak, region by region | Needs people to write and check them |

Recommendation: **keep one shared model, add regional knowledge, try the two-step classifier, and evaluate per
region.** Specialize only a region that has enough data and a measured problem that sharing cannot fix.

## 5. Known code issues

| Issue | Effect | Fix |
|---|---|---|
| `passes_safety_filter` has an inverted "vegan" branch (from the team's merge) | None today ("vegan" is never in the avoid list), but a trap | Remove the branch; add a test |
| The diet pre-filter was dropped from `baseline_recommend` | Halal or kosher searches can return fewer recipes than asked (the final check still removes unsafe ones) | Restore the pre-filter when the diet columns exist |
| The demo data has no African recipes | The Moroccan kitchen never opens on the demo deployment | Add African recipes to `data/demo/` |
| CSS targets Streamlit's element names, which change between versions | Styling silently disappears after an upgrade | Pin Streamlit's version; check in a browser after every upgrade |
