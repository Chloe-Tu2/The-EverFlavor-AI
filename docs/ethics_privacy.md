# Ethics and Privacy

How the EverFlavor AI data pipeline handles privacy, licenses and responsible use. The same points appear in section 2.5 of the notebook.

## Data collection

1. **Public data only.** Every dataset is published under an open license or a government open-data policy (see `sources.md`). Nothing behind a login is collected, and no website is scraped directly.
2. **No personal information.** The pipeline collects and stores no personally identifiable information. Food.com's interaction data has anonymized user IDs only, and the pipeline does not use them. Open Food Facts contributor identities are not used.
3. **Terms of use respected.** API rate limits and terms are followed: Open Food Facts requests are paced and send a descriptive User-Agent, TheMealDB requests are paced, and USDA data is fetched through its official API and bulk downloads.
4. **Licenses honored.** CulinaryDB and RecipeDB are CC BY-NC-SA 3.0 (non-commercial, with credit). Open Food Facts is ODbL. USDA data is public domain. This is a non-commercial student project.

## Secrets

API keys (USDA now; Google Places and an LLM key later) are never written in the code. They are read from Colab Secrets or from `config/.env`, which git ignores, so they are never pushed. Saved notebook outputs show only whether a key is set, never its value.

## Users of the prototype

- Dietary restrictions, remaining calories and location stay within the session and are not stored without explicit consent.
- Location (Google Places, planned) is used only in real time to find stores, and is not stored or shared.

## Honest limits

- **Restriction flags are not medical advice.** They come from ingredient keywords and miss some cases (see `flag_review/labeling_notes.md`), so the system always runs a hard-coded safety filter after the agents.
- **Estimated nutrition is labeled.** Calories for recipes without listed nutrition are estimates (`nutrition_source` = `estimated`) and come with a likely range; they are never presented as exact.
- **Diet profiles are not certifications.** `halal_friendly`, `kosher_friendly` and `jain_friendly` mean the ingredients contain nothing the diet forbids. They cannot show how meat was slaughtered or whether a product is certified, and religious practice varies, so the system must say "halal-friendly ingredients", never "halal".
- **Medical profiles are screens, not advice.** `alpha_gal_friendly`, `pregnancy_friendly`, `g6pd_friendly`, `gout_friendly`, `low_tyramine` and `nightshade_free` only say that none of the listed ingredients appear. Amounts, preparation and personal tolerance matter, so the system must point people to their doctor or dietitian (policy P17).
- **Predicted origins are labeled.** Countries guessed by the model (`origin_source` = `predicted`) are right about 90% of the time, not always, and should be shown as "probably Moroccan". Labeling a dish with the wrong culture can be hurtful, so agents should prefer source-labeled recipes when authenticity matters.
- **Cuisine coverage is uneven.** European recipes far outnumber African and Middle Eastern ones, and many recipes have no cuisine label. Models are weighted to reduce this bias, and the gap is reported rather than hidden.
