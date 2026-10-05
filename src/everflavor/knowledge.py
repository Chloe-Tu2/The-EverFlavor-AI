"""Ingredient knowledge for the agents (notebook 04): pairings, substitutions,
shelf life and names in other languages. Every source is free and needs no key."""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import re
import time
from collections.abc import Iterable, Sequence
from pathlib import Path

import pandas as pd
import requests

from .flags import flags_for_term
from .ingredients import normalize_ingredient
from .progress import progress_bar

__all__ = [
    "ALCOHOL_FREE_SWAPS",
    "FOODKEEPER_ARCHIVE_URL",
    "FOODKEEPER_URL",
    "FOOD_DESCRIPTION_WORDS",
    "NOT_FOOD_DESCRIPTION_WORDS",
    "SHELF_LIFE_CONDITIONS",
    "SUBSTITUTION_PATTERNS",
    "WIKIDATA_SPARQL",
    "WIKIDATA_USER_AGENT",
    "download_foodkeeper",
    "foodkeeper_table",
    "ingredient_pairings",
    "match_shelf_life",
    "names_in_languages",
    "substitution_effects",
    "substitutions_from_reviews",
    "wikidata_matches",
]


# ------------------------------------------------------------------ pairings (section 4)
def _scope_pairings(lists: pd.Series, scope: str, min_recipes: int) -> pd.DataFrame:
    """PMI of every ingredient pair seen together in at least `min_recipes` of `lists`."""
    from scipy import sparse
    from sklearn.preprocessing import MultiLabelBinarizer

    n = len(lists)
    counts = pd.Series([i for items in lists for i in set(items)]).value_counts()
    common = counts.index[counts >= min_recipes]   # a pair can not be more common than its ingredients
    if n == 0 or len(common) < 2:
        return pd.DataFrame(columns=["ingredient_a", "ingredient_b", "scope", "n_recipes", "pmi", "npmi"])
    binarizer = MultiLabelBinarizer(classes=list(common), sparse_output=True)
    keep = set(common)
    x = sparse.csr_matrix(binarizer.fit_transform([[i for i in set(items) if i in keep] for items in lists]),
                          dtype="int32")
    together = sparse.triu(x.T @ x, k=1).tocoo()   # each pair once, without an ingredient with itself
    mask = together.data >= min_recipes
    a, b, n_ab = together.row[mask], together.col[mask], together.data[mask]
    names = binarizer.classes_
    n_a = counts.loc[names[a]].to_numpy()
    n_b = counts.loc[names[b]].to_numpy()
    p_ab = n_ab / n
    pmi = pd.Series(p_ab / ((n_a / n) * (n_b / n))).map(math.log2).to_numpy()
    # Normalized PMI runs from -1 to 1 (1: always together), so scopes of any size compare
    npmi = [p / -math.log2(q) if q < 1 else 1.0 for p, q in zip(pmi, p_ab)]
    return pd.DataFrame({"ingredient_a": names[a], "ingredient_b": names[b], "scope": scope,
                         "n_recipes": n_ab, "pmi": pmi.round(3), "npmi": pd.Series(npmi).round(3)})


