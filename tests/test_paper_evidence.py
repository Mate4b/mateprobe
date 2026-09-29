import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_module(path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "benchmarks"))
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_external_replay_preserves_all_cases_and_upstream_labels(tmp_path, monkeypatch):
    module = load_module(ROOT / "benchmarks/external_conformance.py", monkeypatch)
    base = ROOT / "benchmarks/external-conformance"
    module.run(base / "prepared", tmp_path / "out", base / "evaluation")
    for name in ("summary.json", "comparisons.json", "audit-report.json", "observations.json"):
        assert (tmp_path / "out" / name).read_bytes() == (base / "evaluation" / name).read_bytes()
    pairs = json.loads((base / "prepared/pairs.json").read_text())
    assert all((row["relation"] == "preserve") == row["valid"] for row in pairs)


def test_external_corruption_is_rejected(tmp_path, monkeypatch):
    module = load_module(ROOT / "benchmarks/external_conformance.py", monkeypatch)
    base = ROOT / "benchmarks/external-conformance"
    shutil.copytree(base / "evaluation", tmp_path / "capture")
    (tmp_path / "capture/observations.json").write_text("{}")
    with pytest.raises(ValueError, match="Captured content changed"):
        module.run(base / "prepared", tmp_path / "out", tmp_path / "capture")


def test_pairing_preserves_json_types_and_records_unpairable_groups(monkeypatch):
    module = load_module(ROOT / "benchmarks/external_conformance.py", monkeypatch)
    sources = {k: [] for k in module.KEYWORDS}
    sources["uniqueItems"] = [
        {
            "description": "typed",
            "schema": {},
            "tests": [
                {"description": "baseline", "data": False, "valid": True},
                {"description": "distinct integer", "data": 0, "valid": True},
                {"description": "no-op", "data": False, "valid": True},
            ],
        },
        {
            "description": "no baseline",
            "schema": False,
            "tests": [{"description": "invalid", "data": 0, "valid": False}],
        },
        {
            "description": "remote",
            "schema": {"$ref": "https://example.invalid/schema"},
            "tests": [{"description": "skip", "data": 0, "valid": True}],
        },
    ]
    pairs, ledger = module.build_pairs(sources)
    assert len(pairs) == 1 and type(pairs[0]["variant"]["data"]) is int
    assert [r["status"] for r in ledger] == [
        "baseline",
        "paired",
        "identical_variant",
        "no_valid_baseline",
        "external_reference",
    ]


def test_manuscript_numbers_recompute_from_raw_and_reject_changed_summary(tmp_path, monkeypatch):
    module = load_module(ROOT / "scripts/build_paper_evidence.py", monkeypatch)
    facts = module.build(tmp_path / "evidence")
    assert facts["controlled.classifications"]["value"] == 1152
    assert facts["external.pairs"]["value"] == 124
    assert facts["historical.fixes_reproduced"]["value"] == 3
    assert facts["demo.disagreements"]["value"] == 0
    # A changed manuscript-facing summary must not be accepted just because raw captures verify.
    fake_control = tmp_path / "controlled"
    shutil.copytree(module.CONTROL, fake_control)
    summary = fake_control / "evaluation/summary.json"
    changed = json.loads(summary.read_text())
    changed["disagreements"] = 999
    summary.write_text(json.dumps(changed))
    monkeypatch.setattr(module, "CONTROL", fake_control)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="Derived evidence differs"):
        module.build(tmp_path / "tampered-output")
