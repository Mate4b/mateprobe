import importlib.util
import json
from importlib.metadata import version
from pathlib import Path

import pytest

pytest.importorskip("jsonschema")
if int(version("jsonschema").split(".")[0]) < 4:
    pytest.skip("Integration requires jsonschema 4+", allow_module_level=True)
pytest.importorskip("pydantic", minversion="2.0")

from mateprobe.validator_audit import audit_validator

PATH = Path(__file__).resolve().parents[1] / "examples" / "external_validators.py"
spec = importlib.util.spec_from_file_location("external_validators", PATH)
assert spec is not None and spec.loader is not None
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


def test_jsonschema_format_annotation_is_before_after_difference():
    before = audit_validator(
        demo.jsonschema_before,
        demo.jsonschema_cases(),
        obligations=demo.JSON_OBLIGATIONS,
        validator_id="before",
    )
    after = audit_validator(
        demo.jsonschema_after,
        demo.jsonschema_cases(),
        obligations=demo.JSON_OBLIGATIONS,
        validator_id="after",
    )
    assert before.corpus_digest == after.corpus_digest
    assert before.summary()["counts"] == {"detected": 1, "preserved": 1, "survived": 2}
    assert after.summary()["counts"] == {"detected": 3, "preserved": 1}
    result = {case.id: case for case in after.cases}["ipv4-999-range"]
    assert result.variant is not None and result.variant.violations == ("format@/address",)
    json.dumps(after.to_dict(), allow_nan=False)


def test_measurement_manifest_counts_real_adapter_helpers():
    manifest = demo._measurement_manifest(
        "jsonschema-ipv4",
        demo.jsonschema_before,
        demo.jsonschema_after,
        demo.jsonschema_cases,
        demo.JSON_OBLIGATIONS,
        (demo._jsonschema_adapter,),
        None,
    )
    assert manifest["component_loc"]["normalization_adapter"] == demo._source_lines(
        demo._jsonschema_adapter
    )
    assert manifest["authored_corpus"] == {"cases": 4, "obligations": 2}
    assert "authored expected IDs" not in manifest["manual_mapped_fields"]


def test_pydantic_http_default_is_weaker_than_https_policy():
    before = audit_validator(
        demo.pydantic_before,
        demo.pydantic_cases(),
        obligations=demo.PYDANTIC_OBLIGATIONS,
        validator_id="before",
    )
    after = audit_validator(
        demo.pydantic_after,
        demo.pydantic_cases(),
        obligations=demo.PYDANTIC_OBLIGATIONS,
        validator_id="after",
    )
    assert before.corpus_digest == after.corpus_digest
    assert before.summary()["counts"] == {"detected": 1, "preserved": 1, "survived": 1}
    assert after.summary()["counts"] == {"detected": 2, "preserved": 1}
    assert any("@/url" in violation for violation in after.cases[0].variant.violations)
    assert any("@/url" in violation for violation in after.cases[1].variant.violations)
    json.dumps(after.to_dict(), allow_nan=False)
