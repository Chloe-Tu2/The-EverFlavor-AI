"""Tests for meat seasons (src/everflavor/seasons.py) with made-up numbers: no downloads.

Run with `python -m pytest tests`, or alone:

    python tests/test_seasons.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor import seasons


def slaughter(pattern, years=range(2015, 2025), meat="lamb", growth=0.0):
    """Monthly head counts: per-working-day rate = pattern[month] x yearly growth."""
    rows = []
    for k, year in enumerate(years):
        for month in range(1, 13):
            days = seasons._working_days(pd.Series([year]), pd.Series([month]))[0]
            rows.append({"meat": meat, "year": year, "month": month,
                         "thousand_head": pattern[month - 1] * (1 + growth) ** k * days})
    return pd.DataFrame(rows)


def test_read_ers_slaughter_picks_the_series():
    table = pd.DataFrame({
        "commodity_desc": ["Lambs and yearlings", "Lambs and yearlings", "Cattle", "Lambs and yearlings"],
        "attribute_desc": ["Commercial slaughter", "Federally inspected slaughter", "Commercial slaughter",
                           "Commercial slaughter"],
        "table_name": ["Livestock and poultry slaughter"] * 4,
        "unit_desc": ["thousand head"] * 4,
        "year_id": [2024, 2024, 2024, 2024], "timeperiod_id": [3, 3, 3, 101], "amount": [200, 190, 2500, 2300]})
    out = seasons.read_ers_slaughter(table)
    assert set(out["meat"]) == {"lamb", "beef"} and len(out) == 2   # 101 = the year total, dropped
    with pytest.raises(ValueError):
        seasons.read_ers_slaughter(pd.DataFrame({"a": [1]}))


def test_supply_finds_peaks_and_ignores_growth_and_short_months():
    easter = [0.9, 0.97, 1.12, 1.10, 1.0, 1.0, 0.97, 1.0, 0.98, 0.98, 0.99, 0.99]
    index = seasons.supply_index(slaughter(easter, growth=0.05))   # 5% growth a year changes nothing
    assert index.loc[index["month"] == 3, "index"].iloc[0] == pytest.approx(1.12, abs=0.01)
    row = seasons.supply_seasons(index).iloc[0]
    assert row["pattern"] == "seasonal" and row["peak_months"] == [3, 4] and row["low_months"] == [1]


def test_supply_steady_meat_has_no_peaks():
    flat = [1.0, 1.01, 0.99, 1.0, 1.02, 0.98, 1.0, 1.01, 0.99, 1.0, 1.0, 1.0]
    row = seasons.supply_seasons(seasons.supply_index(slaughter(flat, meat="chicken"))).iloc[0]
    assert row["pattern"] == "steady all year" and row["peak_months"] == []


def test_supply_uses_only_recent_complete_years():
    data = slaughter([1.0] * 12, years=range(2000, 2026))
    data = data[~((data["year"] == 2025) & (data["month"] > 8))]   # 2025 not finished yet
    index = seasons.supply_index(data, years=10)
    assert index["years"].max() == 10
    with pytest.raises(ValueError):
        seasons.supply_index(data, years=0)


def weather(temps, rains, et0s, years=range(2015, 2025)):
    """Daily weather with the same monthly means every year (rain and ET0 are monthly totals)."""
    frames = []
    for year in years:
        for month in range(1, 13):
            days = pd.date_range(f"{year}-{month:02d}-01", periods=pd.Period(f"{year}-{month:02d}").days_in_month)
            frames.append(pd.DataFrame({"date": days, "temperature_2m_mean": temps[month - 1],
                                        "precipitation_sum": rains[month - 1] / len(days),
                                        "et0_fao_evapotranspiration": et0s[month - 1] / len(days)}))
    return pd.concat(frames, ignore_index=True)


def test_grass_scores_need_warmth_and_water():
    temps = [-5, -2, 3, 9, 14, 19, 22, 21, 16, 10, 3, -3]           # cold winters (Great Plains)
    rains = [20, 20, 50, 80, 110, 60, 30, 30, 60, 40, 30, 20]       # dry summer
    et0s = [10, 15, 40, 80, 110, 140, 150, 130, 90, 50, 20, 10]
    scores = seasons.grass_scores(seasons.monthly_weather(weather(temps, rains, et0s)))
    by_month = scores.set_index("month")["score"]
    assert by_month[1] == 0 and by_month[5] > 0.9                    # frozen January, green May
    assert by_month[7] < by_month[5]                                 # summer dries out
    season = seasons.pasture_season(41.0, scores)
    assert season["basis"] == "seasonal" and 1 not in season["grass_months"] and 5 in season["grass_months"]
    assert set(season["finishing_months"]) < set(season["grass_months"])   # the first grass month is not a finish


def test_southern_hemisphere_comes_from_the_weather_itself():
    temps = [18, 18, 16, 13, 10, 7, 6, 7, 9, 12, 14, 17]             # New Zealand: mild, wet winters
    rains = [80, 70, 90, 100, 120, 130, 140, 120, 110, 100, 90, 90]
    et0s = [130, 110, 85, 55, 35, 25, 25, 35, 55, 85, 110, 130]
    season = seasons.pasture_season(-37.8, seasons.grass_scores(seasons.monthly_weather(weather(temps, rains, et0s))))
    assert season["basis"] in ("seasonal", "year-round grass") and 10 in season["grass_months"]


def test_tropics_dry_and_year_round_rules():
    assert seasons.pasture_season(-1.3)["basis"] == "tropics"        # no weather needed
    with pytest.raises(ValueError):
        seasons.pasture_season(45.0)
    desert = weather([12, 14, 18, 22, 27, 32, 35, 34, 31, 24, 17, 12], [20] * 12, [80, 100, 150, 200, 250, 280,
                                                                                   280, 250, 200, 150, 100, 80])
    assert seasons.pasture_season(33.4, seasons.grass_scores(seasons.monthly_weather(desert)))["basis"] == \
        "no grass season"
    mild = weather([8, 8, 9, 11, 13, 15, 17, 17, 15, 12, 10, 9], [100] * 12, [15, 25, 45, 65, 90, 100, 100, 85,
                                                                                 60, 35, 20, 15])
    assert seasons.pasture_season(51.9, seasons.grass_scores(seasons.monthly_weather(mild)))["basis"] == \
        "year-round grass"


def test_short_green_spells_are_not_a_season():
    assert seasons._season_runs([11, 12, 1, 5]) == [[5], [11, 12, 1]]
    scores = pd.DataFrame({"month": range(1, 13), "score": [0.9, 0.8] + [0.0] * 8 + [0.0, 0.0]})
    assert seasons.pasture_season(33.4, scores)["basis"] == "no grass season"   # 2 green months after winter rain
    scores["score"] = [0.9, 0.0, 0.7, 0.8, 0.9, 0.0, 0.0, 0.0, 0.0, 0.6, 0.7, 0.8]
    season = seasons.pasture_season(40.4, scores)                                  # Madrid: spring and autumn
    assert season["grass_months"] == [1, 3, 4, 5, 10, 11, 12] and season["finishing_months"] == [1, 4, 5, 11, 12]


def test_partial_months_and_gaps_do_not_count():
    daily = weather([10] * 12, [100] * 12, [50] * 12, years=[2020, 2021])
    daily = daily[~((daily["date"].dt.year == 2020) & (daily["date"].dt.month == 6) & (daily["date"].dt.day > 10))]
    daily = daily[~((daily["date"].dt.year == 2021) & (daily["date"].dt.month == 3))]   # a whole month missing
    scores = seasons.grass_scores(seasons.monthly_weather(daily))
    assert scores.set_index("month").loc[6, "years"] == 1 and scores.set_index("month").loc[4, "years"] == 1
    assert np.isclose(scores["score"].dropna(), 1).all()


def test_fetch_weather_rejects_bad_places():
    with pytest.raises(ValueError):
        seasons.fetch_daily_weather(95, 0, "2020-01-01", "2020-12-31")


class FakeResponse:
    def __init__(self, data=None, content=b""):
        self.data, self.content = data, content

    def json(self):
        return self.data

    def raise_for_status(self):
        pass


def test_fetch_weather_waits_for_the_rate_limit_then_caches(monkeypatch, tmp_path):
    answers = [{"error": True, "reason": "Minutely API request limit exceeded."},
               {"daily": {"time": ["2020-01-01"], "temperature_2m_mean": [5.0], "precipitation_sum": [1.0],
                          "et0_fao_evapotranspiration": [0.5]}}]
    waits: list[float] = []
    monkeypatch.setattr(seasons.requests, "get", lambda url, params, timeout: FakeResponse(answers.pop(0)))
    monkeypatch.setattr(seasons.time, "sleep", waits.append)
    daily = seasons.fetch_daily_weather(41.26, -95.94, "2020-01-01", "2020-01-01", folder=tmp_path)
    assert len(daily) == 1 and waits == [61]
    again = seasons.fetch_daily_weather(41.26, -95.94, "2020-01-01", "2020-01-01", folder=tmp_path)   # from the CSV
    assert again["temperature_2m_mean"].iloc[0] == 5.0
    monkeypatch.setattr(seasons.requests, "get",
                        lambda url, params, timeout: FakeResponse({"error": True, "reason": "bad date"}))
    with pytest.raises(RuntimeError, match="bad date"):
        seasons.fetch_daily_weather(0, 0, "2020-01-01", "2020-01-01")


def test_ers_download_is_cached_and_read_from_the_zip(monkeypatch, tmp_path):
    import io
    import zipfile
    table = ("commodity_desc,attribute_desc,table_name,unit_desc,year_id,timeperiod_id,timeperiod_desc,amount\n"
             "Hogs,Commercial slaughter,Livestock and poultry slaughter,thousand head,2024,1,Jan-2024,10000\n")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("livestock-data-machine-readable-files/Meat-Statistics.csv", table)
    calls: list[str] = []

    def fake_get(url, timeout):
        calls.append(url)
        return FakeResponse(content=buffer.getvalue())

    monkeypatch.setattr(seasons.requests, "get", fake_get)
    path = seasons.download_ers_livestock(tmp_path)
    assert seasons.download_ers_livestock(tmp_path) == path and len(calls) == 1   # second call: the saved zip
    out = seasons.read_ers_slaughter(path)
    assert out.iloc[0].to_dict() == {"meat": "pork", "year": 2024, "month": 1, "thousand_head": 10000.0}
    monkeypatch.setattr(seasons.requests, "get", lambda url, timeout: FakeResponse(content=b"not a zip"))
    with pytest.raises(zipfile.BadZipFile):
        seasons.download_ers_livestock(tmp_path / "other")


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
