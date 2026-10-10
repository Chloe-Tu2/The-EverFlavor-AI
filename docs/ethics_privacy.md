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

## User data (rules for the app)

What the app learns about a person (allergies, religious or ethical diets, and later health conditions such as
diabetes) is personal and health-related. Nothing like it exists yet; these rules apply from the first version
that saves anything.

| Data | Rule |
|---|---|
| **Profiles** (foods to avoid, diets, calorie budget, area) | Store only what the features need. If saved, encrypt on disk, with the key in `config/.env` or the operating system's key store, never in the repo. Let the user see and delete their profile. |
| **Chat history** | Not saved by default. If a feature needs it: ask first, encrypt it, delete it after a set time. |
| **Audit log** (`llm.ask_agent(..., audit_log=...)`) | Records only the time, model, reason and rules of each blocked answer, never the user's words. |
| **Food photos** (separate photo PC) | Stay on that PC; not sent to outside services. |
| **Location** | Used in real time to find stores; not stored. |
| **Laptop to photo PC** | Ollama talks over plain, unencrypted HTTP: only inside a home network, or through an encrypted tunnel (SSH or a VPN such as Tailscale); never open to the internet. |

**Never in git:** user data goes under `data/user/` or `logs/`, which git ignores together with files named
`user_profiles*`, `chat_history*` and `*audit*.jsonl`; a security test fails if any is tracked
(`tests/test_security.py`). Git keeps every past version, so anything pushed by mistake stays readable even
after it is deleted.

**What is not encrypted, on purpose:** the repository holds code, documentation and results from public
datasets, which teammates and graders need to read. If the team wants only its members to see the
repository, make it private on GitHub (Settings) and add collaborators: access control, with no key to share.
API keys are never committed, not even encrypted; share them with a password manager or a private message,
and use Colab Secrets (or GitHub Actions secrets for CI).

## Honest limits

- **Restriction flags are not medical advice.** They come from ingredient keywords and miss some cases (see `flag_review/labeling_notes.md`), so the system always runs a hard-coded safety filter after the agents.
- **Estimated nutrition is labeled.** Calories for recipes without listed nutrition are estimates (`nutrition_source` = `estimated`) and come with a likely range; they are never presented as exact.
- **Diet profiles are not certifications.** `halal_friendly`, `kosher_friendly` and `jain_friendly` mean the ingredients contain nothing the diet forbids. They cannot show how meat was slaughtered or whether a product is certified, and religious practice varies, so the system must say "halal-friendly ingredients", never "halal".
- **Medical profiles are screens, not advice.** `alpha_gal_friendly`, `pregnancy_friendly`, `g6pd_friendly`, `gout_friendly`, `low_tyramine` and `nightshade_free` only say that none of the listed ingredients appear. Amounts, preparation and personal tolerance matter, so the system must point people to their doctor or dietitian (policy P17).
- **Predicted origins are labeled.** Countries guessed by the model (`origin_source` = `predicted`) are right about 90% of the time, not always, and should be shown as "probably Moroccan". Labeling a dish with the wrong culture can be hurtful, so agents should prefer source-labeled recipes when authenticity matters.
- **Cuisine coverage is uneven.** European recipes far outnumber African and Middle Eastern ones, and many recipes have no cuisine label. Models are weighted to reduce this bias, and the gap is reported rather than hidden.
