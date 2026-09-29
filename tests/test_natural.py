from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from narrative_contracts import evaluate
from narrative_contracts.model import digest

SPEC = importlib.util.spec_from_file_location(
    "natural_benchmark", Path(__file__).parents[1] / "benchmarks/natural.py"
)
assert SPEC and SPEC.loader
natural = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(natural)


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
    request = {"prompt": natural.prompt(scenario), "model": "fixture"}
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
    scenario = natural.scenarios()[0]
    data = response(scenario)
    data["options"][0]["claims"] = data["options"][1]["claims"]
    row = natural.evaluate_record(record(scenario, data), scenario)
    assert row["status"] == "evaluated"
    assert row["invariant_accepted"] is False
    assert any(
        c["status"] == "violated" and c["scope"] == "outcome.0" for c in row["report"]["checks"]
    )


def test_prose_contradiction_without_claim_change_remains_a_documented_gap():
    scenario = natural.scenarios()[0]
    data = response(scenario)
    data["options"][0]["outcome"] = (
        "Your refund is already in the account and the parcel was replaced yesterday."
    )
    doc = natural.document(json.dumps(data), scenario)
    assert evaluate(doc, natural.context(scenario), natural.rules()[:1]).accepted


@pytest.mark.parametrize("change", ["missing_claim", "wrong_id", "boolean_credits", "extra_field"])
def test_invalid_envelopes_are_retained_as_structure_failures(change):
    scenario = natural.scenarios()[0]
    data = response(scenario)
    if change == "missing_claim":
        del data["options"][0]["claims"]["credits"]
    elif change == "wrong_id":
        data["options"][0]["id"] = "invented"
    elif change == "boolean_credits":
        data["options"][0]["claims"]["credits"] = True
    else:
        data["unexpected"] = "ignored?"
    assert (
        natural.evaluate_record(record(scenario, data), scenario)["status"] == "invalid_structure"
    )


def test_truncation_and_collection_error_are_not_success():
    scenario = natural.scenarios()[0]
    truncated = record(scenario)
    truncated["response"]["done_reason"] = "length"
    error = record(scenario)
    error["collection_status"] = "error"
    assert natural.evaluate_record(truncated, scenario)["status"] == "incomplete_generation"
    assert natural.evaluate_record(error, scenario)["status"] == "collection_error"


def test_replay_is_deterministic_and_missing_attempts_are_explicit(tmp_path):
    collection = tmp_path / "collection"
    collection.mkdir()
    dataset = natural.scenarios()[:2]
    manifest = {
        "scenarios": dataset,
        "scenario_digest": digest(dataset),
        "profile": natural.PROFILE,
        "models": {"fixture": {}},
        "rule_configuration": [r.configuration() for r in natural.rules()],
    }
    (collection / "manifest.json").write_text(json.dumps(manifest))
    (collection / "outputs.jsonl").write_text(json.dumps(record(dataset[0])) + "\n")
    natural.replay(collection, tmp_path / "first")
    natural.replay(collection, tmp_path / "second")
    for name in ("reports.json", "summary.json"):
        assert (tmp_path / "first" / name).read_bytes() == (tmp_path / "second" / name).read_bytes()
    summary = json.loads((tmp_path / "first" / "summary.json").read_text())
    assert summary["missing_attempts"] == [f"fixture/{dataset[1]['id']}"]
    with pytest.raises(FileExistsError):
        natural.replay(collection, tmp_path / "first")


def test_summaries_include_all_attempts_without_gold_metrics():
    scenario = natural.scenarios()[0]
    original = record(scenario)
    failed = copy.deepcopy(original)
    failed["collection_status"] = "error"
    rows = [natural.evaluate_record(original, scenario), natural.evaluate_record(failed, scenario)]
    summary = natural.summarize(rows, [original, failed])["fixture"]
    assert summary["attempts"] == 2 and summary["structured_outputs"] == 1
    assert summary["status_counts"]["collection_error"] == 1
    assert not {"accuracy", "precision", "recall"}.intersection(summary)


