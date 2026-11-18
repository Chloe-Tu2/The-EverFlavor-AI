"""The pixel art the app names (app/app.py, art("...")) is all drawn: a missing file would leave an empty box."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "design" / "pixel-art" / "assets"


def test_every_named_picture_exists():
    names = set(re.findall(r'\bart\("([a-z0-9_]+)"\)', (ROOT / "app" / "app.py").read_text(encoding="utf-8")))
    assert "no_photo_skillet" in names
    missing = sorted(n for n in names if not (ASSETS / f"{n}.png").is_file())
    assert not missing, f"pictures named in app.py but not drawn: {missing}"


def test_the_kitchen_scene_is_served_as_a_cached_file():
    """The scene is fetched from app/static/scenes/ (cached by the browser), so the template is a module script
    with one place for the scene, and static serving is on; the copies are never committed."""
    template = (ROOT / "app" / "kitchen_scene.html").read_text(encoding="utf-8")
    assert '<script type="module">' in template and template.count("__SCENE__") == 1
    config = (ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    assert re.search(r"(?m)^enableStaticServing = true$", config)
    assert "app/static/scenes/" in (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert (ROOT / "app" / "static").is_dir()   # Streamlit warns when the served folder is missing
