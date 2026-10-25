"""Cook-time estimates for recipes that do not state their time.

Food.com recipes carry their total minutes; Hugging Face, CulinaryDB and TheMealDB do not. This module fills the
gap with a measured estimate and says where each time came from (minutes_source), so the app can label it and a
real time is never replaced:

- parse_step_minutes() reads the times written in the steps ("bake 30 minutes", "1 1/2 hours", "2-3 hrs").
- fit_time_model() fits two gradient boosting models on log minutes, using Food.com train recipes with 1 to 1,440
  minutes: one for recipes with steps (step count, ingredient count, times in the steps, cooking-method words,
  name words, the median time of the 80 most similar Food.com names) and one for recipes with only a name and
  ingredients (ingredient count, name words, name neighbors).
- estimate_minutes() gives minutes_estimate and minutes_source for every row; time_label() is the text to show.

Measured in docs/plans/COOKING_STEPS_AND_VIDEOS.md ("Estimating missing times: measured", Food.com test split):
with steps, median error 8 min and 83.7% between half and double the real time; without steps, 12 min and 73.7%
(the plan baseline, median by step and ingredient count: 15 min, 68.7%). Over 4 hours only 38% of the no-steps
estimates are within half to double, so the label then says "Several hours (estimate)".

"Overnight" is not counted as minutes: Food.com authors usually leave waiting out of the total (recipes that say
"overnight" have a median of 65 minutes), so it is a feature word only.

Policy (P26, team decision): an estimate is for showing only; it is never used to sort or filter as if it were
a real time. The name neighbors come from Food.com train names only, and each train recipe leaves itself out, so
no recipe sees its own time.
"""
from __future__ import annotations

import re
import warnings
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.feature_extraction.text import TfidfVectorizer

from .checks import require_columns

__all__ = [
    "FEATURES_NO_STEPS",
    "FEATURES_WITH_STEPS",
    "MAX_PLAUSIBLE_MINUTES",
    "METHOD_WORDS",
    "NAME_WORDS",
    "SEVERAL_HOURS",
    "TimeModel",
    "estimate_minutes",
    "fit_time_model",
    "parse_step_minutes",
    "round_minutes",
    "time_features",
    "time_label",
]

MIN_PLAUSIBLE_MINUTES = 1
MAX_PLAUSIBLE_MINUTES = 1440          # 24 hours: longer Food.com times are typing mistakes or "days" of waiting
SEVERAL_HOURS = 240                   # estimates above 4 hours are shown as "Several hours (estimate)"
NEIGHBORS = 80                        # k = 80 was best on val (72.8% half to double for names alone)
RANDOM_STATE = 0

# ---------- times written in the steps ----------
_WORD_NUMBERS: dict[str, float] = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20,
    "thirty": 30, "forty": 40, "forty-five": 45, "sixty": 60, "half": 0.5, "a half": 0.5,
    "several": 3, "few": 3, "a few": 3, "couple": 2, "a couple": 2, "couple of": 2, "a couple of": 2,
}
_NUMBER = (r"(?:\d+\s+\d/\d|\d+/\d+|\d+(?:\.\d+)?|"
           + "|".join(sorted(map(re.escape, _WORD_NUMBERS), key=len, reverse=True)) + r")")
_UNIT = r"(minutes?|mins?|m\b|hours?|hrs?|h\b|seconds?|secs?|days?)"
_DURATION = re.compile(
    rf"\b(?:about\s+|approx\.?\s+|approximately\s+)?({_NUMBER})(?:\s*(?:-|to|or|–)\s*({_NUMBER}))?\s*"
    rf"(?:more\s+|additional\s+|extra\s+)?{_UNIT}(?:\s+and\s+(?:a\s+)?half)?", re.IGNORECASE)
_HALF_HOUR = re.compile(r"\b(?:a\s+)?half(?:\s+an)?\s+hour\b", re.IGNORECASE)
_OVERNIGHT = re.compile(r"\bovernight\b", re.IGNORECASE)
# TheMealDB puts "step 1" (or just "1.") on its own line before each paragraph: a heading, not a step.
_STEP_HEADING = re.compile(r"^\s*(?:step\s*)?\d+\s*[.):]?\s*$", re.IGNORECASE)
_LONGEST_STEP_TIME = 3 * 1440         # a single time over 3 days is not a cooking time

