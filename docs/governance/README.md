# Governance

How EverFlavor is kept safe to publish and easy to maintain as a public project: what data may be public, who
approves what, licences, releases, and the scans that guard secrets and personal data.

| Page | What it answers |
|---|---|
| [public_data_policy.md](public_data_policy.md) | What may be in the repository, what needs review, what never may |
| [human_approval_workflow.md](human_approval_workflow.md) | What an AI may do alone, what needs one person, what needs two, and when to stop |
| [license_compliance.md](license_compliance.md) | What each kind of licence among our sources lets us do, and the open licence questions |
| [release_checklist.md](release_checklist.md) | What to tick before a release |
| [sprint_review_checklist.md](sprint_review_checklist.md) | What every atlas sprint passes before its merge: coverage, representation, enrichment, validation, sources, repository |
| [needs_human_review.md](needs_human_review.md) | The open questions waiting for a person |
| [indigenous_review.md](indigenous_review.md) | The rubric for Indigenous food tradition tags: what the code checks, what a person checks, what the app may say |
| [multi_origin_dish_policy.md](multi_origin_dish_policy.md) | How a dish with several countries of origin counts (every source-backed origin), what counts as evidence, and what a person decides |
| [secret_scan_report.md](secret_scan_report.md) | The latest secret scan (written by the script) |
| [pii_audit_report.md](pii_audit_report.md) | The latest personal-data audit (written by the script) |
| [data_provenance_report.md](data_provenance_report.md) | Whether every data file says its source, licence and date (the tests fail on a gap) |
| [readme_improvement_report.md](readme_improvement_report.md) | What the main README answers well and what it lacks |
| [repository_hygiene_report.md](repository_hygiene_report.md) | Tracked files that look temporary, debug, draft or stale (written by the script) |
| [documentation_gap_report.md](documentation_gap_report.md) | Which pages lack purpose, inputs, outputs or owner, and where each report of the maintenance brief lives |
| [ci_guardrails_report.md](ci_guardrails_report.md) | Which guardrails run in CI, and the gaps |

- **Inputs:** every tracked file (the scans); `docs/sources.md` (licences).
- **Outputs:** the reports above; the secret scan's exit code, which fails CI on any finding.
- **Scripts:** `scripts/governance/secret_scan.py`, `pii_scan.py`, `provenance_audit.py`, `hygiene_audit.py` (tests:
  `tests/test_governance.py`).
- **Ownership:** the team (EverGlow); the policies here are proposed until the team confirms them.
- **Future work:** a licence check of each image file in CI, a broken-link check of the docs, and
  CODEOWNERS once the team assigns folders.
