import importlib.util
from pathlib import Path

from narrative_contracts.model import digest
from narrative_contracts.mutations import audit

spec = importlib.util.spec_from_file_location(
    "benchmark", Path(__file__).parents[1] / "benchmarks/run.py"
)
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)


def test_benchmark_is_reproducible_and_keeps_hard_failures_visible():
    cases = benchmark.dataset(1729, 1)
    assert digest(cases) == digest(benchmark.dataset(1729, 1))
    report = audit(cases, benchmark.RULES)
    summary = report.summary()
    assert summary["counts"].get("excluded", 0) == 0
    assert 0 < summary["detection_score"] < 1
    assert 0 < summary["preservation_rate"] < 1
    families = summary["families"]
    assert families["challenge_undeclared_contradiction"]["survived"] == 6
    assert families["challenge_negated_formula"]["regressed"] == 6


def test_always_reject_is_not_a_good_validator():
    metrics = benchmark.binary_metrics(benchmark.dataset(1729, 1), lambda s: False)
    assert metrics["recall"] == 1
    assert metrics["valid_variant_acceptance"] == 0
    assert metrics["baseline_rejections"] == 90
