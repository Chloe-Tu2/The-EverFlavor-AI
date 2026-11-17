"""Shared fetch helpers (scripts/fetch_tools.py) and the Commons credit rules: fake network, no real calls."""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path

import pandas as pd
import pytest
import requests

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "dish_photos"))
import fetch_dish_photos as fdp
import fetch_tools as ft

JPG = b"\xff\xd8\xff\xe0" + b"0" * 40


class Reply:
    def __init__(self, status: int = 200, content: bytes = b"", headers: dict | None = None, body: object = None):
        self.status_code, self.content, self.headers, self._body = status, content, headers or {}, body

    def json(self) -> object:
        if self._body is None:
            raise ValueError("not json")
        return self._body


class FakeSession:
    def __init__(self, *replies: Reply | Exception):
        self.replies, self.calls = list(replies), 0

    def get(self, url: str, params: dict | None = None, timeout: object = None) -> Reply:
        self.calls += 1
        item = self.replies.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    waits: list[float] = []
    monkeypatch.setattr(ft.time, "sleep", waits.append)
    return waits


def test_retry_after_seconds_date_and_default() -> None:
    assert ft.retry_after({"Retry-After": "7"}, 3) == 7
    assert ft.retry_after({}, 3) == 3
    assert ft.retry_after({"Retry-After": "soon"}, 3) == 3
    assert ft.retry_after({"Retry-After": "-5"}, 3) == 0
    later = format_datetime(datetime.now(timezone.utc) + timedelta(seconds=120), usegmt=True)
    assert 100 < ft.retry_after({"Retry-After": later}, 3) <= 120


def test_too_long_a_wait_stops_the_run() -> None:
    with pytest.raises(ft.FetchError):
        ft.polite_wait({"Retry-After": "99999"}, 5)


def test_busy_answer_waits_as_asked_then_succeeds(no_sleep: list[float]) -> None:
    s = FakeSession(Reply(429, headers={"Retry-After": "4"}), Reply(200, body={"ok": 1}))
    assert ft.get_json(s, "u", pace=0.5) == {"ok": 1}
    assert no_sleep == [4.0, 0.5]


def test_dropped_connection_and_bad_json_are_retried() -> None:
    s = FakeSession(requests.ConnectionError("x"), Reply(200), Reply(200, body={"a": 1}))
    assert ft.request(s, "u", parse=lambda r: r.json(), quiet=True) == {"a": 1}
    assert s.calls == 3


@pytest.mark.parametrize("status", [400, 401, 403, 404, 410])
def test_dead_answers_are_not_asked_twice(status: int) -> None:
    s = FakeSession(Reply(status), Reply(200))
    with pytest.raises(ft.FetchError) as e:
        ft.request(s, "u", quiet=True)
    assert e.value.status == status and s.calls == 1


def test_gives_up_after_the_tries() -> None:
    s = FakeSession(*[Reply(503)] * 3)
    with pytest.raises(ft.FetchError) as e:
        ft.request(s, "u", tries=3, quiet=True)
    assert e.value.status == 503 and s.calls == 3


@pytest.mark.parametrize("data,kind", [(JPG, "jpg"), (b"\x89PNG\r\n\x1a\n" + b"0" * 9, "png"),
                                       (b"RIFF0000WEBPVP8 ", "webp"), (b"GIF89a....", "gif"),
                                       (b"0000ftypavif", "avif"), (b"<html>busy</html>", None)])
def test_image_kind(data: bytes, kind: str | None) -> None:
    assert ft.image_kind(data) == kind


def test_download_image_outcomes(tmp_path: Path) -> None:
    path = tmp_path / "a" / "x.jpg"
    assert ft.download_image(FakeSession(Reply(200, JPG)), "u", path) == "got"
    assert path.read_bytes() == JPG
    other = tmp_path / "y.jpg"
    assert ft.download_image(FakeSession(Reply(200, b"<html>")), "u", other) == "not an image"
    assert ft.download_image(FakeSession(Reply(404)), "u", other) == "gone"
    assert ft.download_image(FakeSession(*[Reply(500)] * 2), "u", other, tries=2) == "failed"
    assert not other.exists() and not list(tmp_path.glob(".*part"))


def test_writes_are_whole_or_not_at_all(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "cache.json"
    ft.save_json({"a": 1}, path)
    assert ft.load_json(path) == {"a": 1}

    def broken(src: object, dst: object) -> None:
        raise OSError("stopped")
    monkeypatch.setattr(ft.os, "replace", broken)
    with pytest.raises(OSError):
        ft.save_json({"a": 2}, path)
    assert ft.load_json(path) == {"a": 1}   # the old cache survives


def test_load_json_default_and_jsonl_and_table(tmp_path: Path) -> None:
    assert ft.load_json(tmp_path / "none.json", {}) == {}
    (tmp_path / "bad.json").write_text("{cut", encoding="utf-8")
    assert ft.load_json(tmp_path / "bad.json", {"x": 1}) == {"x": 1}
    (tmp_path / "log.jsonl").write_text('{"a": 1}\n{"b"\n[1]\n{"c": 2}\n', encoding="utf-8")
    assert ft.read_jsonl(tmp_path / "log.jsonl") == [{"a": 1}, {"c": 2}]
    assert ft.read_jsonl(tmp_path / "missing.jsonl") == []
    table = pd.DataFrame({"a": [1, 2]})
    for name in ("t.csv", "t.parquet"):
        ft.save_table(table, tmp_path / name)
    assert pd.read_csv(tmp_path / "t.csv").equals(table) and pd.read_parquet(tmp_path / "t.parquet").equals(table)


# ---- Commons credits
@pytest.mark.parametrize("artist,expected", [
    ("Jane Doe", "Jane Doe"),
    ("<a href='x'>Jane Doe</a>", "Jane Doe"),
    ("No machine-readable author provided. Bob assumed (based on copyright claims).",
     "Bob (assumed by Wikimedia Commons)"),
    ("", ""),
])
def test_author_name_simple(artist: str, expected: str) -> None:
    assert fdp.author_name(artist) == expected


def test_author_name_drops_email_and_user_box() -> None:
    box = ("Ann Smith<br>I appreciate being notified if you use this photo, write to ann@example.com. "
           "This work is released under licence terms that go on and on and on for a long time indeed.")
    name = fdp.author_name(box)
    assert name == "Ann Smith" and "@" not in name
    assert "@" not in fdp.author_name("x" * 130 + " mail me at a.b@example.org")


def test_recredit_rewrites_only_commons_rows_with_a_cached_field() -> None:
    table = pd.DataFrame({
        "image_file": ["d/Q1.jpg", "d/Q2.jpg", "d/o3.jpg"], "dish_label": ["Soup", "Stew", "Pie"],
        "license": ["CC BY 4.0"] * 3, "author": ["old", "old", "old"],
        "credit": ["Photo of Soup: old, CC BY 4.0, via Wikimedia Commons",
                   "Photo of Stew: old, CC BY 4.0, via Wikimedia Commons",
                   "Photo of Pie: old, CC BY 4.0, via Openverse"]})
    out = fdp.recredit(table, {"Q1": "<b>New Name</b>", "o3": "Z"})
    assert out.author.tolist() == ["New Name", "old", "old"]
    assert out.credit[0] == "Photo of Soup: New Name, CC BY 4.0, via Wikimedia Commons"
    assert out.credit[1:].tolist() == table.credit[1:].tolist()
