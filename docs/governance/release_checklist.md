# Release checklist

The steps of a release are in `.claude/commands/release.md` (`/release`); this is the list to tick before the
team approves one. A release needs a person's approval ([human_approval_workflow.md](human_approval_workflow.md)).

## Before

- [ ] All four CI checks pass locally and on GitHub: `pytest`, `ruff`, `mypy`, `pymarkdown` (`/check`).
- [ ] The secret scan finds nothing: `python scripts/governance/secret_scan.py --report`.
- [ ] The PII audit is read, and every new hit is public or removed: `python scripts/governance/pii_scan.py`.
- [ ] Every data source added since the last release is in `docs/sources.md`, with licence, credit and date, and
      allowed for our use ([license_compliance.md](license_compliance.md)).
- [ ] No photo is shown that was not checked by eye; every shown photo has its credit.
- [ ] Safety changes since the last release have two approvals and a policy row
      (`docs/flag_review/flag_policies.csv`).
- [ ] README numbers come from the latest full run; the folder READMEs are up to date.
- [ ] [needs_human_review.md](needs_human_review.md) has no open item that blocks this release.

## The release itself

- [ ] `__version__`, `CHANGELOG.md` and `app/updates.py` agree (`tests/test_version.py`).
- [ ] Release branch `release/X.Y.Z`, CI green, the team approves, merge, tag `vX.Y.Z`, GitHub Release.

## After

- [ ] Open the app from a clean clone (`python -m streamlit run app/app.py`) and look at a recipe, the map and the
      waiter.
- [ ] Move the planner's finished items to "done" (`docs/plans/README.md`).