def ingredient_pairings(recipes: pd.DataFrame, scope_column: str | None = None,
                        min_recipes: int = 30, skip_scopes: Iterable[str] = ("Other", "Unknown")) -> pd.DataFrame:
    """Score how much more often two ingredients appear together than by chance (PMI).

    PMI = log2(P(a and b) / (P(a) P(b))): 0 means independent, higher means they go
    together. Only pairs seen in at least `min_recipes` recipes are kept, so rare
    pairs do not get huge scores. Computed over all recipes, or within each value
    of `scope_column` (a cuisine family or a country), so "ginger + soy sauce" can
    score high in Asian recipes and "basil + tomato" in Italian ones.

    Args:
        recipes: Recipes with an `ingredient_list` column (lists of normalized names).
        scope_column: None for all recipes, or a column such as "cuisine_family".
        min_recipes: Minimum recipes a pair must appear in.
        skip_scopes: Scope values left out (they are not one cuisine).

    Returns:
        ingredient_a, ingredient_b (alphabetical within the pair), scope ("all" or the
        column's value), n_recipes, pmi and npmi (normalized PMI, -1 to 1), strongest first.
    """
    lists = recipes["ingredient_list"].map(lambda v: [str(i) for i in v] if v is not None else [])
    if scope_column is None:
        groups: list[tuple[str, pd.Series]] = [("all", lists)]
    else:
        groups = [(str(scope), lists[recipes[scope_column] == scope])
                  for scope in recipes[scope_column].dropna().unique() if str(scope) not in set(skip_scopes)]
    parts = [_scope_pairings(group.reset_index(drop=True), scope, min_recipes) for scope, group in groups]
    out = pd.concat([p for p in parts if len(p)], ignore_index=True) if any(len(p) for p in parts) else parts[0]
    swap = out["ingredient_a"] > out["ingredient_b"]
    out.loc[swap, ["ingredient_a", "ingredient_b"]] = out.loc[swap, ["ingredient_b", "ingredient_a"]].to_numpy()
    return out.sort_values(["scope", "npmi"], ascending=[True, False], ignore_index=True)


# ------------------------------------------------------------------ substitutions (section 3)
# "X" is what the reviewer used, "Y" what the recipe asked for
SUBSTITUTION_PATTERNS = [
    re.compile(r"\bused (?P<new>[a-z][a-z' -]*?) instead of (?:the )?(?P<old>[a-z][a-z' -]*)"),
    re.compile(r"\bsubstituted (?P<new>[a-z][a-z' -]*?) for (?:the )?(?P<old>[a-z][a-z' -]*)"),
    re.compile(r"\breplaced (?:the )?(?P<old>[a-z][a-z' -]*?) with (?P<new>[a-z][a-z' -]*)"),
    re.compile(r"\bswapped (?:the )?(?P<old>[a-z][a-z' -]*?) for (?P<new>[a-z][a-z' -]*)"),
]
# Words that end an ingredient name in free text ("sour cream and it was great")
_STOP_WORDS = {"and", "but", "because", "since", "as", "in", "to", "it", "so", "for", "instead", "that", "this",
               "which", "with", "on", "at", "of", "was", "were", "is", "are", "i", "we", "my", "next", "then",
               "also", "too", "plus", "or", "worked", "turned", "made", "added", "used", "the", "a", "an"}
_LEADING_WORDS = {"a", "an", "the", "some", "little", "bit", "of", "more", "less", "just", "only", "half",
                  "regular", "plain", "my", "our", "fresh", "all"}
MAX_NAME_WORDS = 4


def _words_before_stop(text: str) -> list[str]:
    """Return the first words of `text` up to a word that ends an ingredient name (at most MAX_NAME_WORDS)."""
    words: list[str] = []
    text = re.sub(r"\bhalf (?:and|&|n) half\b", "half-and-half", text)   # one ingredient, not "half" + "half"
    for word in text.split():
        if word in _STOP_WORDS and words:
            break
        if not words and word in _LEADING_WORDS:
            continue
        words.append(word)
        if len(words) == MAX_NAME_WORDS:
            break
    return words


def _match_recipe_ingredient(text: str, ingredients: Sequence[str]) -> str | None:
    """Return the recipe ingredient the start of `text` names (longest match first), or None."""
    words = _words_before_stop(text)
    for size in range(len(words), 0, -1):
        names = normalize_ingredient(" ".join(words[:size]))
        if not names:
            continue
        name = names[0]
        for ingredient in ingredients:
            if ingredient == name or ingredient.endswith(" " + name):
                return ingredient
    return None


def _clean_substitute(text: str) -> str | None:
    """Return the normalized name at the start of `text`, or None if nothing is left."""
    names = normalize_ingredient(" ".join(_words_before_stop(text)))
    return names[0] if names and names[0] not in _STOP_WORDS else None


