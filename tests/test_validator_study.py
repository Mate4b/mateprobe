import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def study(study_runtime):
    return study_runtime["load_runner"]("validator_study")


PREPARED = ROOT / "benchmarks/validator-study/prepared"
CAPTURED = ROOT / "benchmarks/validator-study/evaluation"


def test_specification_rejects_bad_label_before_running_a_validator(study, study_runtime):
    row = study.make_corpus()[0]
    row["expected"] = ["unrelated_reason"]
    with pytest.raises(ValueError, match="Invalid relation/target"):
        study.verify_row(row)


def test_prepared_corruption_fails_closed(tmp_path, study, study_runtime):
    prepared = tmp_path / "prepared"
    shutil.copytree(PREPARED, prepared)
    corpus = prepared / "corpus.json"
    corpus.write_text(corpus.read_text() + " ")
    with pytest.raises(ValueError, match="Prepared content changed"):
        study.load_prepared(prepared)


def test_replay_matches_frozen_evidence_with_explicit_version_transition(
    tmp_path, study, study_runtime
):
    output = tmp_path / "replay"
    study.run(PREPARED, output, CAPTURED)
    study_runtime["compare_outputs"]("controlled", CAPTURED, output)


def test_capture_corruption_fails_closed(tmp_path, study, study_runtime):
    captured = tmp_path / "captured"
    shutil.copytree(CAPTURED, captured)
    (captured / "observations.json").write_text("{}")
    with pytest.raises(ValueError, match="Captured outcomes changed"):
        study.run(PREPARED, tmp_path / "out", captured)


def test_reexecution_matches_all_recorded_validator_observations(study, study_runtime):
    observations = json.loads((CAPTURED / "observations.json").read_text())
    for profile, records in observations.items():
        for row in study.load_prepared(PREPARED):
            for side in ("baseline", "variant"):
                assert study.capture(row["domain"], row[side], profile) == records[row["id"]][side]


def test_metrics_do_not_reward_wrong_reasons_or_crashes(study, study_runtime):
    profiles = json.loads((CAPTURED / "summary.json").read_text())["profiles"]
    assert profiles["wrong-diagnostic-ID"]["boolean_success_without_target"] == 96
    assert profiles["crash-on-fault"]["targeted_detections"] == 0
    assert profiles["reject-valid-variation"]["preservation_rate"] == 0.5
    assert profiles["reject-all"]["detection_score"] is None
    assert profiles["unknown-on-fault"]["ablations"]["invalid_hide_unknowns"]["score"] is None
    assert all(p["detailed_disagreements"] == 0 for p in profiles.values())


@pytest.mark.parametrize("change", ["outcome", "evidence", "version", "membership"])
def test_compatibility_check_rejects_changed_results(tmp_path, study, study_runtime, change):
    output = tmp_path / "replay"
    study.run(PREPARED, output, CAPTURED)
    path = output / "audit-reports.json"
    reports = json.loads(path.read_text())
    key = next(iter(reports))
    if change == "outcome":
        reports[key]["cases"][0]["outcome"] = "detected"
    elif change == "evidence":
        reports[key]["cases"][0]["variant"]["evidence"] = [{"library_version": "hidden-change"}]
    elif change == "version":
        reports[key]["library_version"] = "unverified-version"
    else:
        del reports[key]
    path.write_text(json.dumps(reports))
    with pytest.raises(
        ValueError, match="Replay report membership|Unexpected replay|differs beyond"
    ):
        study_runtime["compare_outputs"]("controlled", CAPTURED, output)
