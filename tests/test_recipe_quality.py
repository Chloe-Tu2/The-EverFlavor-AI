"""The recipe quality audit's counts (data/knowledge/recipe_quality.json) add up by source."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_the_quality_counts_add_up() -> None:
    q = json.loads((ROOT / "data" / "knowledge" / "recipe_quality.json").read_text(encoding="utf-8"))
    sizes = q["recipes"]
    sources = [s for s in sizes if s != "all"]
    assert sum(sizes[s] for s in sources) == sizes["all"]
    for check, counts in [*q["checks"].items(), ("complete", q["complete"])]:
        assert sum(counts[s] for s in sources) == counts["all"], check
        assert all(0 <= counts[s] <= sizes[s] for s in sources), check
    c = q["checks"]
    assert c["no photo at all (neither its own nor its dish's)"]["all"] <= c["no photo of its own"]["all"]