def substitutions_from_reviews(reviews: pd.DataFrame, recipes: pd.DataFrame, min_reviews: int = 2) -> pd.DataFrame:
    """Find "used X instead of Y" swaps in review text, keeping only pairs where Y is in the recipe.

    Checking Y against the recipe's own ingredient list filters out most wrong
    matches ("used less time instead of ..."): a review can only replace an
    ingredient the recipe has.

    Args:
        reviews: Food.com reviews with `recipe_id` (Food.com's number), `review` and `rating`.
        recipes: Recipes with `recipe_id` ("foodcom_<number>") and `ingredient_list`.
        min_reviews: Minimum reviews that describe the same swap.

    Returns:
        original, substitute, n_reviews, mean_rating (0-5; Food.com uses 0 for no rating,
        which is left out), example_review (the first matching sentence), most reviews first.
    """
    foodcom = recipes[recipes["recipe_id"].astype(str).str.startswith("foodcom_")]
    ingredients = dict(zip(foodcom["recipe_id"].str.removeprefix("foodcom_").astype(int), foodcom["ingredient_list"]))
    rows = []
    texts = reviews[["recipe_id", "review", "rating"]].dropna(subset=["review"])
    has_word = texts["review"].str.contains(r"\b(?:instead of|substitut|replaced|swapped)", case=False, regex=True)
    for recipe_id, review, rating in texts[has_word].itertuples(index=False):
        recipe_ingredients = ingredients.get(int(recipe_id))
        if recipe_ingredients is None:
            continue
        for sentence in re.split(r"[.!?;\n]+", str(review).lower()):
            for pattern in SUBSTITUTION_PATTERNS:
                for m in pattern.finditer(sentence):
                    old = _match_recipe_ingredient(m.group("old"), list(recipe_ingredients))
                    new = _clean_substitute(m.group("new"))
                    if old and new and new != old:
                        rows.append((old, new, rating, sentence.strip()[:200]))
    pairs = pd.DataFrame(rows, columns=["original", "substitute", "rating", "sentence"])
    if pairs.empty:
        return pd.DataFrame(columns=["original", "substitute", "n_reviews", "mean_rating", "example_review"])
    out = (pairs.assign(rating=pairs["rating"].where(pairs["rating"] > 0))
           .groupby(["original", "substitute"])
           .agg(n_reviews=("sentence", "size"), mean_rating=("rating", "mean"), example_review=("sentence", "first"))
           .reset_index())
    out["mean_rating"] = out["mean_rating"].round(2)
    return (out[out["n_reviews"] >= min_reviews]
            .sort_values(["n_reviews", "original"], ascending=[False, True], ignore_index=True))


def substitution_effects(pairs: pd.DataFrame) -> pd.DataFrame:
    """Add what each swap changes: the restriction flags it removes and adds (everflavor.flags).

    A swap only ever suggests; the agent still checks the substitute against the
    person's restrictions, and a swap never clears a caution on its own.

    Returns:
        A copy of `pairs` with `flags_removed` and `flags_added` (space-separated flag names).
    """
    out = pairs.copy()
    names = pd.unique(pd.concat([out["original"], out["substitute"]]))
    flags = {name: set(flags_for_term(str(name))) for name in names}
    out["flags_removed"] = [" ".join(sorted(flags[o] - flags[s])) for o, s in zip(out["original"], out["substitute"])]
    out["flags_added"] = [" ".join(sorted(flags[s] - flags[o])) for o, s in zip(out["original"], out["substitute"])]
    return out


