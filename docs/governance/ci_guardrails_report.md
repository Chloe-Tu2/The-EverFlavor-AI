# CI guardrails (2026-11-22)

Which of the seven guardrails the brief names actually run on GitHub for every push, checked by Claude (AI)
against `.github/workflows/` and `tests/`. Nothing in the workflows was changed.

| Guardrail | Runs in CI? | Where | Fails the build? |
|---|---|---|---|
| Secret scanning | yes | `security.yml`: `scripts/governance/secret_scan.py`; `tests/test_governance.py` (every rule finds its kind, no tracked file holds one) | yes |
| PII scanning | the rules only | `tests/test_governance.py` checks the rules find e-mails, phones and coordinates; `scripts/governance/pii_scan.py` is run by hand and only reports | no: a match can be a public credit, so a person reads it |
| License compliance | no | `docs/governance/license_compliance.md` (a page, checked by people); `security.yml` dependency review checks the libraries' licences on pull requests | libraries only |
| Data provenance | yes | `tests/test_governance.py::test_every_data_file_records_its_provenance` | yes (source and date; the stricter licence, version and attribution fields are report only) |
| Taxonomy validation | yes | `tests/test_taxonomy.py` (the tree loads with no problem; every app country is in it), `tests/test_atlas.py` | yes |
| Graph validation | yes | `tests/test_food_graph.py`, and since 2026-11-22 `tests/test_maintenance_sprint.py` (no broken links in the built graph) | yes |
| Documentation validation | partly | `checks.yml`: PyMarkdown on `README.md`, `docs/` and the folder READMEs | yes, for the files it scans |

Also on every push: `pytest`, Ruff, mypy (`checks.yml`), known vulnerabilities in the locked libraries
(OSV-Scanner) and CodeQL. Actions are pinned to commits; Dependabot proposes updates.

## Gaps found (for the team; no workflow was changed)

1. **Ruff in CI does not read `scripts/`:** `checks.yml` runs `ruff check src tests notebooks app`. The audit and
   governance scripts are linted only on our machines (and by the pre-commit hook). Suggested: add `scripts`.
2. **PyMarkdown in CI does not scan the root `SECURITY.md` and `GOVERNANCE.md`.** Suggested: add both.
3. **No CI check that links in the docs point to files that exist.** A renamed report (for example
   `provenance_report.md`, now `data_provenance_report.md`) can leave a dead link. Today the only dead links are
   six in `docs/plans/README_0.7.1_draft.md`, written for the root where the draft will go. Suggested: a small
   test that skips drafts.
4. **License compliance is a page, not a check:** a new dataset can be added without a row in
   `license_compliance.md`. Suggested: a test that every source in `docs/sources.md` has a row there.
5. **The PII scan is not in CI** on purpose (credits name people); it should still run before each release
   (`docs/governance/release_checklist.md` lists it).
