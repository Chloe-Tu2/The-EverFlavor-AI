# Planner

**Start here** (team members and AI assistants picking up the work). What is done, what is in progress, what comes
next, grouped by version, with links to the plans behind each item. Update it whenever an item moves.

Last updated: 2026-10-18 (Claude, with med27-coder).

## How versions work

Semantic versions, beta below 1.0 (the full convention is at the top of [CHANGELOG.md](../../CHANGELOG.md)):

| Change | Version step | Example |
|---|---|---|
| Fixes, wording, small style changes | PATCH | 0.5.1 → 0.5.2 |
| A new feature, kitchen, notebook or data source | MINOR | 0.5.2 → 0.6.0 |
| The first finished release (final presentation), later a breaking change | MAJOR | 0.x → 1.0.0 |

How a version moves, as most teams do it:

1. **Plan:** the items for the next version are listed below (this planner is the "milestone").
2. **Branch:** the work happens on `release/<version>` (or one branch per feature, merged into it).
3. **Review:** the team tries the branch (`git checkout release/<version>`, `python -m streamlit run app/app.py`)
   and says what needs rework.
4. **Release:** `/release` (Claude Code) or the steps in `.claude/commands/release.md`: the version number,
   `CHANGELOG.md` and the app's What's new notes (`app/updates.py`) are updated together (a test checks they
   agree), merged into `main`, tagged `vX.Y.Z` and published as a GitHub Release.

## Status

| Version | State | Branch |
|---|---|---|
| 0.5.1 | **In review** by the team | `release/0.5.1` |
| 0.6.0 | **Planned** (below) | `release/0.6.0`, opened after 0.5.1 is merged |
| 1.0.0 | Final presentation | |

### 0.5.1 (in review)

The first numbered release: everything up to now. Details in [CHANGELOG.md](../../CHANGELOG.md).

- The EverFlavor Kitchen front end, the What's new bell, the concept sheet's layout.
- Cuisine kitchens (code-drawn drafts): Japanese, **Chinese**, Mediterranean, Mexican, Middle Eastern, **Moroccan**
  (the African family). Searching a cuisine family opens its kitchen.
- Recipe photo credits and the no-photo placeholder.
- Guards for keys and user data; `CLAUDE.md`.

### 0.6.0 (planned)

Everything we are working on or have agreed to do next, in one place. Owners are filled in when someone takes an item.

| # | Item | Plan | Owner | State |
|---|---|---|---|---|
| 1 | **The team's own art** in the detailed concept style: kitchens and chefs dropped into `design/pixel-art/originals/`, objects mapped so they still move when tapped | [originals/README.md](../../design/pixel-art/originals/README.md) | team (art), Claude (mapping) | waiting for the pictures |
| 2 | **Regional kitchens:** art briefs for all regions; next kitchens Indian and Italian (most recipes) | [REGIONAL_KITCHENS.md](REGIONAL_KITCHENS.md) | | planned |
| 3 | **Kitchen by country, not only by family:** an Indian dish should open the Indian kitchen, not the Chinese one | [REGIONAL_KITCHENS.md](REGIONAL_KITCHENS.md#choosing-the-kitchen) | | planned |
| 4 | **Photo checks:** report-a-wrong-photo button, automatic image-text check, broken-link check | [RELIABILITY.md](RELIABILITY.md#2-recipe-photos) | | planned |
| 5 | **Fewer hallucinations** in the AI's explanations and the meal planner (grounding, more evaluation questions) | [RELIABILITY.md](RELIABILITY.md#1-hallucinations) | | planned |
| 6 | **UI round 2:** profile chips and the chef's three-question onboarding, "Why it's safe for you" on every card, Today's safe picks, faster first load, "How we check" page | [design/PLAN.md](../../design/PLAN.md#next-round-060) | | planned |
| 7 | **Local AI on this PC's NPU** (Foundry Local): time qwen2.5-7b and qwen3-4b against llama3.2 on notebook 09's questions; add as an option in `llm.py` if faster and as safe | [RELIABILITY.md](RELIABILITY.md#3-the-ai-models) | Claude | models downloaded |
| 8 | **Back-end fixes from the team's merge:** the inverted "vegan" line in `passes_safety_filter` (dead code today) and the dropped diet pre-filter (fewer results for halal and kosher searches) | [RELIABILITY.md](RELIABILITY.md#4-known-code-issues) | | to do |
| 9 | **README numbers:** the freshness models' final test results (fish 87.4%, produce 98.8%) in the main README | `notebooks/05` | | to do |
| 10 | **Freshness per-source check:** Fish Eyes FFE photos score 0.76 against 0.97 for the other fish source | [RELIABILITY.md](RELIABILITY.md#3-the-ai-models) | | planned |
| 11 | **Housekeeping:** move the Foundry agent folder (`my-agent-n6agvd/`) out of the repository folder | | med27-coder | to do |

### Follow-up for the next session (2026-10-22)

1. **Bug report** (`EverFlavor_AI_Kitchen_Bug_Report.pdf`, the live demo site): four bugs analysed, fixes proposed,
   waiting for the team's choice. Same recipes every time (sorting by calorie distance only: add variety, memory of
   shown recipes, rename "Other"); wrong cuisines (the demo data's own site tags: run it through notebook 01's
   country logic, drop conflicts, show the country); Food Network logo photos (find shared pictures by fingerprint);
   "N/A minutes" (the demo data has no time column: hide unknown times, bring times from the full data).
2. **Concept kitchens** (`design/pixel-art/concept_kitchens.py`): the four full kitchens drawn in code; rugs now
   stay on the rug. Still wrong: plants (a fan-of-leaves version is in `drafts/concept-kitchens/wip/`), rug
   patterns, perspective (the window sits flat instead of on the side wall), chairs. **Next approach (agreed):**
   isolate each object in the original, trace its outline and pixels at its real angle, then assemble the objects
   into the final kitchen (`design/pixel-art/trace_kitchens.py`).

### Later (1.0 and after)

Hosting and a landing page; My cookbook and sharing; the chef chat tab (`llm.ask_agent`); the meal planner in the
app (`crew.plan_meal`); achievements; animated kitchens (steam, the chef blinking); a phone-first redesign. See
[design/PLAN.md](../../design/PLAN.md) for the reasons and order.

## Handoff notes (for whoever picks this up)

- Read [CLAUDE.md](../../CLAUDE.md) first: the rules that must not be broken (keys, user data, safety decisions in the
  back end, flags only add cautions).
- Run every check before a push (CLAUDE.md lists them; CI runs the same).
- Front-end work: check it in a real browser, not only with Streamlit's test runner; Streamlit 1.65 changed several
  element names (tabs, cards, tags), and CSS that targets the old names silently does nothing.
- Pixel art: drawn in code (`design/pixel-art/make_pixel_art.py`, `cuisine_kitchens.py`); the team's own pictures in
  `originals/` take priority. Archive a picture before replacing it (`design/pixel-art/archive/`).
- Data and AI: [RELIABILITY.md](RELIABILITY.md) lists what can go wrong and what each fix costs.
