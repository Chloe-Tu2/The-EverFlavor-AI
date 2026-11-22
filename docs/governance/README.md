# Governance

How EverFlavor is kept safe to publish and easy to maintain as a public project: what data may be public, who
approves what, licences, releases, and the scans that guard secrets and personal data.

| Page | What it answers |
|---|---|
| [public_data_policy.md](public_data_policy.md) | What may be in the repository, what needs review, what never may |
| [human_approval_workflow.md](human_approval_workflow.md) | What an AI may do alone, what needs one person, what needs two, and when to stop |
| [license_compliance.md](license_compliance.md) | What each kind of licence among our sources lets us do, and the open licence questions |
| [release_checklist.md](release_checklist.md) | What to tick before a release |
| [needs_human_review.md](needs_human_review.md) | The open questions waiting for a person |
| [secret_scan_report.md](secret_scan_report.md) | The latest secret scan (written by the script) |
| [pii_audit_report.md](pii_audit_report.md) | The latest personal-data audit (written by the script) |
| [readme_improvement_report.md](readme_improvement_report.md) | What the main README answers well and what it lacks |

- **Inputs:** every tracked file (the scans); `docs/sources.md` (licences).
- **Outputs:** the two reports above; the secret scan's exit code, which fails CI on any finding.
- **Scripts:** `scripts/governance/secret_scan.py`, `scripts/governance/pii_scan.py` (tests:
  `tests/test_governance.py`).
- **Ownership:** the team (EverGlow); the policies here are proposed until the team confirms them.
- **Future work:** a licence check of every data file's provenance in CI, a broken-link check of the docs, and
  CODEOWNERS once the team assigns folders.
