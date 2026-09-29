import importlib.util
import json
from pathlib import Path

from mateprobe.validator_audit import audit_validator

PATH = Path(__file__).resolve().parents[1] / "examples" / "audit_existing_validator.py"
spec = importlib.util.spec_from_file_location("external_validator_demo", PATH)
assert spec is not None and spec.loader is not None
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


def test_demo_finds_missing_execution_checks_without_hiding_prose_survivor():
    before = audit_validator(
        demo.existing_validator, demo.cases(), obligations=demo.OBLIGATIONS, validator_id="before"
    )
    after = audit_validator(
        demo.corrected_validator, demo.cases(), obligations=demo.OBLIGATIONS, validator_id="after"
    )
    assert before.corpus_digest == after.corpus_digest
    assert before.summary()["counts"] == {"detected": 3, "preserved": 2, "survived": 6}
    assert after.summary()["counts"] == {"detected": 8, "preserved": 2, "survived": 1}
    cases = {case.id: case for case in after.cases}
    assert cases["prose-only-contradiction"].outcome == "survived"
    assert cases["honest-uncertainty"].outcome == "preserved"
    assert "untested" in after.to_markdown()
    json.dumps(after.to_dict(), allow_nan=False)


def test_external_audit_plugin_records_failure_and_success(pytester, monkeypatch):
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    pytester.makepyfile("""
from mateprobe.validator_audit import AuditCase, Obligation, Verdict
from mateprobe.mutations import Relation, Validity
from mateprobe.provenance import supplied_git_provenance

metadata = supplied_git_provenance("a" * 40)

cases = (
    AuditCase("fault", "positive", 1, -1, Relation.VIOLATION, ("negative",),
              Validity.VALID, "Negative integers violate the stated positive-only policy."),
    AuditCase("control", "positive", 1, 2, Relation.PRESERVE,
              validity=Validity.VALID, provenance="Both integers are positive."),
)
obligations = (Obligation("positive", "Input must be positive"),)

def test_correct(mateprobe):
    mateprobe.audit_validator(
        lambda n: Verdict(n > 0, () if n > 0 else ("negative",)),
        cases, obligations=obligations, validator_id="correct/1",
        provenance=metadata,
    )

def test_broken(mateprobe):
    mateprobe.audit_validator(
        lambda n: Verdict(True), cases, obligations=obligations, validator_id="broken/1",
        provenance=metadata,
    )
""")
    path = pytester.path / "report.json"
    result = pytester.runpytest_subprocess(
        "-p", "pytest_mateprobe.plugin", "--mateprobe-report", str(path)
    )
    result.assert_outcomes(passed=1, failed=1)
    result.stdout.fnmatch_lines(["*Validator audit failure:*", "*fault*survived*"])
    reports = json.loads(path.read_text())["reports"]
    assert len(reports) == 2
    assert all(report["type"] == "validator_audit" for report in reports)
    assert reports[1]["summary"]["detection_score"] == 0
    assert reports[1]["provenance"] == {
        "commit": "a" * 40,
        "dirty": None,
        "source": "supplied",
        "error": None,
    }
    assert reports[1]["schema_version"] == 2
