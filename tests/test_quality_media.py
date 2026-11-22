"""The media audit and the quality reports follow their own rules: every dish resolves to an image or the
placeholder, a verified photo has a free licence and a credit, only Commons files are used, scores stay in range."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KNOW = ROOT / "data" / "knowledge"
POINTS = {"recipe": 100, "dish": 90, "variant": 80, "family": 60, "placeholder": 0}


def read(path: str) -> dict:
    return json.loads((KNOW / path).read_text(encoding="utf-8"))


MEDIA = read("media/dish_media_audit.json")["dishes"]


def test_every_dish_resolves_to_an_image_or_the_placeholder() -> None:
    assert MEDIA
    for r in MEDIA:
        assert r["best_level"] in POINTS and r["coverage_score"] == POINTS[r["best_level"]]
        assert r["image_status"] in {"verified", "fallback", "candidate", "missing", "review"}


def test_photos_are_free_credited_commons_files() -> None:
    for r in MEDIA:
        for photo in [r["primary_image"], *r["fallbacks"].values()]:
            if photo:
                assert photo["file_page"].startswith("https://commons.wikimedia.org/wiki/File:")
                assert photo["valid"] == (not photo["problems"])
        if r["image_status"] == "verified":
            assert r["license_valid"] and r["best_level"] in {"recipe", "dish"}
        if r["image_status"] == "fallback":
            assert r["fallback_available"] and r["best_level"] in {"variant", "family"}


def test_the_completeness_score_and_the_queue() -> None:
    q = read("quality/dish_quality.json")
    assert sum(q["weights"].values()) == 100
    for r in q["dishes"]:
        assert 0 <= r["without_image"] <= r["score"] <= 100
        assert r["tier"] == next(t for t, need in sorted(q["tiers"].items(), key=lambda kv: -kv[1]) if r["score"] >= need)
    queue = read("quality/publication_queue.json")["dishes"]
    assert all(not d["problems"] for d in queue if d["status"] == "ready")
    backlog_ready = {b["wikidata"] for b in read("coverage/expansion_backlog.json")["dishes"] if b["status"] == "ready"}
    assert {d["wikidata"] for d in queue if d["status"] == "ready"} <= backlog_ready