# Cooking-method words in the steps and dish words in the name (features of the models).
METHOD_WORDS: dict[str, str] = {
    "bake": r"\bbak|\boven\b", "simmer": r"\bsimmer", "boil": r"\bboil", "fry": r"\bfry|\bfried|\bsaut",
    "grill": r"\bgrill|\bbarbecue|\bbbq", "slow_cooker": r"slow cook|crock ?pot|crockpot",
    "marinate": r"marinat", "overnight": r"overnight", "refrigerate": r"refrigerat|chill|fridge|freez",
    "rise": r"\brise|\brisen|doubled in (?:size|bulk)|\bknead|\byeast", "roast": r"\broast",
    "blend": r"\bblend|\bprocessor|\bshake|\bstir together", "microwave": r"microwave",
    "pressure": r"pressure cook|instant pot", "smoke": r"\bsmok", "brine": r"\bbrine",
}
NAME_WORDS: dict[str, str] = {
    "slow_cooker": r"slow cook|crock ?pot|crockpot",
    "bread": r"bread|\broll|\bbun|dough|brioche|focaccia",
    "cake": r"cake|pie|tart|cookie|brownie|muffin",
    "drink": r"smoothie|shake|cocktail|punch|lemonade|tea\b|coffee",
    "salad": r"salad|dip|salsa|dressing|sauce",
    "roast": r"roast|brisket|pulled|ribs|stew|braise",
    "marinated": r"marinat|jerky|pickle|cured",
}
_METHOD_COLUMNS = ["m_" + key for key in METHOD_WORDS]
_NAME_COLUMNS = ["n_" + key for key in NAME_WORDS]
_NEIGHBOR_COLUMNS = ["knn", "knn_top", "knn_iqr"]
FEATURES_WITH_STEPS: list[str] = (["n_steps", "complexity", "dur_sum", "dur_maxsum", "dur_steps", "ins_len"]
                                  + _NEIGHBOR_COLUMNS + _METHOD_COLUMNS + _NAME_COLUMNS)
FEATURES_NO_STEPS: list[str] = ["complexity"] + _NEIGHBOR_COLUMNS + _NAME_COLUMNS


def _number(text: str) -> float:
    text = text.lower().strip()
    if text in _WORD_NUMBERS:
        return _WORD_NUMBERS[text]
    if " " in text and "/" in text:
        whole, fraction = text.split()
        top, bottom = fraction.split("/")
        return float(whole) + (float(top) / float(bottom) if float(bottom) else 0.0)
    if "/" in text:
        top, bottom = text.split("/")
        return float(top) / float(bottom) if float(bottom) else 0.0
    return float(text)


def _unit_minutes(unit: str) -> float:
    unit = unit.lower()
    if unit.startswith("d"):
        return 1440.0
    if unit.startswith("h"):
        return 60.0
    if unit.startswith("s"):
        return 1 / 60
    return 1.0


def _step_times(step: str) -> list[float]:
    """Every time written in one step, in minutes (a range counts as its middle: "2-3 hrs" -> 150)."""
    times = []
    step = _HALF_HOUR.sub(" 30 minutes", step)
    for match in _DURATION.finditer(step):
        low = _number(match.group(1))
        high = _number(match.group(2)) if match.group(2) else low
        unit = _unit_minutes(match.group(3))
        value = (low + high) / 2 * unit
        if re.search(r"and (?:a )?half", match.group(0), re.IGNORECASE):
            value += 0.5 * unit
        if 0 < value <= _LONGEST_STEP_TIME:
            times.append(value)
    return times


def _split_steps(instructions: object) -> list[str]:
    if not isinstance(instructions, str):
        return []
    lines = re.split(r"\r?\n", instructions)
    return [line for line in lines if line.strip() and not _STEP_HEADING.match(line)]


