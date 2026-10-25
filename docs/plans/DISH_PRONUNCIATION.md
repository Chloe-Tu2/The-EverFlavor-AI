# Dish Pronunciation

A plan to show, next to a foreign dish's name, its name in its own language and script and a simple way to say it,
for example "Bulgogi · 불고기 · bool-GOH-gee" or "Paella · paella · pah-EH-yah", with a play button when an open
recording exists. Part of the next version ([planner](README.md)). It depends on clean dish names
([DISH_NAMES.md](DISH_NAMES.md)).

Written 2026-10-25 (Claude, with med27-coder). This is a plan. Nothing in `src/`, the notebooks or the app has
changed. The prototype scripts and their outputs stay in the session scratchpad, not in the repository.

All numbers come from a prototype run on 2026-10-24/25 against `data/processed/recipes_{train,val,test}.parquet`
(76,866 recipes from the 16 focus countries) and live Wikidata, Wikipedia, Wiktionary and Commons answers on those
days. They will move a little when those sites change.

## 1. Short answer

- **Native name and script: yes, from Wikidata.** 215 of the 221 matched dishes (97%) have a label in the
  dish's language. About 1 in 5 of those labels is a longer or different name (see section 5), so a person checks
  each one before it ships.
- **IPA: too hard for most users, and patchy.** 128 of 221 (58%) have a native IPA from Wikidata or Wiktionary.
  We keep it only as the source for the respelling.
- **Respelling: no open source covers it.** Wikipedia's hand-written `{{respell}}` exists for only 34 of 221
  (15%). A rule-based respelling from the native IPA is a good *draft* (27 of 33 sound right on the top 50), but it
  fails on stress and on wrong labels. **Recommendation: a small curated table, drafted by the rules and checked by
  the team.**
- **Audio: rare.** 59 of 221 (27%) have a recording in the dish's own language on Wikimedia Commons. Most are CC
  BY-SA and need a visible credit.
- **Coverage is uneven.** Italian, French, Spanish and Mexican dish names match well. Chinese, Thai, Korean,
  Moroccan, Turkish, Iranian and Egyptian recipes mostly have English names ("korean beef", "moroccan chicken"),
  so few get a native name by automatic matching.

## 2. Sources and licenses

| Source | What we use | License | How we read it | Credit needed |
|---|---|---|---|---|
| Wikidata | dish item, English label and aliases, native label, P1705 native label, P898 IPA, P443 audio, P495 country of origin, lexemes linked by P5137 | CC0 | SPARQL endpoint, small paced queries with a descriptive User-Agent | No (we still name it) |
| English Wikipedia | the lead's `{{IPAc-en}}` and `{{respell}}` | CC BY-SA 4.0 | MediaWiki API, lead section only | Yes, if we copy a respelling |
| English Wiktionary | English-section IPA and audio; native-word IPA | CC BY-SA 4.0 (and GFDL) | MediaWiki API, one page at a time | Yes, if we copy IPA |
| kaikki.org (Wiktionary extract) | same as Wiktionary, as bulk files | same as Wiktionary | not used: the files are large and the API was enough | Yes |
| Wikimedia Commons (often Lingua Libre) | pronunciation recordings | per file: CC BY-SA 4.0, 3.0, CC BY, CC0, public domain | Commons API `extmetadata` gives license and author | Yes, per file |

No scraping: every call went through an official API or query service, paced at about one call per second, as the
project's data rule asks.

## 3. How the prototype worked

1. Took every 1-3 word phrase that appears in at least 5 recipe names from the 16 focus countries (5,000 most
   common phrases).
2. Looked each phrase up as a Wikidata English label or alias (lower case and capitalised), keeping items with at
   least 3 Wikipedia links.
3. Kept items that are a food or dish (instance or subclass of food Q2095 or dish Q746549) and whose country of
   origin (P495) is a focus country or its region (for example Korea Q18097, Levant Q48214, Ottoman Empire).
4. Dropped plain English words (salad, sauce, chicken, "french", "sweet" and about 150 more). Without this list,
   "sweet", "roll", "gluten" and "french toast" were among the top matches.
5. Matched each recipe name to its longest matching phrase, then took the most common dishes. Only **221**
   dishes passed (the brief asked for about 300); the long tail is mostly single recipes.
6. For those 221: native labels, IPA, audio and lexemes from Wikidata; the Wikipedia lead; Wiktionary pages; and
   the license of every audio file from Commons.

## 4. Coverage per country

"Dishes" counts matched dishes by their country of origin. "Recipes" counts recipes that name one of them.

