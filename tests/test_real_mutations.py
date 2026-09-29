from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from narrative_contracts.model import digest

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "real_mutations_test", ROOT / "benchmarks/real_mutations.py"
)
assert SPEC and SPEC.loader
campaign = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(campaign)


def test_operators_change_only_intended_input_and_leave_reference_untouched():
    manifest, records = campaign.natural.load_collection(ROOT / "benchmarks/remote-results")
    scenario = manifest["scenarios"][0]
    raw = campaign.natural.strict_json(records[0]["response"]["response"])
    before = digest((raw, scenario))
    wrong = campaign.mutate(raw, scenario, "claim_credits")
    assert wrong["options"][0]["claims"]["credits"] == raw["options"][0]["claims"]["credits"] + 1
    assert wrong["options"][0]["outcome"] == raw["options"][0]["outcome"]
    swapped = campaign.mutate(raw, scenario, "branch_claims")
    assert swapped["options"][0]["id"] == raw["options"][0]["id"]
    assert swapped["options"][0]["claims"] == raw["options"][1]["claims"]
    challenge = campaign.mutate(raw, scenario, "prose_wrong_credits")
    assert challenge["options"][0]["claims"] == raw["options"][0]["claims"]
    assert (
        str(scenario["options"][0]["after"]["credits"] + 100) in challenge["options"][0]["outcome"]
    )
    assert digest((raw, scenario)) == before


def test_campaign_freezes_inputs_separates_denominators_and_replays(tmp_path):
    prepared = tmp_path / "prepared"
    result = campaign.prepare(ROOT / "benchmarks/remote-results", prepared)
    assert result["prepared_cases"] == 384
    assert result["unavailable_baselines"] == []
    frozen = (prepared / "prepared.json").read_bytes()
    summary = campaign.run(prepared, tmp_path / "first")
    campaign.run(prepared, tmp_path / "second")
    assert (prepared / "prepared.json").read_bytes() == frozen
    for name in ("summary.json", "cases.json", "baselines.json", "contract-audit.json"):
        assert (tmp_path / "first" / name).read_bytes() == (tmp_path / "second" / name).read_bytes()
    assert summary["baselines_accepted"] == 32
    assert summary["scenario_groups"] == 8
    assert summary["by_lane"]["exact"]["total"] == 64
    assert summary["by_lane"]["heuristic"]["total"] == 96
    assert summary["by_lane"]["schema"]["total"] == 96
    assert summary["by_lane"]["control"]["total"] == 64
    assert summary["by_lane"]["challenge"]["total"] == 64
    assert "detection_rate" not in summary["by_lane"]["challenge"]
    assert "detection_score" not in summary
    rows = json.loads((tmp_path / "first/cases.json").read_text())
    for row in rows:
        if row["lane"] in ("exact", "heuristic") and row["outcome"] == "detected":
            assert any(
                c["status"] == "violated" and all(c[k] == v for k, v in row["target"].items())
                for c in row["result"]["report"]["checks"]
            )
    with pytest.raises(FileExistsError):
        campaign.prepare(ROOT / "benchmarks/remote-results", prepared)
    with pytest.raises(FileExistsError):
        campaign.run(prepared, tmp_path / "first")
    (prepared / "prepared.json").write_bytes(frozen + b" ")
    with pytest.raises(ValueError, match="hash mismatch"):
        campaign.run(prepared, tmp_path / "tampered")