def parse_step_minutes(instructions: object) -> dict[str, float]:
    """The times written in a recipe's steps.

    Steps are lines: Food.com writes one step per line; TheMealDB writes a paragraph per step, sometimes after a
    "step 1" heading line (dropped). A step with several times ("fry 5 min, then bake 30 minutes") adds all of
    them to dur_sum and only its largest to dur_maxsum, so a step that repeats a time is not counted twice.

    Args:
        instructions: The recipe's instructions text (None or NaN for none).

    Returns:
        n_steps (steps found), dur_sum (all times, minutes), dur_maxsum (largest time per step, summed),
        dur_steps (steps with a time) and overnight_steps (steps that say "overnight", not counted as minutes).
    """
    total = per_step_max = 0.0
    with_time = overnight = 0
    steps = _split_steps(instructions)
    for step in steps:
        times = _step_times(step)
        if times:
            with_time += 1
            total += sum(times)
            per_step_max += max(times)
        if _OVERNIGHT.search(step):
            overnight += 1
    return {"n_steps": float(len(steps)), "dur_sum": total, "dur_maxsum": per_step_max,
            "dur_steps": float(with_time), "overnight_steps": float(overnight)}


def time_features(df: pd.DataFrame) -> pd.DataFrame:
    """The step, method-word and name-word features of each recipe (no name neighbors; the model adds those).

    Args:
        df: Recipes with recipe_name; instructions and complexity (ingredient count) are used when present.

    Returns:
        One row per recipe, same index, with the parse_step_minutes() columns, ins_len, complexity, m_* and n_*.
    """
    require_columns(df, ["recipe_name"], "time_features")
    instructions = (df["instructions"] if "instructions" in df.columns else pd.Series("", index=df.index))
    instructions = instructions.fillna("").astype(str)
    names = df["recipe_name"].fillna("").astype(str).str.lower()
    parsed = pd.DataFrame([parse_step_minutes(text) for text in instructions.to_numpy()], index=df.index)
    out = parsed.drop(columns="overnight_steps")
    out["ins_len"] = instructions.str.len().astype(float)
    complexity = df["complexity"] if "complexity" in df.columns else pd.Series(np.nan, index=df.index)
    out["complexity"] = pd.to_numeric(complexity, errors="coerce").astype(float)
    lowered = instructions.str.lower()
    for key, pattern in METHOD_WORDS.items():
        out["m_" + key] = lowered.str.contains(pattern, regex=True).astype(np.int8)
    for key, pattern in NAME_WORDS.items():
        out["n_" + key] = names.str.contains(pattern, regex=True).astype(np.int8)
    return out


