# PII audit (2026-11-22)

`scripts/governance/pii_scan.py` read 478 tracked text files for e-mail addresses, phone numbers, street addresses and GPS coordinates. Values are masked. Nothing was changed: each hit below needs a person to decide whether it is public (a shop's listed phone, a credited author) or personal. Binary tables (parquet) are not read here; their columns are described in `docs/data_dictionary.md`.

## Folders that must never be in git

Tracked files under `data/user/`, `logs/`, `config/.env`: none.

## Hits by kind

- phone number: 16
- street address: 13
- GPS coordinates: 1
- email: 1

## Hits by file (for review)

| File | Area | Kind | Hits | Examples (masked) |
|---|---|---|---:|---|
| `docs/art/flag_recall.svg` | docs | phone number | 14 | `634*********`, `828*********`, `941*********` |
| `data/knowledge/media/commons_meta.json` | data | street address | 4 | `445**********`, `69 *********`, `931*****************` |
| `tests/test_stores.py` | tests | phone number | 2 | `+1 ************` |
| `tests/test_stores.py` | tests | street address | 1 | `12 *******` |
| `data/knowledge/dishes/canada.md` | data | street address | 1 | `560*************` |
| `data/knowledge/dishes/united_states.md` | data | street address | 1 | `88 ***************` |
| `data/knowledge/media/approved_image_queue.json` | data | street address | 1 | `69 *********` |
| `data/knowledge/media/dish_media_audit.json` | data | street address | 1 | `69 *********` |
| `data/knowledge/media/image_priority_queue.json` | data | street address | 1 | `69 *********` |
| `data/knowledge/media/missing_images.json` | data | street address | 1 | `69 *********` |
| `data/knowledge/media/wikidata_images.json` | data | street address | 1 | `69 *********` |
| `docs/plans/MAP.md` | docs | GPS coordinates | 1 | `29.**************` |
| `src/everflavor/sources.py` | code | email | 1 | `t***@everglow.com` |
| `src/everflavor/stores.py` | code | street address | 1 | `123***************` |