| Origin | Dishes | Recipes | Native name | Non-Latin script | Native IPA | English IPA | Wikipedia respelling | Native audio |
|---|---|---|---|---|---|---|---|---|
| Italy | 80 | 10,716 | 77 | 0 | 45 | 60 | 16 | 7 |
| France | 41 | 2,505 | 41 | 0 | 33 | 33 | 10 | 32 |
| India | 25 | 1,453 | 23 | 23 | 13 | 15 | 0 | 0 |
| Mexico | 22 | 3,613 | 21 | 0 | 8 | 20 | 1 | 5 |
| Japan | 12 | 712 | 12 | 12 | 10 | 11 | 1 | 4 |
| Greece | 11 | 1,415 | 11 | 11 | 1 | 9 | 1 | 1 |
| China | 11 | 443 | 11 | 11 | 5 | 8 | 1 | 2 |
| Spain | 8 | 883 | 8 | 0 | 6 | 7 | 3 | 5 |
| Thailand | 3 | 59 | 3 | 3 | 3 | 1 | 0 | 1 |
| Egypt | 2 | 304 | 2 | 2 | 0 | 2 | 0 | 1 |
| South Korea | 2 | 142 | 2 | 2 | 2 | 2 | 1 | 0 |
| Turkey | 2 | 103 | 2 | 0 | 0 | 2 | 0 | 0 |
| Iran | 1 | 197 | 1 | 1 | 1 | 1 | 0 | 1 |
| Lebanon | 1 | 83 | 1 | 1 | 1 | 0 | 0 | 0 |
| **All** | **221** | **22,628** | **215 (97%)** | **66 (30%)** | **128 (58%)** | **171 (77%)** | **34 (15%)** | **59 (27%)** |

Share of each focus country's recipes that name a matched dish:

| Country | Recipes | Name a matched dish |
|---|---|---|
| Italy | 25,150 | 10,390 (41%) |
| Greece | 4,363 | 1,814 (42%) |
| Japan | 2,269 | 819 (36%) |
| Spain | 1,845 | 652 (35%) |
| Mexico | 14,849 | 4,022 (27%) |
| France | 8,691 | 2,236 (26%) |
| South Korea | 606 | 157 (26%) |
| Lebanon | 587 | 152 (26%) |
| India | 7,403 | 1,681 (23%) |
| Turkey | 471 | 63 (13%) |
| Iran | 429 | 32 (7%) |
| Egypt | 206 | 15 (7%) |
| China | 5,984 | 375 (6%) |
| Thailand | 2,421 | 143 (6%) |
| Morocco | 1,592 | 77 (5%) |
| Taiwan | 0 | 0 (no recipes are labelled Taiwan yet) |

Some well-known dishes were missed by the automatic step: "tagine" (147 recipe names; the Wikidata label is
"tajine"), "kimchi" in lower case, "tikka masala", "pho" (Vietnam is not a focus country). A curated table fixes
these in minutes.

Audio in any language exists for 107 dishes, but much of it is the wrong language (Swedish "Fetaost", French
"risotto", German "Pesto"). Only recordings in the dish's own language count above. Lingua Libre made 37 of the 59.

## 5. What goes wrong

| Problem | Examples from the run | Share |
|---|---|---|
| Native label is a longer or different name | pesto → "pesto alla genovese", biscotti → "cantuccio", queso → "chili con queso", orzo → "risoni", tandoori → "तंदूरी चिकन" | about 15 of the top 70 |
| Wrong dish or wrong origin | ramen matched with origin China, label "日本拉面" ("Japanese ramen" in Chinese) | a few |
| English words matched as dishes | "sweet", "roll", "gluten", "mayo", "bbq" before the stop list | fixed by the stop list |
| Broken IPA from parsing | kimchi native IPA read as "/ki/"; X-SAMPA strings such as "/,fEtə'tSi:ni/" | a few |
| Regional variants | Spanish "chorizo": Mexico choh-REE-soh, Spain choh-REE-thoh; Chinese: Mandarin vs Cantonese (dim sum, wonton, chow mein come from Cantonese); Arabic dialects (hummus) | needs a choice per dish |
| Script variants | Wikidata "zh" is often simplified; Taiwan needs traditional (zh-hant) | Taiwan has no recipes yet |

## 6. Respelling: what is reliable

We tested three ways on the top 50 dishes, against a curated draft (`curated_top50.csv` in the scratchpad, written
by Claude from common US usage and the native IPA; the team must still check it).

| Method | Available (of 50) | Sounds right | Same stress and syllables | Both |
|---|---|---|---|---|
| Rules from the native IPA (Wikidata / Wiktionary) | 33 | 27 | 21 | 18 |
| Rules from the English IPA (Wikipedia / Wiktionary) | 44 | 19 | 39 | 17 |
| Wikipedia `{{respell}}` (hand-written) | 34 of all 221 | the English way of saying it | 16 of 31 agree with the rules | |

