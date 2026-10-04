"""Tests for the download helpers (src/everflavor/sources.py) with fake network answers.

No request leaves the computer and no test sleeps: requests.get and time.sleep
are replaced. The most important checks: a key passed to a helper never shows
up in an error, even when the connection itself fails. Run from the project
folder with `python -m pytest tests`, or this file alone (needs pytest):

    python tests/test_sources.py
"""
import io
import json
import sys
import zipfile
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor import sources

FAKE_KEY = "FAKE_KEY_DO_NOT_PRINT_123"


class FakeResponse:
    """The parts of requests.Response the helpers use."""

    def __init__(self, status: int = 200, body: object = None, content: bytes = b"", headers: dict | None = None):
        self.status_code = status
        self.ok = status < 400
        self._body = body if body is not None else {}
        self.content = content
        self.headers = headers or {}

    def json(self):
        return self._body

    def raise_for_status(self):
        if not self.ok:
            raise requests.HTTPError(f"HTTP {self.status_code}", response=self)  # type: ignore[arg-type]


@pytest.fixture
def fake_net(monkeypatch):
    """Replace requests.get with a queue of answers; record every call; never sleep."""
    calls: list[dict] = []
    answers: list[object] = []

    def fake_get(url, params=None, **kwargs):
        calls.append({"url": url, "params": params, **kwargs})
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    monkeypatch.setattr(sources.requests, "get", fake_get)
    monkeypatch.setattr(sources.time, "sleep", lambda *_: None)
    return calls, answers


def _connection_error_with_key() -> requests.ConnectionError:
    # The real message names the full URL, query string and key included
    return requests.ConnectionError(f"Max retries exceeded with url: /search?api_key={FAKE_KEY}&query=x")


# ------------------------------------------------------------------ the key never shows up
def test_usda_search_hides_the_key_when_the_connection_fails(fake_net):
    _, answers = fake_net
    answers.append(_connection_error_with_key())
    with pytest.raises(RuntimeError) as info:
        sources.usda_search("rice", FAKE_KEY)
    assert FAKE_KEY not in str(info.value)
    assert info.value.__cause__ is None and info.value.__suppress_context__   # original error not shown


def test_usda_search_hides_the_key_on_an_error_status(fake_net):
    calls, answers = fake_net
    answers.append(FakeResponse(403))
    with pytest.raises(RuntimeError, match="HTTP 403") as info:
        sources.usda_search("rice", FAKE_KEY)
    assert FAKE_KEY not in str(info.value)
    assert calls[0]["params"]["api_key"] == FAKE_KEY and calls[0]["timeout"] == 15


def test_usda_search_returns_the_json(fake_net):
    _, answers = fake_net
    answers.append(FakeResponse(200, {"foods": [{"description": "Rice"}]}))
    assert sources.usda_search("rice", FAKE_KEY)["foods"][0]["description"] == "Rice"


def test_themealdb_hides_the_key_when_every_attempt_fails(fake_net):
    calls, answers = fake_net
    answers.extend(_connection_error_with_key() for _ in range(3))
    with pytest.raises(RuntimeError) as info:
        sources._get_json(f"https://themealdb.example/api/json/v1/{FAKE_KEY}/search.php")
    assert FAKE_KEY not in str(info.value) and len(calls) == 3


def test_themealdb_retries_busy_answers_then_succeeds(fake_net):
    calls, answers = fake_net
    answers.extend([FakeResponse(503), FakeResponse(200, {"meals": []})])
    assert sources._get_json("https://themealdb.example/search.php") == {"meals": []}
    assert len(calls) == 2


def test_themealdb_download_reports_failed_letters_without_the_key(fake_net, capsys):
    _, answers = fake_net
    meal = {"idMeal": "1", "strMeal": "Tagine", "strCountry": "Moroccan",
            "strIngredient1": " chicken ", "strMeasure1": "1 kg ", "strIngredient2": "", "strIngredient3": None}
    answers.append(FakeResponse(200, {"meals": [meal]}))                    # "a"
    answers.append(FakeResponse(200, {"meals": [meal]}))                    # "b": the same meal again
    answers.extend(_connection_error_with_key() for _ in range(3))          # "c" fails three times
    answers.extend(FakeResponse(200, {"meals": None}) for _ in range(33))   # "d"-"z" and "0"-"9"
    df = sources.download_themealdb(f"https://themealdb.example/api/json/v1/{FAKE_KEY}/search.php")
    printed = capsys.readouterr().out
    assert "search for 'c' failed (RuntimeError)" in printed and FAKE_KEY not in printed
    assert len(df) == 1
    row = df.iloc[0]
    assert row["area"] == "Moroccan" and row["ingredients"] == ["chicken"] and row["measures"] == ["1 kg"]


