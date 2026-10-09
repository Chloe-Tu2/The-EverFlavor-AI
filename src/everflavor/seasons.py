"""Meat seasons (notebook 08, section 3b): when meat is plentiful, and when animals graze fresh grass.

Farm animals are raised all year, so meat has no harvest season. Two different ideas are kept apart,
and neither is about freshness (fresh or spoiled: notebook 05; how long it keeps: notebook 04):

- **Supply season:** the months a meat is most plentiful in the US, from USDA ERS monthly slaughter
  counts (1907 on, no key). Each month's slaughter per working day is compared with its own year's
  average, and the median over recent years is kept, so growth, short months and odd years
  (2020) do not move the answer.
- **Pasture season:** the months grass usually grows at a place, from past weather (Open-Meteo,
  ERA5, no key). A month's grass score is a temperature factor times a moisture factor (rain against
  the water plants lose, over two months, since soil stores water). Between the tropics there is no
  pasture season: meat quality there depends on each farm, which we do not rate.

Wording for the agents: "most plentiful", "often finished on fresh pasture", never "better" or "fresher".
"""
from __future__ import annotations

import io
import math
import time
import zipfile
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np
import pandas as pd
import requests

__all__ = [
    "ERS_LIVESTOCK_URL",
    "ERS_SLAUGHTER_SERIES",
    "GRAZING_MEATS",
    "PASTURE_PLACES",
    "download_ers_livestock",
    "fetch_daily_weather",
    "grass_scores",
    "monthly_weather",
    "pasture_season",
    "read_ers_slaughter",
    "supply_index",
    "supply_seasons",
]

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

# ---------------------------------------------------------------- supply season (USDA ERS)
ERS_LIVESTOCK_URL = ("https://www.ers.usda.gov/media/5539/"
                     "livestock-domestic-data-machine-readable-files.zip")
_ERS_FILE = "Meat-Statistics.csv"
# meat -> (ERS commodity, attribute). Poultry is only reported as federally inspected.
ERS_SLAUGHTER_SERIES = {
    "beef": ("Cattle", "Commercial slaughter"),
    "veal": ("Calves", "Commercial slaughter"),
    "pork": ("Hogs", "Commercial slaughter"),
    "lamb": ("Lambs and yearlings", "Commercial slaughter"),
    "mutton": ("Mature sheep", "Commercial slaughter"),
    "chicken": ("Broilers", "Federally inspected slaughter"),
    "turkey": ("Turkey", "Federally inspected slaughter"),
}
SUPPLY_YEARS = 10           # recent complete years used
SUPPLY_PEAK = 1.05          # a month at least 5% above its year's average is a peak month
SUPPLY_LOW = 0.95           # ... at least 5% below is a low month
SUPPLY_STEADY_RANGE = 0.10  # highest minus lowest month under 10%: "steady all year"


def download_ers_livestock(folder: str | Path, refresh: bool = False, timeout: int = 120) -> Path:
    """Download USDA ERS's livestock machine-readable files (about 1 MB, cached).

    Args:
        folder: Where to keep the zip (data/raw/ers_livestock).
        refresh: Download again even if the zip is there.
        timeout: Seconds to wait for the download.

    Returns:
        The zip's path.
    """
    target = Path(folder) / "livestock-domestic-data-machine-readable-files.zip"
    if target.exists() and not refresh:
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(ERS_LIVESTOCK_URL, timeout=timeout)
    response.raise_for_status()
    zipfile.ZipFile(io.BytesIO(response.content)).testzip()   # fail now, not later, on a broken file
    partial = target.with_suffix(".part")
    partial.write_bytes(response.content)
    partial.replace(target)
    return target


def read_ers_slaughter(source: str | Path | pd.DataFrame,
                       series: Mapping[str, tuple[str, str]] = ERS_SLAUGHTER_SERIES) -> pd.DataFrame:
    """Monthly US slaughter for each meat: meat, year, month, thousand_head.

    Args:
        source: The ERS zip, its Meat-Statistics.csv, or that table already read.
        series: meat -> (ERS commodity, attribute), default ERS_SLAUGHTER_SERIES.

    Raises:
        ValueError: If the table lacks ERS's columns or has none of the series.
    """
    if isinstance(source, pd.DataFrame):
        table = source
    elif str(source).endswith(".zip"):
        with zipfile.ZipFile(source) as archive:
            name = next(n for n in archive.namelist() if n.endswith(_ERS_FILE))
            table = pd.read_csv(archive.open(name), low_memory=False)
    else:
        table = pd.read_csv(source, low_memory=False)
    needed = {"commodity_desc", "attribute_desc", "table_name", "year_id", "timeperiod_id", "amount"}
    if not needed <= set(table.columns):
        raise ValueError(f"not ERS Meat-Statistics: missing {sorted(needed - set(table.columns))}")
    rows = table[(table["table_name"] == "Livestock and poultry slaughter") & table["timeperiod_id"].between(1, 12)]
    parts = []
    for meat, (commodity, attribute) in series.items():
        part = rows[(rows["commodity_desc"] == commodity) & (rows["attribute_desc"] == attribute)]
        parts.append(pd.DataFrame({"meat": meat, "year": part["year_id"].astype(int),
                                   "month": part["timeperiod_id"].astype(int),
                                   "thousand_head": pd.to_numeric(part["amount"], errors="coerce")}))
    out = pd.concat(parts, ignore_index=True).dropna()
    if out.empty:
        raise ValueError("none of the slaughter series were found")
    return out.sort_values(["meat", "year", "month"], ignore_index=True)


