# Data provenance (2026-11-22)

`scripts/governance/provenance_audit.py` checked 111 tracked data files in `data/knowledge/` and `data/reference/`: does each say its source, licence and date, in the file (JSON) or in a README or `docs/sources.md` that names it? **111 do; 0 need a person.** Nothing was changed.

## Files that need their provenance written down

None.

## The stricter check: licence, version and attribution, file by file

Each file, or a docs line that names it, should also state its licence, a version (of the file or the upstream release) and the credit the licence asks for (CC0 and public domain ask none). A file can be documented above and still miss these, because its folder README covers it as a group. **Flagged, not repaired:** a person writes the missing fields.

| Field | Files that state it | Missing |
|---|---:|---:|
| a licence named | 98 | 13 |
| a version or release date | 58 | 53 |
| the credit its licence asks for | 84 | 27 |

## Every file

| File | Source in file | Licence | Date | Named in docs | Documented | Licence named | Version | Attribution |
|---|---|---|---|---|---|---|---|---|
| `data/knowledge/atlas/Africa_Next_500.json` | yes | yes | yes | **no** | yes | yes | yes | **no** |
| `data/knowledge/atlas/Americas_Next_500.json` | yes | yes | yes | **no** | yes | yes | yes | **no** |
| `data/knowledge/atlas/Asia_Next_500.json` | yes | yes | yes | **no** | yes | yes | yes | **no** |
| `data/knowledge/atlas/Europe_Next_500.json` | yes | yes | yes | **no** | yes | yes | yes | **no** |
| `data/knowledge/atlas/Oceania_Next_500.json` | yes | yes | yes | **no** | yes | yes | yes | **no** |
| `data/knowledge/atlas/coverage_scores.json` | yes | yes | yes | yes | yes | yes | yes | **no** |
| `data/knowledge/atlas/missing_regions.json` | yes | yes | yes | yes | yes | yes | yes | **no** |
| `data/knowledge/atlas/missing_variants.json` | yes | yes | yes | yes | yes | yes | yes | **no** |
| `data/knowledge/atlas/publication_review_queue.json` | yes | yes | yes | yes | yes | yes | yes | **no** |
| `data/knowledge/atlas/regional_expansion_backlog.json` | yes | yes | yes | yes | yes | yes | yes | **no** |
| `data/knowledge/atlas/regions.json` | yes | yes | yes | yes | yes | yes | yes | **no** |
| `data/knowledge/countries.json` | yes | yes | yes | yes | yes | yes | yes | yes |
| `data/knowledge/coverage/country_coverage.json` | yes | **no** | yes | **no** | yes | **no** | yes | **no** |
| `data/knowledge/coverage/culinary_region_coverage.json` | yes | **no** | yes | **no** | yes | **no** | yes | **no** |
| `data/knowledge/coverage/expansion_backlog.json` | yes | **no** | yes | yes | yes | **no** | yes | **no** |
| `data/knowledge/coverage/expansion_priority_list.json` | yes | **no** | yes | **no** | yes | **no** | yes | **no** |
| `data/knowledge/coverage/family_coverage.json` | yes | **no** | yes | **no** | yes | **no** | yes | **no** |
| `data/knowledge/coverage/missing_countries.json` | yes | **no** | yes | **no** | yes | **no** | yes | **no** |
| `data/knowledge/coverage/missing_regions.json` | yes | **no** | yes | yes | yes | **no** | yes | **no** |
| `data/knowledge/coverage/next_500.json` | **no** | **no** | **no** | yes | yes | yes | **no** | **no** |
| `data/knowledge/coverage/wikidata_types.json` | yes | yes | yes | yes | yes | yes | yes | yes |
| `data/knowledge/discovery_paths.json` | yes | yes | yes | yes | yes | yes | yes | yes |
| `data/knowledge/dish_families.json` | yes | yes | yes | yes | yes | yes | yes | yes |
| `data/knowledge/dish_recipe_counts.json` | yes | **no** | yes | yes | yes | yes | yes | yes |
| `data/knowledge/dishes.jsonl` | yes | yes | yes | yes | yes | yes | yes | yes |
| `data/knowledge/dishes/argentina.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/australia.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/austria.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/belgium.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/brazil.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/cambodia.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/canada.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/chile.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/china.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/colombia.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/cuba.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/czech_republic.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/denmark.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/egypt.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/ethiopia.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/finland.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/france.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/germany.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/greece.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/hungary.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/india.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/indonesia.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/iran.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/iraq.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/ireland.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/italy.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/jamaica.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/japan.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/lebanon.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/malaysia.md` | yes | yes | yes | yes | yes | yes | yes | yes |
| `data/knowledge/dishes/mexico.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/morocco.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/netherlands.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/new_zealand.md` | yes | yes | yes | yes | yes | yes | yes | yes |
| `data/knowledge/dishes/norway.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/pakistan.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/palestine.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/peru.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/philippines.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/poland.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/portugal.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/puerto_rico.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/russia.md` | yes | yes | yes | yes | yes | yes | yes | yes |
| `data/knowledge/dishes/saudi_arabia.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/south_africa.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/south_korea.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/spain.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/sweden.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/switzerland.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/thailand.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/turkey.md` | yes | yes | yes | yes | yes | yes | yes | yes |
| `data/knowledge/dishes/united_kingdom.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/united_states.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/dishes/vietnam.md` | yes | yes | yes | yes | yes | yes | **no** | yes |
| `data/knowledge/map_prep.json` | yes | yes | yes | yes | yes | yes | yes | yes |
| `data/knowledge/media/approved_image_queue.json` | yes | yes | yes | yes | yes | yes | yes | yes |
| `data/knowledge/media/commons_meta.json` | **no** | **no** | **no** | yes | yes | yes | yes | yes |
| `data/knowledge/media/country_media_coverage.json` | yes | **no** | yes | **no** | yes | **no** | yes | **no** |
| `data/knowledge/media/dish_media_audit.json` | yes | **no** | yes | **no** | yes | **no** | yes | **no** |
| `data/knowledge/media/image_priority_queue.json` | yes | **no** | yes | **no** | yes | **no** | yes | **no** |
| `data/knowledge/media/missing_images.json` | yes | **no** | yes | **no** | yes | **no** | yes | **no** |
| `data/knowledge/media/region_media_coverage.json` | yes | **no** | yes | **no** | yes | **no** | yes | **no** |
| `data/knowledge/media/wikidata_images.json` | yes | yes | yes | yes | yes | yes | yes | yes |
| `data/knowledge/quality/country_quality.json` | yes | yes | yes | **no** | yes | yes | yes | yes |
| `data/knowledge/quality/culinary_region_quality.json` | yes | yes | yes | **no** | yes | yes | yes | yes |
| `data/knowledge/quality/dish_quality.json` | yes | yes | yes | **no** | yes | yes | yes | yes |
| `data/knowledge/quality/map_validation.json` | yes | yes | yes | **no** | yes | yes | yes | yes |
| `data/knowledge/quality/publication_queue.json` | yes | yes | yes | yes | yes | yes | yes | yes |
| `data/knowledge/quality/taxonomy_coverage.json` | yes | yes | yes | **no** | yes | yes | yes | yes |
| `data/knowledge/quality/taxonomy_validation.json` | yes | **no** | yes | yes | yes | **no** | yes | **no** |
| `data/knowledge/quality/walter_coverage.json` | yes | yes | yes | **no** | yes | yes | yes | yes |
| `data/knowledge/recipe_graph_counts.json` | yes | **no** | yes | yes | yes | yes | yes | yes |
| `data/knowledge/recipe_quality.json` | yes | **no** | yes | yes | yes | yes | yes | yes |
| `data/knowledge/review/focus_review.csv` | yes | yes | yes | yes | yes | yes | **no** | **no** |
| `data/knowledge/review/origin_elsewhere.csv` | yes | yes | yes | yes | yes | yes | **no** | **no** |
| `data/knowledge/walter_context.json` | yes | yes | yes | yes | yes | yes | yes | yes |
| `data/reference/cooking_fats.csv` | yes | yes | yes | yes | yes | yes | yes | yes |
| `data/reference/dish_photo_review.csv` | yes | yes | yes | yes | yes | yes | yes | yes |
| `data/reference/dish_pronunciation.csv` | yes | yes | yes | yes | yes | yes | yes | yes |
| `data/reference/food_taxonomy.csv` | yes | yes | yes | yes | yes | yes | yes | yes |
| `data/reference/may_contain.csv` | yes | yes | yes | yes | yes | yes | yes | yes |
| `data/reference/photo_check_sample.csv` | yes | yes | yes | yes | yes | yes | yes | yes |
| `data/reference/place_evidence.csv` | yes | yes | yes | yes | yes | yes | yes | yes |
| `data/reference/recipe_photo_review.csv` | yes | yes | yes | yes | yes | yes | yes | yes |
| `data/reference/specialty_ingredients.csv` | yes | yes | yes | yes | yes | yes | yes | yes |
| `data/reference/walter_injection_set.csv` | yes | yes | yes | yes | yes | yes | yes | yes |
