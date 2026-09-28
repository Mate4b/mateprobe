import json
import subprocess
import sys

import pytest

from narrative_contracts import Claim, Context, DeclaredClaimsConsistent, evaluate
from narrative_contracts.adapters import lifecard_document
from narrative_contracts.serialization import load_bundle


def bundle():
    return {
        "document": {"surfaces": [{"id": "body", "text": "A sample."}]},
        "context": {"states": {"current": {"x": 1}}},
        "contracts": [{"type": "RequiredFact", "rule_id": "fact", "key": "x", "expected": 1}],
    }


def test_json_configuration_matches_python_api():
    doc, context, rules, policy = load_bundle(bundle())
    assert evaluate(doc, context, rules, policy).accepted


@pytest.mark.parametrize("field,value", [("type", "eval"), ("operator", "!="), ("state_ref", 5)])
def test_invalid_contract_configuration_fails_closed(field, value):
    data = bundle()
    data["contracts"][0][field] = value
    with pytest.raises((ValueError, TypeError)):
        load_bundle(data)


def test_bool_does_not_decode_as_numeric_threshold():
    data = bundle()
    data["contracts"] = [
        {"type": "MinimumTokens", "rule_id": "thin", "surface_ids": ["body"], "minimum": True}
    ]
    with pytest.raises(TypeError):
        load_bundle(data)


@pytest.mark.parametrize("state,exit_code", [(1, 0), (2, 1)])
def test_cli_exit_codes_and_json(tmp_path, state, exit_code):
    data = bundle()
    data["context"]["states"]["current"]["x"] = state
    path = tmp_path / "input.json"
    path.write_text(json.dumps(data))
    proc = subprocess.run(
        [sys.executable, "-m", "narrative_contracts.cli", str(path)], capture_output=True, text=True
    )
    assert proc.returncode == exit_code
    assert json.loads(proc.stdout)["accepted"] == (exit_code == 0)


def test_cli_invalid_input_exit_two(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"contracts": [{"type": "unknown"}]}')
    proc = subprocess.run(
        [sys.executable, "-m", "narrative_contracts.cli", str(path)], capture_output=True, text=True
    )
    assert proc.returncode == 2
    assert "Invalid contract bundle" in proc.stderr


def test_lifecard_adapter_preserves_branch_identity():
    card = {
        "title_template": "Offer",
        "body_template": "An offer arrives.",
        "options": [
            {
                "id": "accept",
                "label_template": "Accept",
                "outcomes": [
                    {"id": "yes", "title_template": "Accepted", "body_template": "You accept."}
                ],
            },
            {
                "id": "reject",
                "label_template": "Reject",
                "outcomes": [
                    {"id": "no", "title_template": "Rejected", "body_template": "You reject."}
                ],
            },
        ],
    }
    sid = "$.options[1].outcomes[0].body_template"
    doc = lifecard_document(card, claims_by_surface={sid: (Claim("status", "accepted"),)})
    ctx = Context({"accept/yes": {"status": "accepted"}, "reject/no": {"status": "rejected"}})
    assert doc.surface(sid).state_ref == "reject/no"
    assert not evaluate(doc, ctx, (DeclaredClaimsConsistent("claims", (sid,)),)).accepted


def test_plugin_fails_test_with_actionable_diagnostics_and_writes_report(pytester, monkeypatch):
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    pytester.makepyfile("""
from narrative_contracts import Context, Document, Surface, RequiredFact

def test_fact(narrative):
    narrative.check(Document((Surface("body", "Text"),)), Context({"current": {"x": 1}}),
                    (RequiredFact("must-be-two", "x", 2),))
""")
    report = pytester.path / "report.json"
    result = pytester.runpytest_subprocess(
        "-p", "pytest_narrative_contracts.plugin", "--narrative-report", str(report)
    )
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*Narrative contract failure:*", "*must-be-two*"])
    payload = json.loads(report.read_text())
    assert payload["reports"][0]["accepted"] is False


def test_plugin_audit_fixture(pytester, monkeypatch):
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    pytester.makepyfile("""
from narrative_contracts import Context, Document, Surface, MinimumTokens
from narrative_contracts.mutations import Sample, MutationCase, Relation, Target, Validity, replace_text

def test_audit(narrative):
    base = Sample(Document((Surface("body", "one two three four five six"),)), Context({}))
    bad = MutationCase("bad", "short", Relation.VIOLATION, base, replace_text(base, "body", "x"),
                       (Target("thin", "LOW_LEXICAL_CONTENT", "body"),), Validity.VALID, "short")
    good = MutationCase("good", "space", Relation.PRESERVE, base,
                        replace_text(base, "body", " one two three four five six "),
                        validity=Validity.VALID, provenance="spacing")
    narrative.audit((bad, good), (MinimumTokens("thin", ("body",), 6, 4),))
""")
    result = pytester.runpytest_subprocess("-p", "pytest_narrative_contracts.plugin")
    result.assert_outcomes(passed=1)