# ------------------------------------------------------------------ Open Food Facts
def test_off_get_waits_as_long_as_the_server_asks(fake_net, monkeypatch):
    calls, answers = fake_net
    waits: list[float] = []
    monkeypatch.setattr(sources.time, "sleep", waits.append)
    monkeypatch.setattr(sources, "_off_wait_turn", lambda kind: None)
    answers.extend([FakeResponse(429, headers={"Retry-After": "7"}), FakeResponse(503),
                    FakeResponse(200, {"products": [{"code": "1"}]})])
    assert sources._off_get("https://off.example", kind="search") == {"products": [{"code": "1"}]}
    assert waits == [7.0, 20.0] and len(calls) == 3                    # Retry-After, then 10 s doubled
    assert calls[0]["headers"] == sources.OFF_HEADERS


def test_off_get_gives_a_short_error_for_lasting_failures(fake_net, monkeypatch):
    _, answers = fake_net
    monkeypatch.setattr(sources, "_off_wait_turn", lambda kind: None)
    answers.append(FakeResponse(400))
    with pytest.raises(requests.HTTPError, match="Open Food Facts answered HTTP 400"):
        sources._off_get("https://off.example")


def test_barcodes_are_checked_before_any_request(fake_net, monkeypatch):
    calls, answers = fake_net
    monkeypatch.setattr(sources, "_off_wait_turn", lambda kind: None)
    for bad in ["../search", "12345", "123456789012345", "12345678a", ""]:
        with pytest.raises(ValueError):
            sources.off_get_by_barcode(bad)
    assert calls == []
    answers.extend([FakeResponse(404), FakeResponse(200, {"status": 0}),
                    FakeResponse(200, {"status": 1, "product": {"product_name": "Tofu"}})])
    assert sources.off_get_by_barcode("01234567") is None                 # unknown barcode
    assert sources.off_get_by_barcode(" 0123456789012 ") is None          # found nothing
    assert sources.off_get_by_barcode("0123456789012") == {"product_name": "Tofu"}
    assert calls[-1]["url"].endswith("/api/v2/product/0123456789012.json")


def test_off_rate_limit_spaces_out_requests(monkeypatch):
    clock = [100.0]
    waits: list[float] = []
    monkeypatch.setattr(sources.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(sources.time, "sleep", waits.append)
    monkeypatch.setitem(sources._off_last_request, "search", 98.0)
    sources._off_wait_turn("search")
    assert waits == [pytest.approx(sources.OFF_MIN_INTERVAL["search"] - 2.0)]


# ------------------------------------------------------------------ files and USDA bulk downloads
def test_download_file_never_leaves_a_partial_file(fake_net, tmp_path):
    _, answers = fake_net
    answers.append(FakeResponse(200, content=b"abc"))
    target = sources.download_file("https://example.com/data.zip", tmp_path / "sub" / "data.zip")
    assert target.read_bytes() == b"abc"
    assert sorted(p.name for p in target.parent.iterdir()) == ["data.zip"]
    answers.append(FakeResponse(500))
    with pytest.raises(requests.HTTPError):
        sources.download_file("https://example.com/other.zip", tmp_path / "other.zip")
    assert not (tmp_path / "other.zip").exists() and not (tmp_path / "other.part").exists()


def _usda_zip(folder: Path, name: str) -> Path:
    url, key = sources.USDA_DOWNLOADS[name]
    foods = [
        {"fdcId": 1, "description": "Rice, cooked", "foodNutrients": [
            {"nutrient": {"name": "Energy", "unitName": "kJ"}, "amount": 544},
            {"nutrient": {"name": "Energy", "unitName": "kcal"}, "amount": 130},
            {"nutrient": {"name": "Protein"}, "amount": 2.7},
            {"nutrient": {"name": "Fatty acids, total saturated"}, "amount": 0.1}],
         "foodPortions": [{"portionDescription": "1 cup", "gramWeight": 158},
                          {"portionDescription": "Quantity not specified", "gramWeight": 150}]},
        {"fdcId": 2, "description": "Only kJ", "foodNutrients": [
            {"nutrient": {"name": "Energy", "unitName": "kJ"}, "amount": 100}]},
    ]
    target = folder / url.rsplit("/", 1)[-1]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("foods.json", json.dumps({key: foods}))
    target.write_bytes(buffer.getvalue())
    return target


def test_usda_table_reads_kcal_portions_and_extra_nutrients(fake_net, tmp_path):
    calls, _ = fake_net
    _usda_zip(tmp_path, "fndds")
    table = sources.usda_table("fndds", tmp_path, nutrients={"Fatty acids, total saturated": "sat_fat_100g"})
    assert calls == []                                           # the zip was already there
    assert table["description"].tolist() == ["Rice, cooked"]     # no kcal value: dropped
    row = table.iloc[0]
    assert row["kcal_100g"] == 130 and row["protein_100g"] == 2.7
    assert row["sat_fat_100g"] == 0.1 and row["serving_g"] == 150
    with pytest.raises(ValueError, match="Unknown USDA download"):
        sources.download_usda("branded", tmp_path)


def test_download_and_unzip(fake_net, tmp_path):
    _, answers = fake_net
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("inner/recipes.csv", "a,b\n1,2\n")
    answers.append(FakeResponse(200, content=buffer.getvalue()))
    sources.download_and_unzip("https://example.com/r.zip", tmp_path)
    assert sources.find_file(tmp_path, "recipes.csv") == tmp_path / "inner" / "recipes.csv"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