def _working_days(year: pd.Series, month: pd.Series) -> np.ndarray:
    """Monday-Friday days in each month (packing plants mostly run on weekdays)."""
    start = pd.to_datetime(pd.DataFrame({"year": year, "month": month, "day": 1}))
    end = start + pd.offsets.MonthBegin(1)
    return np.busday_count(start.to_numpy().astype("datetime64[D]"), end.to_numpy().astype("datetime64[D]"))


def supply_index(slaughter: pd.DataFrame, years: int = SUPPLY_YEARS) -> pd.DataFrame:
    """How plentiful each meat usually is in each month, as a share of its year's average.

    Only complete years are used (all 12 months), the most recent `years` of them.

    Returns:
        meat, month, index (median over the years; 1.10 = 10% above average),
        years_above (share of years the month was above average), years.
    """
    if years < 1:
        raise ValueError(f"years must be at least 1, got {years}")
    data = slaughter.copy()
    complete = data.groupby(["meat", "year"])["month"].transform("nunique") == 12
    data = data[complete]
    recent = data.groupby("meat")["year"].transform(lambda y: y >= sorted(y.unique())[-min(years, y.nunique())])
    data = data[recent].copy()
    data["rate"] = data["thousand_head"] / _working_days(data["year"], data["month"])
    data["ratio"] = data["rate"] / data.groupby(["meat", "year"])["rate"].transform("mean")
    grouped = data.groupby(["meat", "month"])
    return pd.DataFrame({
        "index": grouped["ratio"].median(),
        "years_above": grouped["ratio"].apply(lambda r: float((r > 1).mean())),
        "years": grouped["year"].nunique(),
    }).reset_index()


