"""Tests for food freshness from photos (src/everflavor/freshness.py), notebook 05.

Tiny generated images stand in for the real datasets; training itself needs
torch and a GPU and is not run here. Run with `python -m pytest tests`, or alone:

    python tests/test_freshness.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor import freshness
from everflavor.freshness import (
    SAFETY_NOTE,
    freshness_coverage,
    group_near_duplicates,
    index_images,
    mendeley_download,
    sample_weights,
    selection_score,
    split_without_leakage,
)


def _image(path: Path, seed: int) -> None:
    from PIL import Image
    path.parent.mkdir(parents=True, exist_ok=True)
    pixels = np.random.default_rng(seed).integers(0, 255, (16, 16, 3), dtype=np.uint8)
    Image.fromarray(pixels).save(path)


def test_index_images_reads_state_item_and_age_from_names(tmp_path):
    for i, rel in enumerate(["Rotten/Apple/1.jpg", "Semi-Fresh/Banana/2.jpg", "Fresh/Banana/3.png",
                             "fish_eyes/tilapia_day3/4.jpg", "Fresh/Apple/aug_flip_5.jpg", "Misc/6.jpg",
                             "fish_eyes/carp_1-2days/7.jpg", "notes.txt"]):
        if rel.endswith(".txt"):
            (tmp_path / rel).write_text("not an image")
        else:
            _image(tmp_path / rel, i)
    index = index_images("test_source", tmp_path, "CC BY 4.0").set_index(
        index_images("test_source", tmp_path)["path"].map(lambda p: Path(p).relative_to(tmp_path).as_posix()))
    assert "Fresh/Apple/aug_flip_5.jpg" not in index.index                  # a source's own augmented copy
    assert "notes.txt" not in index.index
    assert tuple(index.loc["Rotten/Apple/1.jpg", ["group", "item", "state"]]) == ("produce", "apple", "spoiled")
    assert index.loc["Semi-Fresh/Banana/2.jpg", "state"] == "aging"          # not "fresh"
    assert index.loc["Fresh/Banana/3.png", "photo_set"] == "test_source:Fresh/Banana/3.png"   # one photo, one set
    series = index_images("test_source", tmp_path, series=True)                    # one fish photographed daily
    assert series.loc[series["path"].str.contains("tilapia"), "photo_set"].iloc[0] == "test_source:fish_eyes/tilapia_day3"
    assert tuple(index.loc["fish_eyes/tilapia_day3/4.jpg", ["item", "age_days_min", "age_days_max"]]) == ("tilapia", 3, 3)
    assert tuple(index.loc["fish_eyes/carp_1-2days/7.jpg", ["age_days_min", "age_days_max"]]) == (1, 2)
    assert index["state"].isna()["Misc/6.jpg"]                               # kept for a hand check
    assert index["license"].iloc[0] == "CC BY 4.0"


def test_source_rules_and_spellings_of_states(tmp_path):
    for i, rel in enumerate(["Semi_Fresh eggplant(4-8)/1.jpg", "Fresh pineapple(1-15)/2.jpg",
                             "Fish/Highly Fresh/3.jpg", "Fish/Fresh/4.jpg", "Fish/Not Fresh/5.jpg"]):
        _image(tmp_path / rel, i)
    plain = index_images("s", tmp_path).set_index(index_images("s", tmp_path)["path"].map(lambda p: Path(p).name))
    assert tuple(plain.loc["1.jpg", ["item", "state"]]) == ("eggplant", "aging")     # "semi fresh", not "fresh"
    assert tuple(plain.loc["2.jpg", ["item", "state"]]) == ("pineapple", "fresh")
    assert plain.loc["4.jpg", "state"] == "fresh" and plain.loc["5.jpg", "state"] == "spoiled"
    fish = index_images("s", tmp_path, state_rules={"fresh": "aging", "highly fresh": "fresh"})
    fish = fish.set_index(fish["path"].map(lambda p: Path(p).name))
    assert [fish.loc[f"{n}.jpg", "state"] for n in (3, 4, 5)] == ["fresh", "aging", "spoiled"]


def test_near_duplicates_and_the_split_keep_groups_together():
    index = pd.DataFrame({"photo_set": ["fish1", "fish1", "fish2", "fish3", "fish4"]})
    hashes = [np.zeros(64, bool), np.zeros(64, bool), np.ones(64, bool),
              np.r_[np.ones(62, bool), np.zeros(2, bool)], np.r_[np.zeros(32, bool), np.ones(32, bool)]]
    groups = group_near_duplicates(index, max_distance=4, hashes=hashes)
    assert groups.tolist() == [0, 0, 2, 2, 4]                               # fish3 is a near-copy of fish2
    index["duplicate_group"] = groups
    for seed in range(20):
        split = split_without_leakage(index, seed=seed)
        assert split.iloc[0] == split.iloc[1]                                # one fish, one split
        assert split.iloc[2] == split.iloc[3]                                # near-duplicates, one split
    many = pd.DataFrame({"photo_set": [f"set{i}" for i in range(3000)]})
    shares = split_without_leakage(many).value_counts(normalize=True)
    assert shares["train"] == pytest.approx(0.7, abs=0.03) and shares["test"] == pytest.approx(0.15, abs=0.03)
    assert split_without_leakage(many).equals(split_without_leakage(many))   # the same every run


def test_coverage_weights_and_scores():
    index = pd.DataFrame({"group": ["produce"] * 6, "item": ["apple"] * 6,
                          "state": ["fresh", "fresh", "fresh", "spoiled", "fresh", "spoiled"],
                          "source": ["big", "big", "big", "big", "small", "small"]})
    coverage = freshness_coverage(index, min_images=3).set_index(["state", "source"])
    assert coverage.loc[("fresh", "big"), "images"] == 3 and coverage.loc[("fresh", "big"), "item_state_images"] == 4
    assert coverage.loc[("spoiled", "small"), "warning"] == "fewer than 3 images"
    weights = sample_weights(index)
    assert weights.mean() == pytest.approx(1.0)
    per_source = weights.groupby(index["source"]).sum()
    assert per_source["big"] == pytest.approx(per_source["small"])           # every source counts equally
    big = index["source"] == "big"
    per_state = weights[big].groupby(index.loc[big, "state"]).sum()
    assert per_state["fresh"] == pytest.approx(per_state["spoiled"])         # and every state within it
    scores = selection_score(["spoiled", "spoiled", "fresh", "aging"], ["fresh", "spoiled", "fresh", "aging"])
    assert scores["spoiled_called_fresh"] == 0.5 and scores["accuracy"] == 0.75
    assert "throw it out" in SAFETY_NOTE


def _zip(files: dict) -> bytes:
    import io
    import zipfile
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def test_mendeley_download_checks_the_license_and_zip_paths(monkeypatch, tmp_path):
    import json
    record: dict = {"name": "Bananas", "doi": {"id": "10.17632/abc.1"},
              "data_licence": {"short_name": "CC BY 4.0", "url": "http://creativecommons.org/licenses/by/4.0"},
              "files": [{"filename": "Ripeness.zip", "content_details": {"download_url": "https://x/1"}},
                        {"filename": "Augmented Ripeness.zip", "content_details": {"download_url": "https://x/2"}},
                        {"filename": "Ripeness.rar", "content_details": {"download_url": "https://x/3"}}]}
    answers = {freshness.MENDELEY_API + "abc": json.dumps(record).encode(), "https://x/1": _zip({"Green/1.jpg": b"jpg"})}
    asked: list[str] = []

    def fake_download(url, target, timeout):
        asked.append(url)
        target.write_bytes(answers[url])
        return target

    monkeypatch.setattr(freshness, "_get_bytes", lambda url, timeout: answers[url])
    monkeypatch.setattr(freshness, "_download_to", fake_download)
    files = mendeley_download("abc", tmp_path / "bananas")
    assert [f.name for f in files] == ["Green", "LICENSE.txt"] and asked == ["https://x/1"]   # no augmented copies, no .rar
    assert "CC BY 4.0" in (tmp_path / "bananas" / "LICENSE.txt").read_text(encoding="utf-8")
    record["data_licence"]["short_name"] = "CC BY-NC 3.0"
    answers[freshness.MENDELEY_API + "abc"] = json.dumps(record).encode()
    with pytest.raises(PermissionError):
        mendeley_download("abc", tmp_path / "other")
    record["data_licence"]["short_name"] = "CC BY 4.0"
    answers[freshness.MENDELEY_API + "abc"] = json.dumps(record).encode()
    answers["https://x/1"] = _zip({"../escape.jpg": b"jpg"})
    with pytest.raises(ValueError):
        mendeley_download("abc", tmp_path / "third")
    assert not (tmp_path / "escape.jpg").exists()
    with pytest.raises(ValueError):
        mendeley_download("../etc", tmp_path / "fourth")
    loose = {"name": "Fish eyes", "version": 1, "data_licence": {"short_name": "CC BY 4.0"},
             "files": [{"filename": "IMG_1.jpg", "folder_id": "f1", "content_details": {"download_url": "https://x/4"}}]}
    answers[freshness.MENDELEY_API + "fish"] = json.dumps(loose).encode()
    answers[freshness.MENDELEY_API + "fish/folders/1"] = json.dumps([{"id": "f1", "name": "Chanos - Not Fresh"}]).encode()
    answers["https://x/4"] = b"jpg"
    mendeley_download("fish", tmp_path / "fish")
    assert (tmp_path / "fish" / "Chanos - Not Fresh" / "IMG_1.jpg").exists()   # the label stays in the folder name


def test_zenodo_download_checks_the_license_and_unpacks(monkeypatch, tmp_path):
    import json
    record: dict = {"metadata": {"title": "MeatScan", "license": {"id": "cc-by-4.0"}}, "doi": "10.5281/zenodo.1",
                    "files": [{"key": "photos.zip", "links": {"self": "https://z/1"}}]}
    answers = {freshness.ZENODO_API + "1": json.dumps(record).encode(),
               "https://z/1": _zip({"Fresh/1.jpg": b"jpg", "Spoiled/2.jpg": b"jpg"})}

    def fake_download(url, target, timeout):
        target.write_bytes(answers[url])
        return target

    monkeypatch.setattr(freshness, "_get_bytes", lambda url, timeout: answers[url])
    monkeypatch.setattr(freshness, "_download_to", fake_download)
    files = freshness.zenodo_download("1", tmp_path / "meat")
    assert [f.name for f in files] == ["Fresh", "LICENSE.txt", "Spoiled"]                  # the archive is removed
    record["metadata"]["license"]["id"] = "cc-by-nc-4.0"
    answers[freshness.ZENODO_API + "1"] = json.dumps(record).encode()
    with pytest.raises(PermissionError):
        freshness.zenodo_download("1", tmp_path / "other")
    with pytest.raises(ValueError):
        freshness.zenodo_download("1/../2", tmp_path / "third")


def test_unpack_rar_refuses_paths_outside_the_folder(monkeypatch, tmp_path):
    import subprocess

    class Done:
        stdout = "photos/1.jpg\n../../evil.jpg\n"

    ran: list[list[str]] = []
    monkeypatch.setattr(freshness, "_rar_tool", lambda: ["bsdtar"])
    def fake_run(cmd, **kw):
        ran.append(cmd)
        return Done()

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(ValueError):
        freshness._unpack_rar(tmp_path / "x.rar", tmp_path / "out")
    assert len(ran) == 1                                                                   # listed, never unpacked


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