# ---------- the model ----------
@dataclass
class TimeModel:
    """Two fitted models and the name index of the training recipes (from fit_time_model)."""

    vectorizer: TfidfVectorizer
    train_names: Any                  # sparse TF-IDF matrix of the training names (rows = training recipes)
    train_minutes: np.ndarray
    global_median: float
    with_steps: HistGradientBoostingRegressor
    without_steps: HistGradientBoostingRegressor
    neighbors: int = NEIGHBORS
    memory_mb: int = 256

    def name_neighbors(self, names: Iterable[str], exclude_self: bool = False) -> pd.DataFrame:
        """Median, top similarity and spread (IQR) of the minutes of the most similar training names.

        The search runs in chunks sized to memory_mb (dense similarity block plus its indices), so even all
        Food.com train names against themselves stay within a few hundred MB.

        Args:
            names: Recipe names.
            exclude_self: True only for the training names themselves, in training order: each one then leaves
                itself out.

        Returns:
            Columns knn (NaN when no name shares a word), knn_top and knn_iqr.
        """
        matrix = self.vectorizer.transform([str(name) for name in names])
        rows, columns = matrix.shape[0], self.train_names.shape[0]
        median = np.full(rows, np.nan)
        top = np.zeros(rows)
        spread = np.zeros(rows)
        if rows == 0 or columns == 0:
            return pd.DataFrame({"knn": median, "knn_top": top, "knn_iqr": spread})
        k = min(self.neighbors, columns)
        kth = min(k + int(exclude_self), columns - 1)
        # Bytes per similarity cell: the float32 block, its negated copy and argpartition's copy, int64 indices.
        chunk = max(1, int(self.memory_mb * 2**20 // (columns * 24)))
        transposed = self.train_names.T
        for start in range(0, rows, chunk):
            block = (matrix[start:start + chunk] @ transposed).toarray().astype(np.float32, copy=False)
            if exclude_self:
                local = np.arange(block.shape[0])
                block[local, start + local] = -1.0
            if k < columns:
                index = np.argpartition(-block, kth, axis=1)[:, :k]
            else:
                index = np.broadcast_to(np.arange(columns), (block.shape[0], columns))
            sims = np.take_along_axis(block, index, axis=1)
            minutes = np.where(sims > 0, self.train_minutes[index], np.nan)
            end = start + block.shape[0]
            found = (sims > 0).any(axis=1)
            if found.any():
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", RuntimeWarning)
                    median[start:end] = np.nanmedian(minutes, axis=1)
                    q25, q75 = np.nanpercentile(minutes, [25, 75], axis=1)
                spread[start:end] = np.nan_to_num(q75 - q25)
            top[start:end] = np.maximum(sims.max(axis=1), 0.0)
        return pd.DataFrame({"knn": median, "knn_top": top, "knn_iqr": spread})


def _plausible(minutes: pd.Series) -> pd.Series:
    values = pd.to_numeric(minutes, errors="coerce")
    return (values >= MIN_PLAUSIBLE_MINUTES) & (values <= MAX_PLAUSIBLE_MINUTES)


def _with_neighbors(features: pd.DataFrame, neighbors: pd.DataFrame, global_median: float) -> pd.DataFrame:
    out = features.copy()
    out["knn"] = neighbors["knn"].fillna(global_median).to_numpy()
    out["knn_top"] = neighbors["knn_top"].to_numpy()
    out["knn_iqr"] = neighbors["knn_iqr"].to_numpy()
    return out


def _booster(random_state: int) -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(loss="absolute_error", max_iter=400, learning_rate=0.08,
                                         max_leaf_nodes=63, min_samples_leaf=50, random_state=random_state)


def fit_time_model(train_df: pd.DataFrame, neighbors: int = NEIGHBORS, random_state: int = RANDOM_STATE,
                   memory_mb: int = 256) -> TimeModel:
    """Fit the cook-time estimator on training recipes with real times.

    Uses the Food.com rows (all rows when there is no source column) whose minutes are 1 to 1,440. Fit on the
    train split only. On the full Food.com train split (about 152,000 recipes) the leave-self-out name search
    takes a few minutes.

    Args:
        train_df: Training recipes with recipe_name, minutes, instructions and complexity.
        neighbors: How many similar names give the neighbor median (80, measured).
        random_state: Seed of the gradient boosting models, so a refit gives the same estimates.
        memory_mb: Memory for one chunk of the name search.

    Returns:
        The fitted TimeModel.

    Raises:
        ValueError: When a column is missing or no row has a plausible time.
    """
    require_columns(train_df, ["recipe_name", "minutes", "instructions", "complexity"], "fit_time_model")
    rows = train_df
    if "source" in rows.columns:
        rows = rows[rows["source"] == "foodcom"]
    rows = rows[_plausible(rows["minutes"])]
    if rows.empty:
        raise ValueError("fit_time_model() found no Food.com recipe with 1 to 1,440 minutes to learn from.")
    names = rows["recipe_name"].fillna("").astype(str).to_numpy()
    minutes = rows["minutes"].astype(float).to_numpy()
    min_df = 2 if len(rows) >= 50 else 1
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=min_df, dtype=np.float32)
    train_names = vectorizer.fit_transform(names)
    global_median = float(np.median(minutes))
    model = TimeModel(vectorizer=vectorizer, train_names=train_names, train_minutes=minutes,
                      global_median=global_median, with_steps=_booster(random_state),
                      without_steps=_booster(random_state), neighbors=neighbors, memory_mb=memory_mb)
    features = _with_neighbors(time_features(rows), model.name_neighbors(names, exclude_self=True), global_median)
    target = np.log1p(minutes)
    model.with_steps.fit(features[FEATURES_WITH_STEPS].fillna(0).to_numpy(), target)
    model.without_steps.fit(features[FEATURES_NO_STEPS].fillna(0).to_numpy(), target)
    return model


def round_minutes(minutes: float | None) -> float:
    """Display rounding of an estimate: to 5 minutes under an hour (at least 5), to 15 minutes above."""
    if minutes is None or not np.isfinite(minutes):
        return float("nan")
    if minutes < 60:
        return float(max(5, 5 * round(minutes / 5)))
    return float(15 * round(minutes / 15))


def estimate_minutes(model: TimeModel, df: pd.DataFrame) -> pd.DataFrame:
    """minutes_estimate and minutes_source for each recipe; real times are never replaced.

    minutes_source is "recipe" when the recipe's own minutes are 1 to 1,440 (minutes_estimate is then empty,
    the app shows minutes), "estimate_steps" when it has steps, "estimate_name" when it has only a name and
    ingredients, and "unknown" when there is nothing to go on (no steps, no similar name, no ingredient count).

    Args:
        model: From fit_time_model().
        df: Recipes with recipe_name; minutes, instructions and complexity are used when present.

    Returns:
        A dataframe with the same index: minutes_estimate (float, rounded with round_minutes) and minutes_source.
    """
    require_columns(df, ["recipe_name"], "estimate_minutes")
    out = pd.DataFrame({"minutes_estimate": np.nan, "minutes_source": "unknown"}, index=df.index)
    real = (_plausible(df["minutes"]) if "minutes" in df.columns
            else pd.Series(False, index=df.index)).fillna(False).astype(bool)
    out.loc[real, "minutes_source"] = "recipe"
    todo = df[~real]
    if todo.empty:
        return out
    features = time_features(todo)
    neighbors = model.name_neighbors(todo["recipe_name"].fillna("").astype(str).to_numpy())
    found = neighbors["knn"].notna().to_numpy()
    features = _with_neighbors(features, neighbors, model.global_median)
    has_steps = features["n_steps"].to_numpy() > 0
    has_count = features["complexity"].fillna(0).to_numpy() > 0
    by_name = ~has_steps & (found | has_count)
    estimate = np.full(len(todo), np.nan)
    if has_steps.any():
        rows = features.loc[has_steps, FEATURES_WITH_STEPS].fillna(0).to_numpy()
        estimate[has_steps] = np.expm1(model.with_steps.predict(rows))
    if by_name.any():
        rows = features.loc[by_name, FEATURES_NO_STEPS].fillna(0).to_numpy()
        estimate[by_name] = np.expm1(model.without_steps.predict(rows))
    source = np.where(has_steps, "estimate_steps", np.where(by_name, "estimate_name", "unknown"))
    out.loc[todo.index, "minutes_estimate"] = [round_minutes(value) for value in estimate]
    out.loc[todo.index, "minutes_source"] = source
    return out


def _hours_and_minutes(minutes: int) -> str:
    if minutes < 60:
        return f"{minutes} min"
    hours, rest = divmod(minutes, 60)
    return f"{hours} h {rest} min" if rest else f"{hours} h"


def time_label(minutes: float | None, source: str | None) -> str:
    """The cook time as the app shows it.

    Args:
        minutes: The recipe's own minutes when source is "recipe", else minutes_estimate.
        source: minutes_source ("recipe", "estimate_steps", "estimate_name" or "unknown").

    Returns:
        "35 min" for a real time, "About 40 min (estimated from similar recipes)" for an estimate (rounded to
        5 min under an hour, 15 min above), "Several hours (estimate)" for an estimate over 4 hours, and "" when
        the time is unknown.
    """
    if minutes is None or source not in ("recipe", "estimate_steps", "estimate_name"):
        return ""
    try:
        value = float(minutes)
    except (TypeError, ValueError):
        return ""
    if not np.isfinite(value) or value <= 0:
        return ""
    if source == "recipe":
        return _hours_and_minutes(max(1, round(value)))
    rounded = round_minutes(value)
    if rounded > SEVERAL_HOURS:
        return "Several hours (estimate)"
    return f"About {_hours_and_minutes(int(rounded))} (estimated from similar recipes)"