# Alcohol-free swaps for recipes with contains_alcohol or contains_alcohol_extract, from
# common cooking guidance; notebook 02 estimates how much alcohol cooking leaves
ALCOHOL_FREE_SWAPS = pd.DataFrame([
    ("red wine", "beef or vegetable stock with a little red wine vinegar", "adds acidity like wine"),
    ("white wine", "chicken or vegetable stock with a little lemon juice or white wine vinegar", "keeps the acidity"),
    ("beer", "stock or non-alcoholic beer", "non-alcoholic beer may still hold up to 0.5% alcohol"),
    ("mirin", "rice vinegar with a little sugar", "mirin is sweet rice wine"),
    ("sake", "rice vinegar diluted with water, or stock", ""),
    ("sherry", "apple or white grape juice with a little vinegar", ""),
    ("brandy", "apple juice or brandy-flavored alcohol-free extract", "check the extract's label"),
    ("rum", "pineapple or apple juice, or alcohol-free rum flavoring", "check the flavoring's label"),
    ("vanilla extract", "alcohol-free vanilla flavoring, vanilla powder or a vanilla bean", ""),
    ("almond extract", "alcohol-free almond flavoring", ""),
], columns=["original", "substitute", "note"])


# ------------------------------------------------------------------ shelf life (section 5)
FOODKEEPER_URL = "https://www.fsis.usda.gov/shared/data/EN/foodkeeper.json"   # CC0 (data.gov)
# USDA's server refuses some networks (HTTP 403); the Internet Archive keeps the same file
FOODKEEPER_ARCHIVE_URL = "https://web.archive.org/web/20250702182320id_/" + FOODKEEPER_URL
# Column prefix in FoodKeeper -> (storage place, when the time starts)
SHELF_LIFE_CONDITIONS = {
    "Pantry": ("pantry", "as sold"), "DOP_Pantry": ("pantry", "from purchase"),
    "Pantry_After_Opening": ("pantry", "after opening"),
    "Refrigerate": ("fridge", "as sold"), "DOP_Refrigerate": ("fridge", "from purchase"),
    "Refrigerate_After_Opening": ("fridge", "after opening"),
    "Refrigerate_After_Thawing": ("fridge", "after thawing"),
    "Freeze": ("freezer", "as sold"), "DOP_Freeze": ("freezer", "from purchase"),
}
_DAYS_PER = {"hours": 1 / 24, "days": 1, "weeks": 7, "months": 30, "years": 365, "year": 365}


def download_foodkeeper(folder: str | Path, refresh: bool = False, timeout: int = 60) -> Path:
    """Download USDA FoodKeeper (JSON) once, from USDA or, if USDA refuses, the Internet Archive copy.

    Returns:
        The saved `foodkeeper.json` (plain JSON, even when the copy came compressed).

    Raises:
        RuntimeError: If neither copy can be downloaded.
    """
    target = Path(folder) / "foodkeeper.json"
    if target.exists() and not refresh:
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    for url in (FOODKEEPER_URL, FOODKEEPER_ARCHIVE_URL):
        try:
            response = requests.get(url, timeout=timeout, headers={"User-Agent": WIKIDATA_USER_AGENT})
        except (requests.ConnectionError, requests.Timeout):
            continue
        if not response.ok:
            continue
        content = response.content
        if content[:2] == b"\x1f\x8b":   # the archive can return the file still gzip-compressed
            content = gzip.decompress(content)
        json.loads(content)              # a broken copy is never saved
        partial = target.with_suffix(".part")
        partial.write_bytes(content)
        partial.replace(target)
        return target
    raise RuntimeError("USDA FoodKeeper could not be downloaded from USDA or the Internet Archive")


def _days(value: object, unit: object) -> float | None:
    """Turn a FoodKeeper time and unit into days (None for 'Indefinitely', 'When Ripe' ...)."""
    factor = _DAYS_PER.get(str(unit).strip().lower())
    if factor is None or not isinstance(value, (int, float)) or math.isnan(value):
        return None
    return round(float(value) * factor, 2)


