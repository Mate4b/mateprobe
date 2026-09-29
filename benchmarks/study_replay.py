"""Replay immutable a3 study drivers against MateProbe without changing their sources.

The CLI runs in its own process. Tests use the same scoped import bridge. Archived
reports stay unchanged; comparison permits only explicit library-version metadata.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path

import mateprobe
import mateprobe.model
import mateprobe.mutations
import mateprobe.validator_audit

ROOT = Path(__file__).resolve().parents[1]
DRIVERS = {"validator_study", "historical_validator_study", "historical_followup"}


@contextmanager
def legacy_imports():
    aliases = {
        "narrative_contracts": mateprobe,
        "narrative_contracts.model": mateprobe.model,
        "narrative_contracts.mutations": mateprobe.mutations,
        "narrative_contracts.validator_audit": mateprobe.validator_audit,
    }
    if any(
        name in sys.modules and sys.modules[name] is not module for name, module in aliases.items()
    ):
        raise RuntimeError("Use an environment without an already imported legacy library")
    existing = {name: sys.modules[name] for name in aliases if name in sys.modules}
    try:
        sys.modules.update(aliases)
        yield
    finally:
        for name in aliases:
            if name in existing:
                sys.modules[name] = existing[name]
            else:
                sys.modules.pop(name, None)


def load_runner(name):
    if name not in DRIVERS:
        raise ValueError("Unknown frozen study driver")
    spec = importlib.util.spec_from_file_location(name, ROOT / "benchmarks" / (name + ".py"))
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compare_outputs(study, frozen, replay):
    names = ("summary.json", "audit-reports.json")
    if study == "controlled":
        names += ("comparisons.json", "observations.json")
    for name in names:
        expected = json.loads((frozen / name).read_text())
        actual = json.loads((replay / name).read_text())
        normalized = deepcopy(actual)
        if name == "audit-reports.json":
            if expected.keys() != normalized.keys():
                raise ValueError("Replay report membership changed")
            metadata = [(expected[key], normalized[key]) for key in expected]
        elif name == "summary.json" and study == "controlled":
            metadata = [(expected, normalized)]
        else:
            metadata = []
        for old, new in metadata:
            if (
                old["library_version"] != "0.1.0a3"
                or new["library_version"] != mateprobe.__version__
            ):
                raise ValueError("Unexpected replay library version")
            new["library_version"] = old["library_version"]
        if expected != normalized:
            raise ValueError(f"Study replay differs beyond library version: {name}")


def replay_all(output):
    output.mkdir(parents=True, exist_ok=False)
    with legacy_imports():
        controlled = load_runner("validator_study")
        frozen = ROOT / "benchmarks/validator-study"
        controlled.run(frozen / "prepared", output / "controlled", frozen / "evaluation")
        compare_outputs("controlled", frozen / "evaluation", output / "controlled")
        historical = load_runner("historical_validator_study")
        historical.replay(historical.OUT / "captured", output / "historical")
        compare_outputs("historical", historical.OUT / "evaluation", output / "historical")
        followup = load_runner("historical_followup")
        followup.verify()
        followup.base.replay(followup.OUT / "captured", output / "followup")
        compare_outputs("followup", followup.OUT / "evaluation", output / "followup")
    (output / "compatibility.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "frozen_library_version": "0.1.0a3",
                "replay_library_version": mateprobe.__version__,
                "studies": ["controlled", "historical", "followup"],
                "allowed_difference": "library_version in reports and controlled summary only",
                "scope": "Reclassification of frozen observations; not new third-party executions.",
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New output directory")
    replay_all(parser.parse_args().output.resolve())
