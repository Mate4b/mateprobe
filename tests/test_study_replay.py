import sys
from pathlib import Path
from runpy import run_path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_historical_import_bridge_cleans_up_after_failure():
    runtime = run_path(str(ROOT / "benchmarks/study_replay.py"))
    before = {
        key: value for key, value in sys.modules.items() if key.startswith("narrative_contracts")
    }
    with pytest.raises(RuntimeError, match="study failure"):
        with runtime["legacy_imports"]():
            runtime["load_runner"]("validator_study")
            raise RuntimeError("study failure")
    after = {
        key: value for key, value in sys.modules.items() if key.startswith("narrative_contracts")
    }
    assert after == before


def test_historical_import_bridge_refuses_mixed_runtime(monkeypatch):
    runtime = run_path(str(ROOT / "benchmarks/study_replay.py"))
    legacy = ModuleType("narrative_contracts")
    monkeypatch.setitem(sys.modules, "narrative_contracts", legacy)
    with pytest.raises(RuntimeError, match="already imported legacy"):
        with runtime["legacy_imports"]():
            pytest.fail("Must not mix installed library implementations")
    assert sys.modules["narrative_contracts"] is legacy
