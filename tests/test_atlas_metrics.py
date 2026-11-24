"""Atlas metrics, region pages and the README dashboard (scripts/knowledge/enrichment_impact.py, region_pages.py)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "knowledge"))
import country_scores as cs
import enrichment_impact as ei
import region_pages as rp

PAGE = {"id": "west_africa", "name": "West Africa", "continent": "Africa", "countries": ["Ghana"],
        "coverage_score": 40.0, "representative_dishes": ["Jollof rice"], "dish_families": ["stew"],
        "sources": [{"name": "Wikipedia"}], "human_reviewed": False,
        "indigenous_traditions": [{"tradition": "x", "reviewed": False}]}


def test_a_good_region_page_passes_and_bad_ones_are_named() -> None:
    assert rp.validate(PAGE, {"Ghana"}) == []
    assert "unknown country Ghana" in rp.validate(PAGE, set())
    assert "coverage out of range" in rp.validate({**PAGE, "coverage_score": 120}, {"Ghana"})
    assert "no sources" in rp.validate({**PAGE, "sources": []}, {"Ghana"})
    tagged = {**PAGE, "indigenous_traditions": [{"tradition": "x", "reviewed": True}]}
    assert "an Indigenous tag marked reviewed without a person" in rp.validate(tagged, {"Ghana"})


def test_change_reads_as_points_and_percent() -> None:
    assert ei.change(53, 90) == "+37 (+69.8%)"
    assert ei.change(0, 3) == "+3"


def test_the_dashboard_has_the_four_kpis_and_no_emoji() -> None:
    nums = {k: 1.0 for keys in ei.SECTIONS.values() for k in keys} | {k: 2.0 for k in ei.RECOVERY}
    block = "\n".join(ei.dashboard(nums, nums))
    for part in ("### Coverage", "### Representation", "### Enrichment", "### Recovery"):
        assert part in block
    assert not re.search("[\U0001F000-\U0001FAFF\u2600-\u27BF]", block)


def test_the_readme_dashboard_sits_between_its_markers() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert text.index(ei.START) < text.index("## Atlas progress") < text.index(ei.END)


def test_one_dish_is_covered_but_not_represented() -> None:
    one = [{"qid": "Q1"}]
    s = cs.scores(one, set(), {}, {}, has_regions=False)
    assert s["representation"] < cs.WEAK_BELOW and s["enrichment"] == 0.0
    rich = [{"qid": f"Q{i}", "story_candidates": ["x"], "origin": ["Ghana"], "region": "Ashanti"} for i in range(3)]
    walter = {f"Q{i}": {"lines": ["a", "b"], "variants": ["v"]} for i in range(3)}
    paths = {f"Q{i}": {"next": [{"qid": "Q9"}]} for i in range(3)}
    s = cs.scores(rich, {"Q0", "Q1", "Q2"}, walter, paths, has_regions=True)
    assert s["representation"] == 100.0 and s["enrichment"] == 100.0
    assert cs.scores([], set(), {}, {}, has_regions=True)["representation"] == 0.0


def test_indigenous_verdicts_survive_a_rerun(tmp_path, monkeypatch) -> None:
    import culinary_coverage as cc
    monkeypatch.setattr(cc, "SHEET", tmp_path / "indigenous_tags.csv")
    foods = [{"tradition": "Māori", "name": "Hāngī", "qid": "Q1", "country": "New Zealand"},
             {"tradition": "Inuit", "name": "Akutaq", "qid": "Q2", "country": "Canada"}]
    cc.review_sheet(foods)
    text = cc.SHEET.read_text(encoding="utf-8").replace("Q1,New Zealand,,,,,", "Q1,New Zealand,,,keep,A person,ok")
    cc.SHEET.write_text(text, encoding="utf-8")
    rows = cc.review_sheet(foods)
    assert cc.is_reviewed(rows[("Māori", "Q1")]) and not cc.is_reviewed(rows[("Inuit", "Q2")])
    assert not cc.is_reviewed({"verdict": "keep", "reviewer": ""})   # a verdict needs a person's name
