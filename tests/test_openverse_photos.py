"""Openverse photo source: the pure rules (no network)."""
from __future__ import annotations

import sys
from pathlib import Path

import imagehash
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "dish_photos"))
import fetch_openverse as ov


def result(**kw):
    base = {"title": "Homemade lasagna", "tags": [{"name": "pasta"}], "license": "by", "width": 800, "height": 600,
            "thumbnail": "https://api.openverse.org/v1/images/x/thumb/", "mature": False}
    return {**base, **kw}


@pytest.mark.parametrize("code,ok", [("cc0", True), ("pdm", True), ("by", True), ("by-sa", True), ("BY", True),
                                     ("by-nc", False), ("by-nd", False), ("by-nc-sa", False), (None, False)])
def test_is_free(code, ok):
    assert ov.is_free(code) is ok


def test_license_label():
    assert ov.license_label("by", "2.0") == "CC BY 2.0"
    assert ov.license_label("by-sa", "4.0") == "CC BY-SA 4.0"
    assert ov.license_label("cc0", "1.0") == "CC0 1.0"
    assert ov.license_label("pdm", "1.0") == "Public domain"
    assert ov.license_label("by", None) == "CC BY"


def test_credit_text():
    assert ov.credit_text("lasagna", "Ann", "CC BY 2.0", "flickr") == \
        "Photo of lasagna: Ann, CC BY 2.0, via flickr on Openverse"


def test_upgrade_rule():
    assert ov.upgrade_ok(0.06, 0.08, 800, 600, True)
    assert not ov.upgrade_ok(0.06, 0.079, 800, 600, True)   # not 0.02 higher
    assert not ov.upgrade_ok(0.06, 0.12, 800, 399, True)    # too small
    assert not ov.upgrade_ok(0.06, 0.12, 800, 600, False)   # fails the check
    assert not ov.upgrade_ok(None, 0.12, 800, 600, True)    # no score for the current photo
    assert not ov.upgrade_ok(0.06, 0.12, None, 600, True)   # size unknown


def test_near_duplicate():
    im = Image.effect_noise((64, 64), 80).convert("RGB")
    other = Image.effect_noise((64, 64), 80).convert("RGB")
    h = imagehash.phash(im)
    assert ov.near_duplicate(h, [imagehash.phash(im.resize((32, 32)))])
    assert not ov.near_duplicate(h, [imagehash.phash(other)])
    assert not ov.near_duplicate(h, [])


def test_keep_candidate():
    assert ov.keep_candidate(result(), "lasagna")
    assert ov.keep_candidate(result(title="Dinner", tags=[{"name": "lasagna"}]), "lasagna")  # words in tags
    assert not ov.keep_candidate(result(title="Dinner", tags=[]), "lasagna")
    assert not ov.keep_candidate(result(license="by-nc"), "lasagna")
    assert not ov.keep_candidate(result(title="Lasagna box"), "lasagna")
    assert not ov.keep_candidate(result(width=200, height=200), "lasagna")
    assert not ov.keep_candidate(result(mature=True), "lasagna")
