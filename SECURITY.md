# Security

## Reporting a problem

Please do not post the details of a security problem or a leaked secret in a public issue. Open an issue that
says only "Security report: please contact me", and a maintainer will reach you privately on GitHub to hear what
you found and where. (GitHub's private "Report a vulnerability" form is not switched on for this repository yet.)
We answer as soon as we can; this is a student project, so there is no bounty.

A food-safety problem (a recipe shown as safe for an allergy it is not safe for) counts as a security problem:
report it the same way.

## What protects the project

- **Secrets** live only in `config/.env` (git-ignored) or Colab Secrets, never in a file git tracks. The pre-commit
  hook refuses to commit secret files and user data, and `scripts/governance/secret_scan.py` reads every tracked
  file for keys and tokens on every push and pull request (CI fails on a finding).
- **User data** (profiles, chat history, audit logs) is never committed, and the audit log never records what a
  person typed (`docs/ethics_privacy.md`).
- **Libraries** are pinned (`config/requirements.lock`) and checked against known vulnerabilities by
  `osv-scanner` and Dependabot; CodeQL reads the code.
- **Safety decisions** (allergies, diets) come from the back end only, and a change to them needs two people
  (`docs/governance/human_approval_workflow.md`).

See [docs/governance/](docs/governance/README.md) for the data policy, the approval workflow and the latest scans.
