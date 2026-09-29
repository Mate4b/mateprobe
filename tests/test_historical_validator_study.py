import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def study(study_runtime):
    return study_runtime["load_runner"]("historical_validator_study")


CAPTURED = ROOT / "benchmarks/historical-validator-results/captured"


def test_prepared_records_include_valid_trigger_variations(study, study_runtime):
    data = study.load_prepared()
    assert len(data["candidates"]) == 10
    pairs = data["authored_inputs"]
    for id in ("marshmallow-file-url", "marshmallow-idn-email", "jsonschema-bool-ref-cache"):
        assert pairs[id][0]["relation"] == "preserve"
        assert pairs[id][0]["expected"] == []
    assert pairs["jsonschema-enum-bool-int"][0]["relation"] == "violation"
    assert all(
        json.dumps(p["baseline"], sort_keys=True) != json.dumps(p["variant"], sort_keys=True)
        for rows in pairs.values()
        for p in rows
    )


def test_historical_offline_replay_matches_frozen_evidence(tmp_path, study, study_runtime):
    study.replay(CAPTURED, tmp_path / "out")
    study_runtime["compare_outputs"]("historical", study.OUT / "evaluation", tmp_path / "out")


def test_historical_capture_tampering_is_rejected(tmp_path, study, study_runtime):
    captured = tmp_path / "captured"
    shutil.copytree(CAPTURED, captured)
    (captured / "captured.json").write_text("{}")
    with pytest.raises(ValueError, match="Capture changed"):
        study.replay(captured, tmp_path / "out")


def test_historical_versions_and_paired_controls_are_retained(study, study_runtime):
    summary = json.loads((study.OUT / "evaluation/summary.json").read_text())
    assert summary["included"] == 4
    assert summary["excluded"] == 6
    assert len(summary["results"]) == summary["included"]
    for item in summary["results"]:
        assert set(item["outcomes"]) == {item["before_version"], item["after_version"]}


def test_compatibility_followup_replays_and_keeps_nonreproduction(tmp_path, study, study_runtime):
    spec = importlib.util.spec_from_file_location(
        "historical_followup_test", ROOT / "benchmarks/historical_followup.py"
    )
    followup = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(followup)
    followup.verify()
    summary = followup.base.replay(followup.OUT / "captured", tmp_path / "out")
    assert summary["fixes_reproduced"] == 3
    assert (
        next(r for r in summary["results"] if r["id"] == "marshmallow-idn-email")["fix_reproduced"]
        is False
    )
    study_runtime["compare_outputs"]("followup", followup.OUT / "evaluation", tmp_path / "out")
