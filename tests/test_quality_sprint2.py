"""The content quality sprint (2026-11-22): the approved image queue's rules, the completeness projection and the
taxonomy validation, and the committed files agreeing with each other."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "knowledge"))

import completeness_report
import image_queue

MEDIA = ROOT / "data" / "knowledge" / "media"
GOOD = {"license": "CC BY-SA 4.0", "author": "A. Cook", "mime": "image/jpeg", "width": 1200, "height": 800}


def test_only_free_credited_photos_of_a_fair_size_are_queued() -> None:
    assert image_queue.check("Pho.jpg", GOOD) == []
    assert image_queue.check("Pho.jpg", {**GOOD, "license": "All rights reserved"})[0].startswith("licence not free")
    assert "no author to credit" in image_queue.check("Pho.jpg", {**GOOD, "author": ""})
    assert image_queue.check("Pho.svg", {**GOOD, "mime": "image/svg+xml"})[0].startswith("not a photo")
    assert image_queue.check("Pho.jpg", {**GOOD, "width": 300})[0].startswith("smaller than")
    assert image_queue.check("Map of pho.jpg", GOOD) == ["named or described as a map, logo, drawing or label, not a photo"]
    assert image_queue.check("Gone.jpg", {"missing": True}) == ["the file is not on Commons"]


def test_the_committed_queue_keeps_its_own_rules() -> None:
    q = json.loads((MEDIA / "approved_image_queue.json").read_text(encoding="utf-8"))
    assert q["approved"] + q["rejected"] == q["asked"] == len(q["dishes"]) + len(q["rejected_dishes"])
    meta = json.loads((MEDIA / "commons_meta.json").read_text(encoding="utf-8"))
    for d in q["dishes"]:
        assert image_queue.check(d["commons_file"], meta[d["commons_file"]]) == []
        assert d["author"] in d["credit"] and d["license"] in d["credit"]
    assert all(d["reasons"] for d in q["rejected_dishes"])


def test_tiers_follow_the_scores() -> None:
    tiers = {"rich": 70, "fair": 40, "thin": 0}
    assert [completeness_report.tier(s, tiers) for s in (0, 39, 40, 69, 70, 100)] == [
        "thin", "thin", "fair", "fair", "rich", "rich"]


def test_the_taxonomy_validation_file_is_complete() -> None:
    v = json.loads((ROOT / "data" / "knowledge" / "quality" / "taxonomy_validation.json").read_text(encoding="utf-8"))
    assert sum(v["nodes"].values()) == 267 and v["nodes"]["country"] == 205   # after sprint 3 (coverage recovery), 2026-11-23
    assert {"zone_differences", "region_differences", "countries_missing_from_taxonomy"} <= set(v)
    assert all(b["country"] for b in v["below_country"])
