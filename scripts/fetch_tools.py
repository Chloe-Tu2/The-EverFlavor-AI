"""Shared helpers for the data fetchers in scripts/ (API clients): polite retries and safe writes.

Every fetcher follows the same rules, so they live here once:

- **Wait as long as the server asks.** `retry_after` reads a Retry-After header as seconds or as a date. When the
  wait is longer than `MAX_WAIT` the fetcher stops with a clear message instead of asking too early.
- **Do not ask again when it cannot help.** 400, 401, 403, 404 and 410 end the attempts at once.
- **A stopped run never leaves a broken file.** Files are written under a temporary name first, then renamed
  (`write_bytes`, `save_json`, `save_table`), so a cache or a table is either the old one or the new one.
- **A photo is a photo.** `image_kind` reads the first bytes, so an error page is never saved as a picture.

Used by scripts/dish_photos/, scripts/recipe_photos/fetch.py and scripts/knowledge/fetch_knowledge.py; the tests
(tests/test_fetch_tools.py) run it with fake network answers.
"""
from __future__ import annotations

import email.utils
import json
import math
import os
import time
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

GIVE_UP = (400, 401, 403, 404, 410)   # asking again cannot change these answers
MAX_WAIT = 900.0                      # seconds; a longer Retry-After stops the run (rerun later)


class FetchError(RuntimeError):
    """A request that did not succeed. `status` is the last HTTP status (None: no answer at all)."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


def retry_after(headers: Mapping[str, str] | None, default: float) -> float:
    """Seconds the server asks us to wait: its Retry-After header (seconds or an HTTP date), else `default`."""
    value = (headers or {}).get("Retry-After")
    if value is None or not str(value).strip():
        return default
    text = str(value).strip()
    try:
        seconds = float(text)
    except ValueError:
        try:
            when = email.utils.parsedate_to_datetime(text)
        except (TypeError, ValueError):
            return default
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        seconds = (when - datetime.now(timezone.utc)).total_seconds()
    if math.isnan(seconds):
        return default
    return max(0.0, seconds)


def polite_wait(headers: Mapping[str, str] | None, default: float) -> float:
    """`retry_after`, but a wait longer than MAX_WAIT raises: better to stop than to ask before the server allows."""
    seconds = retry_after(headers, default)
    if seconds > MAX_WAIT:
        raise FetchError(f"the server asks to wait {seconds:.0f} s; rerun later (what was fetched is saved)", 429)
    return seconds


def request(session: Any, url: str, *, params: dict | None = None, parse: Callable[[Any], Any] | None = None,
            timeout: float | tuple[float, float] = 60, tries: int = 5, wait: float = 10.0, quiet: bool = False) -> Any:
    """GET `url` and return `parse(response)` (the response itself without `parse`).

    A busy answer (429, 5xx) or a dropped connection is tried again, after the server's Retry-After or
    `wait` x the attempt number. An answer in GIVE_UP, or no good answer after `tries`, raises FetchError.
    `parse` may raise ValueError (a 200 answer that is not what was asked for): that is tried again too.
    """
    status: int | None = None
    for attempt in range(1, tries + 1):
        pause = wait * attempt
        try:
            response = session.get(url, params=params, timeout=timeout)
            status = response.status_code
            if status == 200:
                return parse(response) if parse else response
            if status in GIVE_UP:
                raise FetchError(f"http {status}: {url}", status)
            if not quiet:
                print("  http", status, "retry", attempt, flush=True)
            pause = polite_wait(response.headers, pause)
        except (requests.RequestException, ValueError) as e:
            if not quiet:
                print("  error", type(e).__name__, "retry", attempt, flush=True)
        if attempt < tries:
            time.sleep(pause)
    raise FetchError(f"failed after {tries} tries: {url}", status)


def get_json(session: Any, url: str, params: dict | None = None, pace: float = 1.0, tries: int = 5,
             wait: float = 10.0) -> dict:
    """One JSON API call, then `pace` seconds of rest (the APIs' fair-use rate)."""
    data = request(session, url, params=params, parse=lambda r: r.json(), tries=tries, wait=wait)
    time.sleep(pace)
    return data


def image_kind(data: bytes) -> str | None:
    """File type of a picture from its first bytes (jpg, png, webp, gif, avif), None when it is not one."""
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if data[4:12] in (b"ftypavif", b"ftypheic", b"ftypmif1"):
        return "avif"
    return None


def download_image(session: Any, url: str, path: Path, *, pace: float = 1.0, tries: int = 5,
                   wait: float = 15.0) -> str:
    """Save the picture at `url` as `path`: "got", "gone" (the link is dead), "not an image" or "failed"."""
    try:
        data = request(session, url, parse=lambda r: r.content, tries=tries, wait=wait, quiet=True)
    except FetchError as e:
        return "gone" if e.status in GIVE_UP else "failed"
    time.sleep(pace)
    if image_kind(data) is None:
        return "not an image"
    write_bytes(path, data)
    return "got"


def _temporary(path: Path) -> Path:
    # A leading dot: patterns like "<id>.*" that look for finished files never match a half-written one
    return path.with_name(f".{path.name}.part")


def write_bytes(path: Path, data: bytes) -> None:
    """Write a file whole or not at all (temporary name first, then renamed)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = _temporary(path)
    tmp.write_bytes(data)
    os.replace(tmp, path)


def write_text(path: Path, text: str) -> None:
    write_bytes(path, text.encode("utf-8"))


def save_json(obj: object, path: Path) -> None:
    """Save a cache as JSON, whole or not at all: a run stopped while saving keeps the earlier answers."""
    write_text(path, json.dumps(obj, ensure_ascii=False))


def load_json(path: Path, default: Any = None) -> Any:
    """Read a JSON cache. With a `default`, a missing or unreadable file gives the default (asked again)."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        if default is None:
            raise
        return default


def save_table(table: Any, path: Path) -> None:
    """Save a pandas table (.parquet or .csv by the file name), whole or not at all."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = _temporary(path)
    if path.suffix == ".parquet":
        table.to_parquet(tmp, index=False)
    else:
        table.to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, path)


def read_jsonl(path: Path) -> list[dict]:
    """The records of a .jsonl log. A line cut short by a stopped run is skipped, not fatal."""
    records: list[dict] = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records
