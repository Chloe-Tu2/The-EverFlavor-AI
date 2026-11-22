# Spanish, French and Italian allergen words: what changes (2026-11-21)

Every recipe's allergen flags computed twice, with the code on `main` and with the new words (`add_keyword_flags`
on all 291,755 recipes), before the words went in. Policy P26 in `flag_policies.csv`; every word, kept, dropped
or made an exception, with its reason, is in `allergen_words_es_fr_it.csv`.

## The words

- **Batch 1:** Spanish, French and Italian names from notebook 04's name table, only where the Wikidata item's
  own English label is the English ingredient (so "arachide" is the French name of the peanut item).
- **Batch 2:** the core English allergen words the table did not cover (shrimp, squid, tuna, sesame...), looked
  up on Wikidata by their exact English label; when that found the wrong item (a band called Tuna, a heraldic
  lobster) the food item was taken instead and written down. Regular plurals the matcher does not make itself
  (nueces, noci, pistacchi, cozze, gamberi, arachidi) were added.
- **Left out:** words with another meaning in recipes (pan, bar, masa, latte, moule, halwa, sarda, anguilla, maní
  read as "mani"), dish names (a dish is left to the English rules), Latin names and words of other languages.
- **Exceptions:** the foreign names of the English exceptions (lait de coco is coconut milk, harina de arroz is rice
  flour), and the clashes this report found (crème de menthe, kecap manis, noix de coco, beurre noisette, aam panna).

In all: 549 words kept (661 word-and-flag rows, since a word such as gamba sets both crustacean and shellfish), 414 rows left out, 94 exception phrases.

## What changes

240 recipes gain a caution (Food.com 142, CulinaryDB 59, Hugging Face 39); no recipe loses one.

| Flag | Recipes gained | Words behind most of them |
|---|---:|---|
| Gluten | 129 | panini 34, biscotti 25, matzoh 20, pain 11, pumpernickel 11, fideo 8, risoni 6 |
| Dairy | 91 | crème 52, fromage 16, panna 8, panir 8, lait 4 |
| Fish | 7 | pesce 3, ikura, morue, fumet, tonno |
| Sesame | 6 | hoisin 3, halava, téhina, helva |
| Tree nuts | 4 | piñón, pistache, turrón, castagna |
| Molluscs | 2 | vongole, calamar |
| Egg, shellfish, soy | 1 each | huevo, vongole, kochujang |

Every gain is the word's own meaning (panna cotta, linguine con le vongole, matzoh brei), so these are cautions the
English words missed. The flags only ever add cautions; none was removed.

## Known gaps

- Italian "latte" (milk) is left out because English recipes use it for the coffee drink; Italian texts with
  "latte intero" are not caught yet.
- Spanish "maní" is left out (see above); "cacahuete" and "cacahuate" are kept.
- Words outside these three languages are not covered, except the safety gate's own list
  (`FOREIGN_FOOD_WORDS`).
