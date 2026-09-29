from copy import deepcopy
from pathlib import Path
from runpy import run_path

import pytest

compare = run_path(str(Path(__file__).resolve().parents[1] / "scripts/compare_replay.py"))[
    "compare"
]


def test_replay_comparison_only_allows_explicit_version_change():
    frozen = [
        {"id": "case", "report": {"library_version": "old", "checks": [{"status": "violated"}]}}
    ]
    replay = deepcopy(frozen)
    replay[0]["report"]["library_version"] = "new"
    compare(frozen, replay, "old", "new")
    assert replay[0]["report"]["library_version"] == "new"
    with pytest.raises(ValueError, match="version"):
        compare(frozen, replay, "old", "unexpected")
    replay[0]["report"]["checks"][0]["status"] = "satisfied"
    with pytest.raises(ValueError, match="beyond"):
        compare(frozen, replay, "old", "new")


def test_nested_report_version_is_the_only_permitted_mutation_difference():
    frozen = [{"result": {"report": {"library_version": "old"}}, "outcome": "survived"}]
    replay = deepcopy(frozen)
    replay[0]["result"]["report"]["library_version"] = "new"
    compare(frozen, replay, "old", "new", ("result", "report"))
    replay[0]["outcome"] = "detected"
    with pytest.raises(ValueError, match="beyond"):
        compare(frozen, replay, "old", "new", ("result", "report"))
