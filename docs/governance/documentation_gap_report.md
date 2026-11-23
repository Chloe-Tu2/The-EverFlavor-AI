# Documentation gaps (2026-11-22)

The pages the maintenance brief asks about, checked by Claude (AI): does each exist, and does it say purpose,
inputs, outputs, how to run, owner and future work? Also where each report the brief names lives, since several
already existed under another name.

## The pages

| Page | Exists | State | Gap |
|---|---|---|---|
| `README.md` | yes | "At a glance" answers the seven questions (`readme_improvement_report.md`) | "Current Status" is dated; 771 lines |
| `docs/README.md` | yes | an index of `docs/` | add `safety_engine.md` (done 2026-11-22) |
| `docs/governance/README.md` | yes | lists every governance page | the reports of 2026-11-22 added |
| `data/README.md` | yes | the folders and the files outside them | none found |
| `data/knowledge/README.md` | yes | the knowledge files | the new quality queues added |
| `notebooks/README.md` | yes | notebooks 01 to 15 | last changed 2026-11-19: check its numbers after the next full run |
| `src/everflavor/domain/README.md` | yes | purpose, inputs, outputs, dependencies, tests, owner, future work | none |
| `src/everflavor/safety/README.md` | **no folder** | the safety engine is `flags.py`, `safety.py`, `recommend.py` and others in `src/everflavor/` | written as [docs/safety_engine.md](../safety_engine.md); moving the code into a package is the team's call |
| `scripts/` | no README | each script says what it does in its docstring | a short `scripts/README.md` listing them by folder (suggested) |
| `CONTRIBUTING.md` | yes, at `docs/CONTRIBUTING.md` | linked from the README | GitHub looks in the root, `docs/` or `.github/`, so it is found |

## Where the brief's reports are

| The brief asks for | Our file |
|---|---|
| `secret_scan_report.md`, `pii_audit_report.md` | `docs/governance/` |
| `repository_hygiene_report.md` | `docs/governance/` (new) |
| `data_provenance_report.md` | `docs/governance/` (was `provenance_report.md`) |
| `dish_quality_report.md` | `docs/audits/` (the score's weights: see below) |
| `rich_dish_upgrade_queue.json`, `walter_enrichment_queue.json` | `data/knowledge/quality/` (new), summed up in `docs/audits/dish_enrichment_queues.md` |
| `image_coverage_report.md` | `docs/audits/` |
| `approved_image_queue.json`, `country_media_coverage.json`, `region_media_coverage.json` | `data/knowledge/media/` |
| `map_validation_report.md`, `walter_coverage_report.md`, `taxonomy_validation_report.md` | `docs/audits/` |
| `food_graph_validation_report.md` | `docs/audits/` (new) |
| `global_culinary_atlas_report.md` | `docs/audits/global_culinary_atlas.md` |
| `continent_coverage_report.md` | `docs/audits/` (new) |
| `country_coverage_report.md`, `culinary_region_coverage_report.md` | `docs/audits/` |
| `missing_regions.json` | `data/knowledge/atlas/` (CLDR subregions) and `data/knowledge/coverage/` (the place tree) |
| `expansion_priority_list.json` | `data/knowledge/coverage/` |
| `readme_improvement_report.md`, `documentation_gap_report.md`, `ci_guardrails_report.md` | `docs/governance/` |
| `needs_human_review.md` | `docs/governance/` |

## The dish quality weights

The brief suggests image 20, history 15, country 10, region 10, family 10, versions 10, Walter context 10, related
dishes 10, recipe coverage 10 and map coverage 5. **Those add up to 110, not 100.** The score we use
(`scripts/knowledge/quality_reports.py`, `WEIGHTS`) has the same parts and points except: fun facts 10 in place of
"Walter context", a recipe 5 in place of 10, and no map part. It was not changed: a new weighting is a policy for
the team (`needs_human_review.md`).
