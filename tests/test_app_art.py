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
