# Changelog

Notable changes to EverFlavor AI, newest first, in the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
format with [semantic versions](https://semver.org/) (MAJOR.MINOR.PATCH):

- **PATCH** (0.5.1 → 0.5.2): fixes, small wording or style changes.
- **MINOR** (0.5.2 → 0.6.0): a new feature, notebook or data source.
- **MAJOR** (0.x → 1.0.0): the first finished release (planned for the final presentation); after that, a change
  that breaks how people use the app or the saved data.

Versions below 1.0 are the **beta**. The version lives in `src/everflavor/__init__.py` (`__version__`); the
notes people see in the app's "What's new" bell are in `app/updates.py`; `tests/test_version.py` checks that all
three agree. Each release is merged to `main`, tagged (`v0.5.1`) and published as a GitHub Release.

## [0.5.1] - 2026-10-18

The first numbered release (beta). It sums up the work since the project started in September 2026.

### Added

- **The EverFlavor Kitchen front end** (`app/`): a pixel-art kitchen you can touch (curtains close, jars shake,
  the pot puffs steam), a pixel chef who reads out every result, pixel icons instead of emoji, four color themes
  (Classic is the team's original palette), real food photos in the recipe cards, a disclaimer and contributor
  footer, and a "What's new" bell for updates. Design notes, art generator and references in `design/`.
- **Data pipelines** (notebooks 01-09): recipes from several sources with allergen and diet flags, USDA nutrition,
  Open Food Facts hidden allergens, ingredient features, food freshness from photos (models for produce and fish),
  recipe variants, seasons and footprint, and the evaluation of the local AI agents.
- **The back end** (`src/everflavor/`): the calorie calculator, the safety gate, local models through Ollama, five
  agent tools, the answer guard, the CrewAI meal planner, and 200+ red-team checks.
- **Guards for keys and user data**: a Claude Code hook and a git pre-commit hook refuse to commit `config/.env`,
  key files or user data (`.claude/hooks/`); project rules in `CLAUDE.md`.

### Changed

- Readable pixel fonts (Jersey 10 and VT323) replace the first pixel font, whose letters and numbers were hard to read.
- Clicks in the app update the page in about 0.05 s instead of 1.5 s.

### Fixed

- On computers in dark mode, the app showed white text on its cream background.
- Chosen allergy and diet tags, and the recipe cards, were not styled in Streamlit 1.65.

[0.5.1]: https://github.com/Chloe-Tu2/The-EverFlavor-AI/releases/tag/v0.5.1