@pytest.mark.parametrize("unload_failure", [None, "still_loaded", "timeout"])
def test_collection_unloads_before_next_model(monkeypatch, tmp_path, unload_failure):
    loaded = set()
    generated = []
    unloads = []
    dataset = natural.scenarios()[:2]

    def http(base, route, payload=None, timeout=120):
        if route == "/api/tags":
            return {"models": [{"name": "first"}, {"name": "second"}]}
        if route == "/api/show":
            return {}
        if route == "/api/version":
            return {"version": "test"}
        if route == "/api/ps":
            return {"models": [{"name": name} for name in loaded]}
        assert route == "/api/generate"
        model = payload["model"]
        if payload.get("keep_alive") == 0:
            unloads.append(model)
            if unload_failure == "timeout":
                raise TimeoutError("Unload failed")
            if unload_failure != "still_loaded":
                loaded.discard(model)
            return {"done": True}
        assert not loaded - {model}, "Two different models would be resident"
        loaded.add(model)
        generated.append(model)
        return {"done": True, "response": "{}"}

    monkeypatch.setattr(natural, "_http", http)
    monkeypatch.setattr(natural, "scenarios", lambda: dataset)
    args = SimpleNamespace(
        output=tmp_path / "collection",
        models=["first", "second"],
        base_url="http://fixture",
        seed=1729,
        timeout=5,
    )
    if unload_failure:
        with pytest.raises((RuntimeError, TimeoutError)):
            natural.collect(args)
        assert generated == ["first", "first"]
        assert unloads == ["first"]
    else:
        natural.collect(args)
        assert generated == ["first", "first", "second", "second"]
        assert unloads == ["first", "second"]
        assert not loaded
    assert len((args.output / "outputs.jsonl").read_text().splitlines()) == len(generated)


def test_occupied_server_blocks_batch_without_unloading_other_work(monkeypatch):
    calls = []

    def http(base, route, payload=None, timeout=120):
        calls.append(route)
        return {"models": [{"name": "someone-elses-model"}]}

    monkeypatch.setattr(natural, "_http", http)
    with pytest.raises(RuntimeError), natural._single_model("http://fixture", "first", 5):
        pytest.fail("Must not begin generation on an occupied server")
    assert calls == ["/api/ps"]


def test_batch_exception_still_unloads_model(monkeypatch):
    unloaded = []

    def http(base, route, payload=None, timeout=120):
        if route == "/api/ps":
            return {"models": []}
        unloaded.append(payload)
        return {"done": True}

    monkeypatch.setattr(natural, "_http", http)
    with pytest.raises(ValueError, match="interrupted batch"):
        with natural._single_model("http://fixture", "first", 5):
            raise ValueError("interrupted batch")
    assert unloaded == [{"model": "first", "keep_alive": 0}]


@pytest.mark.parametrize(
    "change", ["extra_id", "model", "scenario", "group", "request_model", "prompt"]
)
def test_replay_rejects_records_outside_frozen_manifest(tmp_path, change):
    collection = tmp_path / "collection"
    collection.mkdir()
    scenario = natural.scenarios()[0]
    row = record(scenario)
    row["request"].update(system=natural.SYSTEM, options={"seed": 1729}, format="json")
    manifest = {
        "scenarios": [scenario],
        "scenario_digest": digest([scenario]),
        "profile": natural.PROFILE,
        "models": {"fixture": {}},
        "rule_configuration": [r.configuration() for r in natural.rules()],
        "system": natural.SYSTEM,
        "options": {"seed": 1729},
        "format": "json",
    }
    if change == "extra_id":
        row["id"] += "/invented"
    elif change == "model":
        row["model"] = "not-in-manifest"
    elif change == "scenario":
        row["scenario_id"] = "not-in-manifest"
    elif change == "group":
        row["group"] = "pretend-independent"
    elif change == "request_model":
        row["request"]["model"] = "other"
    else:
        row["request"]["prompt"] = "different instructions"
    row["request_digest"] = digest(row["request"])
    (collection / "manifest.json").write_text(json.dumps(manifest))
    (collection / "outputs.jsonl").write_text(json.dumps(row) + "\n")
    with pytest.raises(ValueError):
        natural.replay(collection, tmp_path / "invalid-replay")
    assert not (tmp_path / "invalid-replay").exists()
