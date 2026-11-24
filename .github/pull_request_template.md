## Summary

What changed and why, in two or three plain sentences.

## Checklist

- [ ] The same checks as CI pass locally: `python -m pytest -q`, `ruff check src tests notebooks app scripts`,
      `mypy --config-file config/mypy.ini`, and the PyMarkdown scan in `CLAUDE.md`
- [ ] The app starts (`python -m streamlit run app/app.py`) with no exception, when the app changed
- [ ] No secrets, user data (`data/user/`, `logs/`), personal emails, PC paths or local-only plans in the diff
- [ ] Safety decisions still come from the back end (`src/everflavor`); diet labels say "-friendly"
- [ ] New facts, dishes and images keep their source and licence; nothing invented
- [ ] Judgment calls added to `docs/governance/needs_human_review.md` with who decided
- [ ] README, folder READMEs and CHANGELOG `[Unreleased]` updated; numbers match the latest run
- [ ] No emojis in files, commits or this description
- [ ] For an atlas sprint: `docs/governance/sprint_review_checklist.md` and `docs/audits/sprints/sprint_N_impact.md`

## Needs a person

Anything a reviewer must decide or check by eye.
