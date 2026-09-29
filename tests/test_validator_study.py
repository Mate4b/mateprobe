import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "validator_study", ROOT / "benchmarks/validator_study.py"
)
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)
PREPARED = ROOT / "benchmarks/validator-study/prepared"
CAPTURED = ROOT / "benchmarks/validator-study/evaluation"


def test_specification_rejects_bad_label_before_running_a_validator():
    row = study.make_corpus()[0]
    row["expected"] = ["unrelated_reason"]
    with pytest.raises(ValueError, match="Invalid relation/target"):
        study.verify_row(row)


def test_prepared_corruption_fails_closed(tmp_path):
    prepared = tmp_path / "prepared"
    shutil.copytree(PREPARED, prepared)
    corpus = prepared / "corpus.json"
    corpus.write_text(corpus.read_text() + " ")
    with pytest.raises(ValueError, match="Prepared content changed"):
        study.load_prepared(prepared)


def test_replay_matches_frozen_evidence_byte_for_byte(tmp_path):
    output = tmp_path / "replay"
    study.run(PREPARED, output, CAPTURED)
    for name in ("summary.json", "comparisons.json", "audit-reports.json", "observations.json"):
        assert (output / name).read_bytes() == (CAPTURED / name).read_bytes()


def test_capture_corruption_fails_closed(tmp_path):
    captured = tmp_path / "captured"
    shutil.copytree(CAPTURED, captured)
    (captured / "observations.json").write_text("{}")
    with pytest.raises(ValueError, match="Captured outcomes changed"):
        study.run(PREPARED, tmp_path / "out", captured)


def test_reexecution_matches_all_recorded_validator_observations():
    observations = json.loads((CAPTURED / "observations.json").read_text())
    for profile, records in observations.items():
        for row in study.load_prepared(PREPARED):
            for side in ("baseline", "variant"):
                assert study.capture(row["domain"], row[side], profile) == records[row["id"]][side]


def test_metrics_do_not_reward_wrong_reasons_or_crashes():
    profiles = json.loads((CAPTURED / "summary.json").read_text())["profiles"]
    assert profiles["wrong-diagnostic-ID"]["boolean_success_without_target"] == 96
    assert profiles["crash-on-fault"]["targeted_detections"] == 0
    assert profiles["reject-valid-variation"]["preservation_rate"] == 0.5
    assert profiles["reject-all"]["detection_score"] is None
    assert profiles["unknown-on-fault"]["ablations"]["invalid_hide_unknowns"]["score"] is None
    assert all(p["detailed_disagreements"] == 0 for p in profiles.values())
