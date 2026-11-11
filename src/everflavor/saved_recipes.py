"""Saved recipes kept in the user's own browser (beta): what goes into local storage, and checking what comes back.

While EverFlavor is in beta, saved recipes stay only on the user's device (the browser's local storage, one
`everflavor` key). Nothing is sent to us. What the browser hands back is treated as untrusted: anyone can edit
their own storage, so `decode` keeps only well-formed entries, cuts long text and caps the count, and never
fails (bad data just means nothing is loaded). The same format is the "backup" file a user can download and load.
"""
from __future__ import annotations

import json
from datetime import date

VERSION = 1
MAX_RECIPES = 200
MAX_NAME = 200
MAX_LINE = 2000
MAX_LINES = 10
MAX_ID = 100
MAX_BYTES = 1_000_000


def encode(saved: dict[str, dict], today: str | None = None) -> str:
    """The saved recipes as the JSON kept in the browser (and in the backup file)."""
    today = today or date.today().isoformat()
    recipes = {rid: {"name": e["name"], "lines": list(e["lines"]), "saved_on": e.get("saved_on", today)}
               for rid, e in list(saved.items())[:MAX_RECIPES]}
    return json.dumps({"app": "everflavor", "version": VERSION, "recipes": recipes}, ensure_ascii=False)


def decode(text: str | bytes | None) -> dict[str, dict]:
    """The saved recipes read back from the browser or a backup file; anything malformed is left out."""
    if not text or len(text) > MAX_BYTES:
        return {}
    try:
        data = json.loads(text)
    except (ValueError, UnicodeDecodeError):
        return {}
    recipes = data.get("recipes") if isinstance(data, dict) and data.get("app") == "everflavor" else None
    if not isinstance(recipes, dict):
        return {}
    saved: dict[str, dict] = {}
    for rid, entry in recipes.items():
        if len(saved) >= MAX_RECIPES:
            break
        if not (isinstance(rid, str) and 0 < len(rid) <= MAX_ID and isinstance(entry, dict)):
            continue
        name, lines = entry.get("name"), entry.get("lines")
        if not (isinstance(name, str) and name.strip() and isinstance(lines, list) and lines):
            continue
        lines = [line[:MAX_LINE] for line in lines[:MAX_LINES] if isinstance(line, str)]
        if not lines:
            continue
        saved_on = entry.get("saved_on")
        saved[rid] = {"name": name[:MAX_NAME], "lines": lines,
                      **({"saved_on": saved_on[:10]} if isinstance(saved_on, str) else {})}
    return saved


def merge(current: dict[str, dict], loaded: dict[str, dict]) -> dict[str, dict]:
    """Recipes from the browser or a file added to the ones saved this visit (this visit's copy wins)."""
    merged = {**loaded, **current}
    return dict(list(merged.items())[:MAX_RECIPES])
