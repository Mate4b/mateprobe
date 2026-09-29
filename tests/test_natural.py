from __future__ import annotations

import copy
import json

import pytest

from benchmarks.natural import (
    PROFILE,
    context,
    document,
    evaluate_record,
    prompt,
    replay,
    rules,
    scenarios,
    summarize,
)
from narrative_contracts import evaluate
from narrative_contracts.model import digest


def response(scenario):
    return {
        "body": "A careful courier reviews the available alternatives before making a decision about the next stage of the journey.",
        "options": [
            {
                "id": o["id"],
                "label": o["action"],
                "outcome": "Your decision opens a specific next step while the remaining possibilities stay separate and the package continues to require attention.",
                "claims": o["after"].copy(),
            }
            for o in scenario["options"]
        ],
    }


def record(scenario, data=None):
    request = {"prompt": prompt(scenario)}
    return {
        "id": f"fixture/{scenario['id']}",
        "scenario_id": scenario["id"],
        "model": "fixture",
        "group": scenario["group"],
        "wall_seconds": 1,
        "request": request,
        "request_digest": digest(request),
        "collection_status": "returned",
        "response": {
            "done": True,
            "done_reason": "stop",
            "response": json.dumps(data if data is not None else response(scenario)),
        },
    }


def test_cross_branch_declarations_do_not_mask_error():
    scenario = scenarios()[0]
    data = response(scenario)
    data["options"][0]["claims"] = data["options"][1]["claims"]
    row = evaluate_record(record(scenario, data), scenario)
    assert row["status"] == "evaluated"
    assert row["invariant_accepted"] is False
    assert any(
        c["status"] == "violated" and c["scope"] == "outcome.0" for c in row["report"]["checks"]
    )


def test_prose_contradiction_without_claim_change_remains_a_documented_gap():
    scenario = scenarios()[0]
    data = response(scenario)
    data["options"][0]["outcome"] = (
        "Your refund is already in the account and the parcel was replaced yesterday."
    )
    doc = document(json.dumps(data), scenario)
    assert evaluate(doc, context(scenario), rules()[:1]).accepted


@pytest.mark.parametrize("change", ["missing_claim", "wrong_id", "boolean_credits", "extra_field"])
def test_invalid_envelopes_are_retained_as_structure_failures(change):
    scenario = scenarios()[0]
    data = response(scenario)
    if change == "missing_claim":
        del data["options"][0]["claims"]["credits"]
    elif change == "wrong_id":
        data["options"][0]["id"] = "invented"
    elif change == "boolean_credits":
        data["options"][0]["claims"]["credits"] = True
    else:
        data["unexpected"] = "ignored?"
    assert evaluate_record(record(scenario, data), scenario)["status"] == "invalid_structure"


def test_truncation_and_collection_error_are_not_success():
    scenario = scenarios()[0]
    truncated = record(scenario)
    truncated["response"]["done_reason"] = "length"
    error = record(scenario)
    error["collection_status"] = "error"
    assert evaluate_record(truncated, scenario)["status"] == "incomplete_generation"
    assert evaluate_record(error, scenario)["status"] == "collection_error"


def test_replay_is_deterministic_and_missing_attempts_are_explicit(tmp_path):
    collection = tmp_path / "collection"
    collection.mkdir()
    dataset = scenarios()[:2]
    manifest = {
        "scenarios": dataset,
        "scenario_digest": digest(dataset),
        "profile": PROFILE,
        "models": {"fixture": {}},
        "rule_configuration": [r.configuration() for r in rules()],
    }
    (collection / "manifest.json").write_text(json.dumps(manifest))
    (collection / "outputs.jsonl").write_text(json.dumps(record(dataset[0])) + "\n")
    replay(collection, tmp_path / "first")
    replay(collection, tmp_path / "second")
    for name in ("reports.json", "summary.json"):
        assert (tmp_path / "first" / name).read_bytes() == (tmp_path / "second" / name).read_bytes()
    summary = json.loads((tmp_path / "first" / "summary.json").read_text())
    assert summary["missing_attempts"] == [f"fixture/{dataset[1]['id']}"]
    with pytest.raises(FileExistsError):
        replay(collection, tmp_path / "first")


def test_summaries_include_all_attempts_without_gold_metrics():
    scenario = scenarios()[0]
    original = record(scenario)
    failed = copy.deepcopy(original)
    failed["collection_status"] = "error"
    rows = [evaluate_record(original, scenario), evaluate_record(failed, scenario)]
    summary = summarize(rows, [original, failed])["fixture"]
    assert summary["attempts"] == 2 and summary["structured_outputs"] == 1
    assert summary["status_counts"]["collection_error"] == 1
    assert not {"accuracy", "precision", "recall"}.intersection(summary)
