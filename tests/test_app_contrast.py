"""Every kitchen's page colors are readable (WCAG 2.2 AA): text 4.5:1 on what it sits on, and the borders that
outline buttons and fields 3:1 (app/themes.py; the Classic kitchen's night colors too)."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUTTON_TEXT = "#2B1E1A"   # the dark text on every button and chosen tag (app/app.py, style())


def _themes():
    spec = importlib.util.spec_from_file_location("themes", ROOT / "app" / "themes.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return {**module.THEMES, "Classic at night": {**module.THEMES["Classic"], **module.NIGHT_COLORS}}


def _luminance(color: str) -> float:
    channels = [int(color.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    r, g, b = (c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    light, dark = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def test_contrast_formula_matches_known_values():
    assert contrast("#000000", "#FFFFFF") == pytest.approx(21.0)
    assert contrast("#777777", "#FFFFFF") == pytest.approx(4.48, abs=0.01)


@pytest.mark.parametrize("name", list(_themes()))
def test_every_theme_is_readable(name):
    t = _themes()[name]
    pairs = [("text", "panel", 4.5), ("text", "sidebar", 4.5), ("text", "bubble", 4.5),
             ("heading", "panel", 4.5),                       # headings, and the footer's links
             (BUTTON_TEXT, "button", 4.5), (BUTTON_TEXT, "button_hover", 4.5),
             ("border", "panel", 3.0)]                        # the outline of buttons, fields and cards
    low = [f"{fg} on {bg}: {contrast(t.get(fg, fg), t[bg]):.2f} < {need}"
           for fg, bg, need in pairs if contrast(t.get(fg, fg), t[bg]) < need]
    assert not low, f"{name}: " + "; ".join(low)