def supply_seasons(index: pd.DataFrame) -> pd.DataFrame:
    """One line per meat: its pattern, peak months and low months, ready for the agents.

    A peak month is at least SUPPLY_PEAK of its year's average in the median year and above average
    in most years; a low month mirrors that. A meat whose months differ by less than
    SUPPLY_STEADY_RANGE is "steady all year" (no peaks reported).
    """
    rows = []
    for meat, part in index.groupby("meat"):
        part = part.sort_values("month")
        spread = float(part["index"].max() - part["index"].min())
        peaks = part[(part["index"] >= SUPPLY_PEAK) & (part["years_above"] > 0.5)]["month"].tolist()
        lows = part[(part["index"] <= SUPPLY_LOW) & (part["years_above"] < 0.5)]["month"].tolist()
        steady = spread < SUPPLY_STEADY_RANGE or not (peaks or lows)
        rows.append({
            "meat": meat,
            "pattern": "steady all year" if steady else "seasonal",
            "peak_months": [] if steady else peaks,
            "low_months": [] if steady else lows,
            "spread": round(spread, 3),
            "years": int(part["years"].min()),
            "source": "USDA ERS monthly slaughter, US",
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- pasture season (Open-Meteo)
OPEN_METEO_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
WEATHER_VARIABLES = ("temperature_2m_mean", "precipitation_sum", "et0_fao_evapotranspiration")
TROPICS_LATITUDE = 23.44    # between the tropics: no pasture season (quality depends on the farm)
# The four limits below were checked against known grazing months in 10 regions (Nebraska, Alberta,
# Ireland, Spain, Mongolia, Argentina, New Zealand, Australia, Texas, Arizona; 2015-2024 weather):
# 4 months off in 120 (with the 3-month rule), against 17 for a first guess (5-10 C, 0.3-0.7). Notebook 08, 3b.
GRASS_BASE_C = 4.0          # monthly mean at or below: grass does not grow (pasture grasses start near 4-5 C)
GRASS_FULL_C = 9.0          # at or above: temperature no longer limits growth
MOISTURE_NONE = 0.15        # rain / water loss over two months at or below: too dry (desert)
MOISTURE_FULL = 0.5         # at or above: water no longer limits (semi-arid grassland is about 0.2-0.5)
GRASS_MONTH_SCORE = 0.5     # a month with a usual score at or above this is a grass month
YEAR_ROUND_MONTHS = 11      # grass in this many months or more: grazing all year, no season
MIN_SEASON_MONTHS = 3       # a shorter green spell (desert after rain) cannot carry a grazing season
GRAZING_MEATS = ("beef", "veal", "lamb", "mutton", "goat", "bison", "venison")

# Grazing regions to describe (team can add more). Coordinates are a typical farm area, not a city center.
PASTURE_PLACES = {
    "Texas Gulf Coast (Houston)": (29.76, -95.37),
    "US Great Plains (Nebraska)": (41.26, -95.94),
    "Western Canada (Alberta)": (51.05, -114.07),
    "Ireland (Cork)": (51.90, -8.47),
    "Central Spain (Madrid)": (40.42, -3.70),
    "Mongolia (Ulaanbaatar)": (47.89, 106.91),
    "Argentina pampas (Buenos Aires)": (-34.60, -58.38),
    "New Zealand (Waikato)": (-37.79, 175.28),
    "Southeast Australia (Wagga Wagga)": (-35.12, 147.37),
    "US desert (Phoenix)": (33.45, -112.07),
    "East Africa highlands (Nairobi)": (-1.29, 36.82),
}


def fetch_daily_weather(latitude: float, longitude: float, start: str, end: str,
                        folder: str | Path | None = None, refresh: bool = False,
                        max_waits: int = 5, timeout: int = 120) -> pd.DataFrame:
    """Daily mean temperature, rain and reference water loss (ET0) for a place (Open-Meteo, cached).

    Open-Meteo is free for non-commercial use, needs no key and asks for attribution (CC BY 4.0).
    Long ranges count as many requests: when it says the per-minute limit is reached, this waits a
    minute and tries again, up to `max_waits` times.

    Args:
        latitude, longitude: The place.
        start, end: First and last day, "YYYY-MM-DD".
        folder: Keep a CSV per place and range here; None skips the cache.
        refresh: Download again even if the CSV is there.
        max_waits: Most one-minute waits for the rate limit.
        timeout: Seconds to wait for each request.

    Returns:
        date, temperature_2m_mean, precipitation_sum, et0_fao_evapotranspiration.

    Raises:
        ValueError: If the place is not a valid latitude / longitude.
        RuntimeError: If Open-Meteo still refuses after the waits.
    """
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError(f"not a place on Earth: {latitude}, {longitude}")
    cache = None
    if folder is not None:
        cache = Path(folder) / f"weather_{latitude:.2f}_{longitude:.2f}_{start}_{end}.csv"
        if cache.exists() and not refresh:
            return pd.read_csv(cache, parse_dates=["date"])
    params: dict[str, str | float] = {"latitude": latitude, "longitude": longitude, "start_date": start, "end_date": end,
              "daily": ",".join(WEATHER_VARIABLES), "timezone": "GMT"}
    for attempt in range(max_waits + 1):
        data = requests.get(OPEN_METEO_ARCHIVE, params=params, timeout=timeout).json()
        if not data.get("error"):
            break
        if "limit" not in str(data.get("reason", "")).lower() or attempt == max_waits:
            raise RuntimeError(f"Open-Meteo: {data.get('reason')}")
        time.sleep(61)
    daily = pd.DataFrame(data["daily"]).rename(columns={"time": "date"})
    daily["date"] = pd.to_datetime(daily["date"])
    if cache is not None:
        cache.parent.mkdir(parents=True, exist_ok=True)
        daily.to_csv(cache, index=False)
    return daily


def monthly_weather(daily: pd.DataFrame) -> pd.DataFrame:
    """Daily weather to months: year, month, temp_c (mean), rain_mm, et0_mm (sums), days."""
    needed = {"date", *WEATHER_VARIABLES}
    if not needed <= set(daily.columns):
        raise ValueError(f"daily weather is missing {sorted(needed - set(daily.columns))}")
    dates = pd.to_datetime(daily["date"])
    grouped = daily.groupby([dates.dt.year.rename("year"), dates.dt.month.rename("month")])
    return pd.DataFrame({
        "temp_c": grouped["temperature_2m_mean"].mean(),
        "rain_mm": grouped["precipitation_sum"].sum(min_count=1),
        "et0_mm": grouped["et0_fao_evapotranspiration"].sum(min_count=1),
        "days": grouped["temperature_2m_mean"].count(),
    }).reset_index()


def _ramp(value: pd.Series, low: float, high: float) -> pd.Series:
    """0 at or below `low`, 1 at or above `high`, a straight line between."""
    return ((value - low) / (high - low)).clip(0, 1)


def grass_scores(monthly: pd.DataFrame) -> pd.DataFrame:
    """How well grass usually grows in each calendar month (0 = not at all, 1 = fully).

    Each month of each year gets temperature factor x moisture factor; the moisture factor uses that
    month and the one before (rain stored in the soil carries over), on the real calendar, so January
    uses the previous December. Months with fewer than 25 days of data are dropped. The usual score
    is the mean over the years.

    Returns:
        month, score, temp_c, moisture (rain / water loss), years.
    """
    data = monthly.copy()
    data.loc[data["days"] < 25, ["temp_c", "rain_mm", "et0_mm"]] = np.nan   # a partial month counts as missing
    firsts = pd.to_datetime(pd.DataFrame({"year": data["year"], "month": data["month"], "day": 1}))
    data.index = pd.PeriodIndex(firsts, freq="M")
    data = data[~data.index.duplicated()].sort_index()
    if data["temp_c"].notna().sum() == 0:
        raise ValueError("no complete months of weather")
    calendar = pd.period_range(data.index.min(), data.index.max(), freq="M")
    data = data.reindex(calendar)   # gaps become missing
    rain2 = data["rain_mm"] + data["rain_mm"].shift(1)
    et02 = data["et0_mm"] + data["et0_mm"].shift(1)
    data["moisture"] = rain2 / et02.where(et02 > 0)
    data["score"] = _ramp(data["temp_c"], GRASS_BASE_C, GRASS_FULL_C) * _ramp(data["moisture"], MOISTURE_NONE,
                                                                              MOISTURE_FULL)
    data["year"], data["month"] = calendar.year, calendar.month
    data = data.dropna(subset=["score"])
    grouped = data.groupby("month")
    return pd.DataFrame({
        "score": grouped["score"].mean().round(3),
        "temp_c": grouped["temp_c"].mean().round(1),
        "moisture": grouped["moisture"].median().round(2),
        "years": grouped["year"].nunique(),
    }).reindex(range(1, 13)).rename_axis("month").reset_index()


def _season_runs(months: Sequence[int]) -> list[list[int]]:
    """Runs of consecutive months, December joining January (Nov, Dec, Jan is one run)."""
    chosen = set(months)
    if len(chosen) == 12:
        return [list(range(1, 13))]
    runs = []
    for start in sorted(chosen):
        if (start - 2) % 12 + 1 in chosen:      # not the first month of a run
            continue
        run, month = [], start
        while month in chosen:
            run.append(month)
            month = month % 12 + 1
        runs.append(run)
    return runs


def _months_text(months: Sequence[int]) -> str:
    return ", ".join(MONTHS[m - 1] for m in months)


def pasture_season(latitude: float, scores: pd.DataFrame | None = None) -> dict:
    """The pasture season at a place, ready for the agents.

    Args:
        latitude: The place's latitude (decides the tropics rule).
        scores: `grass_scores` for the place; not needed between the tropics.

    Returns:
        {"basis": "tropics" | "year-round grass" | "no grass season" | "seasonal",
        "grass_months" (1-12), "finishing_months" (grass months that follow a grass month: animals
        have grazed fresh grass for weeks, which is what changes the meat), "text"}.
    """
    if not -90 <= latitude <= 90:
        raise ValueError(f"not a latitude: {latitude}")
    if math.fabs(latitude) < TROPICS_LATITUDE:
        return {"basis": "tropics", "grass_months": [], "finishing_months": [],
                "text": "Between the tropics: no pasture season; meat quality depends on each farm."}
    if scores is None:
        raise ValueError("grass scores are needed outside the tropics")
    usual = scores.dropna(subset=["score"])
    green = [int(m) for m in usual.loc[usual["score"] >= GRASS_MONTH_SCORE, "month"]]
    grass = sorted(m for run in _season_runs(green) if len(run) >= MIN_SEASON_MONTHS for m in run)
    if len(grass) >= YEAR_ROUND_MONTHS:
        return {"basis": "year-round grass", "grass_months": grass, "finishing_months": grass,
                "text": "Grass grows almost all year: animals can graze year-round; quality depends on each farm."}
    if not grass:
        return {"basis": "no grass season", "grass_months": [], "finishing_months": [],
                "text": "Too cold or dry for pasture grass most of the year: animals are mostly fed."}
    finishing = [m for m in grass if (m - 2) % 12 + 1 in grass]
    return {"basis": "seasonal", "grass_months": grass, "finishing_months": finishing,
            "text": f"Fresh grass usually grows {_months_text(grass)}; grass-fed meat is often finished on "
                    f"pasture in {_months_text(finishing or grass)}."}
