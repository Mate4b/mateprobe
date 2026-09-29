from pathlib import Path
from runpy import run_path

import pytest

pytest_plugins = ["pytester"]


@pytest.fixture
def study_runtime():
    runtime = run_path(str(Path(__file__).resolve().parents[1] / "benchmarks/study_replay.py"))
    with runtime["legacy_imports"]():
        yield runtime
