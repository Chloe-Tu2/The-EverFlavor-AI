"""One version everywhere: the package, the top of CHANGELOG.md and the app's What's new notes (app/updates.py)."""
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from everflavor import __version__

SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def _updates() -> list:
    spec = importlib.util.spec_from_file_location("updates", ROOT / "app" / "updates.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.UPDATES


def test_version_is_semantic_and_the_same_everywhere():
    assert SEMVER.match(__version__), __version__
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    top = re.search(r"^## \[(\d+\.\d+\.\d+)\] - (\d{4}-\d{2}-\d{2})$", changelog, re.MULTILINE)
    assert top and top.group(1) == __version__, "the newest CHANGELOG.md entry must be the package version"
    assert f"[{__version__}]: https://github.com/" in changelog, "the version needs its link at the bottom"
    updates = _updates()
    assert updates[0]["version"] == __version__ and updates[0]["date"] == top.group(2)


def test_update_notes_are_short_and_newest_first():
    updates = _updates()
    versions = [tuple(int(n) for n in u["version"].split(".")) for u in updates]
    assert versions == sorted(versions, reverse=True) and len(set(versions)) == len(versions)
    for update in updates:
        assert 1 <= len(update["notes"]) <= 3
        assert all(note.startswith(("New: ", "Changed: ", "Fixed: ")) for note in update["notes"])
