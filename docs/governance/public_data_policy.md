# Public data policy

What may go into this public repository, what needs a person's review first, and what never may. It applies to
every file git tracks: code, data, notebooks (with their outputs), reports and docs. Proposed 2026-11-22 by
Claude (AI); the team confirms it.

## Allowed

- **Recipes** from sources whose licence allows sharing (see [license_compliance.md](license_compliance.md)),
  with their source and link.
- **Dish information** read from Wikipedia (CC BY-SA, credited per article) and Wikidata (CC0).
- **Countries, regions and the Food Taxonomy** (`data/reference/food_taxonomy.csv`), with the source that draws
  each level.
- **Public-domain or CC0 government data** (USDA FoodData Central, FoodKeeper, cooking yields).
- **Counts and audit reports** built from the above (`docs/audits/`, `data/knowledge/`), which hold no recipe
  text from restricted sources.

## Review required (a person decides, and the decision is recorded)

- **Images:** every dish or recipe photo; only free licences, each with its author and licence credit, and a check
  by eye before the app shows it ([human_approval_workflow.md](human_approval_workflow.md)).
- **A new third-party dataset**, or a new use of one we have: its licence, attribution and whether it allows our
  use (non-commercial terms included) go into `docs/sources.md` first.
- **Map data:** OpenStreetMap (ODbL, credit "© OpenStreetMap contributors") and anything from a paid map API
  (Google Places: only place IDs may be stored).
- **Tourism or regional data**, and **imported recipe collections**.
- **Public business details** (a shop's listed phone or address on the map): allowed only as the map source
  publishes them.

## Prohibited (never committed)

- **User data:** profiles, saved preferences, chat history, audit logs (`data/user/`, `logs/`;
  `docs/ethics_privacy.md`).
- **Credentials:** API keys, tokens, passwords, connection strings, cookies (`config/.env` only; Colab Secrets).
- **Personal contact details** of anyone who is not a credited public author: e-mail addresses, phone numbers,
  home addresses. An uploader's e-mail found in a source's metadata is removed before storing
  (`scripts/knowledge/image_queue.py`).
- **Private notes and internal comments:** unfinished plans stay in `docs/plans/local/` (git-ignored); commits use
  the GitHub no-reply address; no personal paths.
- **Content a licence does not allow us to share** (TheMealDB photos, for example).

## How it is enforced

| Check | Where | Fails the run? |
|---|---|---|
| Secret files (.env, keys, user data) | `.gitignore`, the pre-commit hook | Yes (refuses the commit) |
| Secrets inside tracked files | `scripts/governance/secret_scan.py`, in CI and the tests | Yes |
| E-mail, phone, address, GPS hits | `scripts/governance/pii_scan.py` → [pii_audit_report.md](pii_audit_report.md) | No: a person reviews |
| Each source's licence and credit | `docs/sources.md`, [license_compliance.md](license_compliance.md) | Not yet automated |