What this means:

- The **English IPA** gives the anglicised way (broo-SKEH-tuh, py-EH-luh). It has the right stress but not the
  sound "as said in its region".
- The **native IPA** gives the regional sound (broos-KEHT-tah, pah-EH-yah) but loses stress when the IPA has no
  stress mark (French, Japanese) and inherits wrong labels (biscotti → kahn-TOOT-choh).
- **Neither is reliable alone.** The honest choice: a curated respelling per dish, drafted by the native-IPA rules,
  checked by a team member (or a speaker of the language), with the reviewer's name in the table. No respelling is
  better than a wrong one.

## 7. Recommended display

```text
Paella · paella · pah-EH-yah  [▶ Listen]
Bulgogi · 불고기 · bool-GOH-gee
Audio: "LL-Q1321 (spa)-Marreromarco-paella.wav", Marreromarco, CC BY-SA 4.0, via Wikimedia Commons
```

- The English dish name first, as now.
- The native name only when it differs from the English one or uses another script (66 of 221 use another
  script). Do not repeat "risotto · risotto".
- The respelling in plain letters, stressed syllable in capitals, with a small "how to say it" label. No IPA on
  the page (it can sit in a tooltip).
- A play button only when a recording in the dish's language exists. Audio plays only on a tap, never on page load
  (`st.audio(url)` without `autoplay`). Stream from Commons or keep a small copy; either way show the credit.
- The credit under the player: file name or title, author, license with a link, "via Wikimedia Commons". CC0 and
  public-domain files need no credit, but we show the source anyway.
- If the dish is unclear (no checked row), show nothing extra.

## 8. Where the data lives

A small committed table, `data/reference/dish_pronunciation.csv` (or `data/processed/` if the team prefers), about
250 rows, one per dish. A draft with this layout is in the scratchpad (`out/dish_pronunciation_draft.csv`).

| Column | Example |
|---|---|
| `dish_key` | paella |
| `wikidata_qid` | Q212121 |
| `origin_country`, `lang`, `variant` | Spain, es, es-ES |
| `native_name` | paella |
| `respelling`, `respelling_source` | pah-EH-yah, curated |
| `ipa` | /paˈeʝa/ |
| `audio_file`, `audio_license`, `audio_author` | the Commons file name, CC BY-SA 4.0, the author |
| `reviewed_by`, `reviewed_on` | team member, date |

Wikidata facts are CC0, so they can be committed. Copied Wiktionary IPA and Wikipedia respellings are CC BY-SA: the
table's README names the sources and license, and the table is shared under the same terms. We do not commit audio
files; we store the file name and play it from Commons.

## 9. How it is matched to recipes

- The clean dish name from [DISH_NAMES.md](DISH_NAMES.md) is the key. Raw recipe names ("ina garten s chicken pot
  pie") must not be matched directly.
- Match on whole words, longest phrase first, singular and plural.
- Show the row only when the recipe's country fits the dish's origin (a recipe from Italy called "tacos" gets no
  Spanish line).
- Matching runs in the back end (`src/everflavor`), like every other data decision. The page only shows the result.

## 10. Risks

- **Wrong match:** a wrong native name looks worse than none. Only reviewed rows ship.
- **Regional variants:** Mexican vs Spain Spanish, Mandarin vs Cantonese, Levantine vs Egyptian Arabic. Each row
  names one variant and says it ("as said in Mexico").
- **Licenses:** every audio file and copied IPA keeps its credit. A file with no clear license is left out.
- **Sources change:** Wikidata labels change. The table is a snapshot with a date; we refresh it on purpose.
- **Respect:** names for religious or regional foods follow the source language, never a joke spelling.

## 11. Steps in order

1. Wait for clean dish names ([DISH_NAMES.md](DISH_NAMES.md)).
2. Re-run the prototype on the clean names; add the missed dishes by hand (tagine, kimchi, tikka masala, the top
   dish of each kitchen).
3. Build the table (about 250 rows): native name, native-IPA respelling draft, audio file and license.
4. Team review: each row checked and signed in `reviewed_by`; choose the variant per dish.
5. Back end: a lookup in `src/everflavor` from dish name to the row, with tests (a missing row shows nothing).
6. App: show the line and the play button with credit on the recipe card; audio only on a tap.
7. Credits page and data README: sources, licenses, date of the snapshot.
8. Later: more countries, Taiwanese (traditional script) when Taiwan recipes exist.
