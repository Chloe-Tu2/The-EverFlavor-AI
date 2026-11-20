"""The app's fresh-code reload (top of app/app.py) must be safe when several sessions start at once.

The live site crashed (Python 3.14, @dataclass in cooking_time.py: AttributeError on sys.modules.get(...)) when a
second session deleted the everflavor modules while the first was still importing them: the stamp that says
"these copies are fresh" was only set after all the imports. Now the check, the clean-up and the stamp happen
under one lock, before any `from everflavor... import`.
"""
import re
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "app" / "app.py").read_text(encoding="utf-8")


def test_the_stamp_is_set_under_the_lock_before_any_project_import():
    lock = SOURCE.index('with sys.__dict__.setdefault("_everflavor_import_lock", threading.Lock()):')
    purge = SOURCE.index("del sys.modules[_name]")
    stamp = SOURCE.index('vars(_everflavor_package)["_app_stamp"] = _SRC_STAMP')
    first_import = re.search(r"^from everflavor[. ]", SOURCE, re.MULTILINE)
    assert first_import is not None
    assert lock < purge < stamp < first_import.start()
    assert SOURCE.count("_app_stamp\"] = ") == 1   # set once, not again after the imports
    assert '.rglob("*.py")' in SOURCE              # files in subfolders (domain/) count too


def test_the_reload_block_survives_sessions_running_at_once():
    """Run the block itself in several threads, as Streamlit runs sessions: none may see a module disappear."""
    block = SOURCE[SOURCE.index("_SRC_STAMP = "):SOURCE.index("from chef_lines import")]
    sys.path.insert(0, str(ROOT / "src"))
    errors: list[BaseException] = []

    def run_block(stamp_shift: float) -> None:
        names = {"ROOT": ROOT, "sys": sys, "threading": threading}
        exec(block.replace("default=0.0)", f"default=0.0) + {stamp_shift}"), names)   # noqa: S102 - the app's own block

    def session() -> None:
        try:
            run_block(1.0)   # every session after one deploy sees the same new stamp
            import everflavor.cooking_time  # what crashed: a dataclass module imported right after
            import everflavor.dish_steps
            assert "everflavor.cooking_time" in sys.modules and everflavor.dish_steps.__name__
        except BaseException as e:   # noqa: BLE001 - any failure in a session is the bug
            errors.append(e)

    run_block(0.0)   # the old deploy's copies are loaded
    import everflavor.cooking_time  # noqa: F401
    threads = [threading.Thread(target=session) for _ in range(12)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors, errors[:3]
