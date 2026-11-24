# Atlas sprint review checklist

Every atlas sprint (a fetch with new sources or countries) passes this gate before its pull request is merged.
Written 2026-11-23 for sprint 4, from med27-coder's request. The sprint's impact report
(`python scripts/knowledge/enrichment_impact.py --sprint N --before <ref>`, writing
`docs/audits/sprints/sprint_N_impact.md`) answers the first four sections with numbers.

## Coverage

- [ ] World culinary coverage went up or stayed the same; any fall is explained
- [ ] The new countries with a dish are named in the report
- [ ] No country lost all its dishes by accident (a country page whose last dish moved away is removed)
- [ ] `atlas_metrics.json`, the README dashboard and the recovery chart were regenerated

## Representation

- [ ] Notebook 15 rerun: dish families and categories
- [ ] Notebook 11 rerun: country pages, with no PC paths in its outputs
- [ ] `region_pages.py`, `country_scores.py` and `country_counts.py` rerun: region pages, weak and uncovered
      countries, our count beside the UN's

## Enrichment and preservation

- [ ] The fetch ran with `--stories`, so story sentences are kept
- [ ] No entry lost its origin, story or family compared with the backup (`dishes.jsonl` before the fetch)
- [ ] `graph_assets.py` rerun: related dishes and Walter's context
- [ ] Every new Indigenous tag is `reviewed: false` and listed for the rubric (`indigenous_review.md`)

## Validation (a person)

- [ ] New entries read (a sample per new source), moved entries each checked
- [ ] Country and region placements of new countries in the place tree checked
- [ ] Each judgment call added to `needs_human_review.md`; no item there silently resolved or removed

## Sources and safety

- [ ] Every new entry keeps its Wikidata and Wikipedia sources and licences
- [ ] Nothing invented: no dish, fact or story without a source sentence
- [ ] `graph_validation.py`: no dish without a place, no cycles

## Repository

- [ ] `pytest`, `ruff`, `mypy` and the Markdown check pass, as in CI; the app loads with no exception
- [ ] No PC paths, personal emails or local-only work in the diff
- [ ] CHANGELOG, `data/knowledge/README.md` and the main README counts match the latest run