def foodkeeper_table(path: str | Path) -> pd.DataFrame:
    """Tidy FoodKeeper: one row per food, storage place and starting point, times in days.

    Times are USDA guidance, never a guarantee that food is safe ("USDA suggests
    using it within 3-5 days").

    Args:
        path: The FoodKeeper JSON file (download_foodkeeper).

    Returns:
        foodkeeper_id, name (with its subtitle), product (without it), keywords, category, storage
        (pantry / fridge / freezer), condition (as sold / from purchase / after
        opening / after thawing), min_days, max_days, unit (as FoodKeeper wrote it:
        "Months", or a note such as "Not Recommended"), tip.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    sheets = {s["name"]: [{k: v for cell in row for k, v in cell.items()} for row in s["data"]] for s in data["sheets"]}
    categories = {int(c["ID"]): " / ".join(x for x in (c.get("Category_Name"), c.get("Subcategory_Name")) if x)
                  for c in sheets["Category"]}
    rows = []
    for food in sheets["Product"]:
        name = food.get("Name") or ""
        if food.get("Name_subtitle"):
            name = f"{name} ({food['Name_subtitle']})"
        for prefix, (storage, condition) in SHELF_LIFE_CONDITIONS.items():
            unit = food.get(f"{prefix}_Metric")
            tip = food.get(f"{prefix}_tips") or food.get(f"{prefix}_Tips")
            if not unit and not tip:
                continue
            rows.append({"foodkeeper_id": int(food["ID"]), "name": name, "product": food.get("Name") or "",
                         "keywords": food.get("Keywords") or "",
                         "category": categories.get(int(food.get("Category_ID") or 0), ""),
                         "storage": storage, "condition": condition,
                         "min_days": _days(food.get(f"{prefix}_Min"), unit),
                         "max_days": _days(food.get(f"{prefix}_Max"), unit),
                         "unit": unit or "", "tip": tip or ""})
    return pd.DataFrame(rows)


def match_shelf_life(ingredients: Iterable[str], table: pd.DataFrame) -> pd.DataFrame:
    """Match each of our ingredient names to its best FoodKeeper food.

    Matches, best first: "name" (the food's own name, such as "Milk"), "keyword"
    (one of its keywords, first keywords first) and "head" (only the ingredient's
    last word matches: "cheddar cheese" -> "Cheese"). "keyword" and "head" matches
    go to a hand check, like the USDA nutrition matches in notebook 01.

    Returns:
        ingredient, foodkeeper_id, foodkeeper_name, match, n_candidates (foods that
        matched equally well); ingredients without a match are left out.
    """
    foods = table[["foodkeeper_id", "name", "product", "keywords"]].drop_duplicates("foodkeeper_id")
    # Form -> [(rank, foodkeeper_id)]: rank 0 for the food's own name, then its keywords in order
    index: dict[str, list[tuple[int, int]]] = {}
    for fid, product, keywords in foods[["foodkeeper_id", "product", "keywords"]].itertuples(index=False):
        for rank, word in enumerate([str(product), *str(keywords).split(",")]):
            for form in normalize_ingredient(word.strip()):
                index.setdefault(form, []).append((rank, int(fid)))
    names = dict(zip(foods["foodkeeper_id"], foods["name"]))
    rows = []
    for ingredient in dict.fromkeys(ingredients):
        candidates, head = index.get(ingredient), False
        if not candidates and " " in ingredient:
            candidates, head = index.get(ingredient.rsplit(" ", 1)[1]), True
        if not candidates:
            continue
        rank, fid = min(candidates)
        match = "head" if head else ("name" if rank == 0 else "keyword")
        n_best = len({f for r, f in candidates if r == rank})
        rows.append((ingredient, fid, names[fid], match, n_best))
    return pd.DataFrame(rows, columns=["ingredient", "foodkeeper_id", "foodkeeper_name", "match", "n_candidates"])


# ------------------------------------------------------------------ names across languages (section 2)
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
# The query service asks every tool for a descriptive User-Agent with a way to reach its authors
WIKIDATA_USER_AGENT = "EverFlavorAI/0.1 (student project; https://github.com/Chloe-Tu2/The-EverFlavor-AI)"
# Words in a Wikidata description that point to a food, used to rank candidates
FOOD_DESCRIPTION_WORDS = ["food", "dish", "ingredient", "spice", "herb", "vegetable", "fruit", "plant", "species",
                          "cultivar", "cheese", "meat", "sauce", "condiment", "beverage", "drink", "oil", "nut",
                          "seed", "grain", "cereal", "legume", "bean", "flour", "seasoning", "fish", "dairy",
                          "bread", "pasta", "sugar", "sweetener", "paste", "powder", "berry", "mushroom",
                          "edible", "culinary", "cooking", "baking", "leavening", "liquid", "juice", "vinegar"]
# Words that point away from a food ("protein-coding gene in the species ...")
NOT_FOOD_DESCRIPTION_WORDS = ["gene", "genetic", "element", "protein", "film", "album", "song", "band", "novel", "village", "surname",
                              "name", "painting", "journal", "asteroid", "ship", "company", "software", "episode",
                              "disambiguation", "single", "book", "character", "magazine", "river", "town",
                              "municipality", "article", "video", "game", "brand", "television", "vessel",
                              "container", "utensil", "tool", "dispenser"]


def _sparql(query: str, cache_dir: Path, refresh: bool = False, retries: int = 3) -> list[dict]:
    """Run one SPARQL query on Wikidata, cached by the query's hash; returns the result rows."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / (hashlib.sha1(query.encode("utf-8")).hexdigest()[:16] + ".json")
    if cache_file.exists() and not refresh:
        return json.loads(cache_file.read_text(encoding="utf-8"))
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(WIKIDATA_SPARQL, params={"query": query}, timeout=70,
                                    headers={"User-Agent": WIKIDATA_USER_AGENT,
                                             "Accept": "application/sparql-results+json"})
        except (requests.ConnectionError, requests.Timeout) as e:
            if attempt == retries:
                raise RuntimeError(f"Wikidata could not be reached ({type(e).__name__})") from None
            time.sleep(5 * attempt)
            continue
        if response.status_code in (429, 500, 502, 503, 504) and attempt < retries:
            time.sleep(float(response.headers.get("Retry-After", 5 * attempt)))
            continue
        response.raise_for_status()
        rows = [{k: v["value"] for k, v in b.items()} for b in response.json()["results"]["bindings"]]
        cache_file.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
        time.sleep(1)   # fair use of the public service
        return rows
    raise ValueError(f"retries must be at least 1, got {retries}")


def _quote(text: str) -> str:
    """Return a SPARQL string literal (quotes and backslashes escaped)."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _food_score(description: str) -> int:
    """Food words in a Wikidata description minus 3 per non-food word (0 or less: probably not a food)."""
    words = set(re.findall(r"[a-z]+", description.lower()))
    return sum(w in words for w in FOOD_DESCRIPTION_WORDS) - 3 * sum(w in words for w in NOT_FOOD_DESCRIPTION_WORDS)


def _wikidata_best(names: Sequence[str], cache_dir: Path, refresh: bool,
                   batch_size: int) -> dict[str, tuple[str | None, str, int, str]]:
    """For each name: (best food item, its description, candidates found, "exact" / "ranked" / "none")."""
    found: dict[str, list[tuple[str, str, str]]] = {n: [] for n in names}
    batches = [list(names[i:i + batch_size]) for i in range(0, len(names), batch_size)]
    for batch in progress_bar(batches, "Wikidata names", show=len(batches) > 3):
        values = " ".join(_quote(n) + "@en" for n in batch)
        query = f"""SELECT DISTINCT ?name ?item ?kind ?description WHERE {{
  VALUES ?name {{ {values} }}
  {{ ?item rdfs:label ?name BIND("label" AS ?kind) }} UNION {{ ?item skos:altLabel ?name BIND("alias" AS ?kind) }}
  OPTIONAL {{ ?item schema:description ?description FILTER(LANG(?description) = "en") }}
}}"""
        for row in _sparql(query, cache_dir, refresh):
            found[row["name"]].append((row["item"].rsplit("/", 1)[1], row.get("description", ""), row["kind"]))
    best: dict[str, tuple[str | None, str, int, str]] = {}
    for name, candidates in found.items():
        # Best first: a label (not only an alias), then the most food words, then the older item
        foods = sorted({c for c in candidates if _food_score(c[1]) > 0},
                       key=lambda c: (c[2] != "label", -_food_score(c[1]), int(c[0][1:])))
        if foods:
            best[name] = (foods[0][0], foods[0][1], len(candidates), "exact" if len(foods) == 1 else "ranked")
        else:
            best[name] = (None, "", len(candidates), "none")
    return best


def wikidata_matches(names: Sequence[str], cache_dir: str | Path, refresh: bool = False,
                     batch_size: int = 40) -> pd.DataFrame:
    """Find the Wikidata item for each English ingredient name (label or alias match), cached.

    Candidates are ranked: an English label before an alias, then by the food words
    in their description ("species of plant", "spice") minus non-food words ("gene",
    "film"), so "egg" finds the food, not a gene. A name with no match is tried
    again without its first words ("ground cinnamon" -> "cinnamon",
    "all-purpose flour" -> "flour"); those matches are marked "head".

    Args:
        names: Our ingredient names.
        cache_dir: Where each query's answer is saved.
        refresh: True asks Wikidata again instead of using saved answers.
        batch_size: Names per query (the service stops queries after 60 seconds).

    Returns:
        ingredient, wikidata_id, description, n_candidates, match: "exact" (one food
        candidate), "ranked" (several, the best kept), "head" (found by its last
        words) or "none". "ranked" and "head" go to a hand check.
    """
    cache_dir = Path(cache_dir)
    best = _wikidata_best(list(names), cache_dir, refresh, batch_size)
    # Shorter forms of the names nothing matched, longest first
    shorter = {n: [" ".join(n.replace("-", " ").split()[i:]) for i in range(1, len(n.replace("-", " ").split()))]
               for n, b in best.items() if b[3] == "none"}
    tails = list(dict.fromkeys(t for forms in shorter.values() for t in forms if t not in best))
    best.update(_wikidata_best(tails, cache_dir, refresh, batch_size) if tails else {})
    rows: list[tuple[str, str | None, str, int, str]] = []
    for name in names:
        item, description, n_candidates, match = best[name]
        if match == "none":
            tail = next((t for t in shorter.get(name, []) if best[t][3] != "none"), None)
            if tail is not None:
                item, description, n_candidates, _ = best[tail]
                match = "head"
        rows.append((name, item, description, n_candidates, match))
    return pd.DataFrame(rows, columns=["ingredient", "wikidata_id", "description", "n_candidates", "match"])


def names_in_languages(wikidata_ids: Sequence[str], languages: Sequence[str], cache_dir: str | Path,
                       refresh: bool = False, batch_size: int = 40) -> pd.DataFrame:
    """Labels and aliases of Wikidata items in `languages` (CC0), cached.

    Returns:
        wikidata_id, language, name, kind ("label" or "alias").
    """
    cache_dir = Path(cache_dir)
    ids = list(dict.fromkeys(i for i in wikidata_ids if i))
    langs = ", ".join(_quote(lang) for lang in languages)
    rows = []
    batches = [ids[i:i + batch_size] for i in range(0, len(ids), batch_size)]
    for batch in progress_bar(batches, "Wikidata labels", show=len(batches) > 3):
        values = " ".join(f"wd:{i}" for i in batch)
        query = f"""SELECT ?item ?name ?lang ?kind WHERE {{
  VALUES ?item {{ {values} }}
  {{ ?item rdfs:label ?name BIND("label" AS ?kind) }} UNION {{ ?item skos:altLabel ?name BIND("alias" AS ?kind) }}
  BIND(LANG(?name) AS ?lang)
  FILTER(?lang IN ({langs}))
}}"""
        for row in _sparql(query, cache_dir, refresh):
            rows.append((row["item"].rsplit("/", 1)[1], row["lang"], row["name"], row["kind"]))
    return pd.DataFrame(rows, columns=["wikidata_id", "language", "name", "kind"])
