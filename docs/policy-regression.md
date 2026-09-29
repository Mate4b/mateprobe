# Turn a survivor into a regression check

This guide shows how to preserve a real audit failure while fixing the validator
that caused it. It uses the development-checkout `audit_validator` API; it does
not require replacing the validator or adding a new policy language. The example
is self-contained and uses no private application data.

## 1. Keep the survivor and a valid control

Suppose refunds are allowed only in USD and only up to the supplied limit. The
existing validator checks the amount but forgets the currency rule:

```python
from narrative_contracts.mutations import Relation, Validity
from narrative_contracts.validator_audit import (
    AuditCase,
    Obligation,
    Verdict,
    audit_validator,
)


def validate_refund_before(data):
    violations = ()
    if data["amount_cents"] > data["limit_cents"]:
        violations = ("amount_exceeded",)
    return Verdict(accepted=not violations, violations=violations)


baseline = {"amount_cents": 5000, "limit_cents": 6000, "currency": "USD"}
cases = (
    AuditCase(
        id="over-limit",
        obligation="refund-policy",
        baseline=baseline,
        variant={"amount_cents": 6001, "limit_cents": 6000, "currency": "USD"},
        relation=Relation.VIOLATION,
        expected=("amount_exceeded",),
        validity=Validity.VALID,
        provenance="Reviewed policy case: 6001 exceeds the limit of 6000.",
    ),
    AuditCase(
        id="unsupported-currency",
        obligation="refund-policy",
        baseline=baseline,
        variant={"amount_cents": 5000, "limit_cents": 6000, "currency": "EUR"},
        relation=Relation.VIOLATION,
        expected=("currency_not_supported",),
        validity=Validity.VALID,
        provenance="Reviewed policy case: refunds are limited to USD.",
    ),
    AuditCase(
        id="at-limit-usd",
        obligation="refund-policy",
        baseline=baseline,
        variant={"amount_cents": 6000, "limit_cents": 6000, "currency": "USD"},
        relation=Relation.PRESERVE,
        validity=Validity.VALID,
        provenance="Reviewed control: the inclusive USD limit permits 6000.",
    ),
)
obligations = (Obligation("refund-policy", "Refunds must be USD and no greater than the limit."),)

before = audit_validator(
    validate_refund_before,
    cases,
    obligations=obligations,
    validator_id="refund-policy/1",
)
assert {case.id: case.outcome for case in before.cases} == {
    "over-limit": "detected",
    "unsupported-currency": "survived",
    "at-limit-usd": "preserved",
}
```

`unsupported-currency` is the survivor: the authored invalid variant was
accepted. `over-limit` is a real detected fault, and `at-limit-usd` is the
preservation control. Keep both when fixing the validator; a reject-everything
change must not make the audit pass.

## 2. Fix the validator, then run the same corpus

Add the missing blocking finding to the validator. The adapter still receives
only the sample; it must not receive `case.expected` or copy labels into the
result.

```python
def validate_refund_after(data):
    violations = []
    if data["amount_cents"] > data["limit_cents"]:
        violations.append("amount_exceeded")
    if data["currency"] != "USD":
        violations.append("currency_not_supported")
    return Verdict(accepted=not violations, violations=tuple(violations))


after = audit_validator(
    validate_refund_after,
    cases,
    obligations=obligations,
    validator_id="refund-policy/2",
)
assert {case.id: case.outcome for case in after.cases} == {
    "over-limit": "detected",
    "unsupported-currency": "detected",
    "at-limit-usd": "preserved",
}
after.assert_thresholds()
print(after.to_markdown())
```

The `AuditCase` labels and rationales are the user's responsibility: review the
baseline, decide whether each variant is a violation or preservation, name the
obligation, and provide the expected stable finding IDs. The user also owns the
adapter's mapping from real validator output to `Verdict`, the scope convention
for IDs, and any domain authorization or backend checks.

The library's responsibility is narrower: isolate and run paired inputs, verify
the baseline, compare the returned `Verdict` with the authored expectation,
classify outcomes such as `survived`, `detected`, `preserved`, `regressed`,
`unattributed_rejection`, `undetermined`, and `error`, and retain those results
in the report. It does not infer truth labels, inspect arbitrary prose, prove
business correctness, or turn an exception into a detection. A rejection with
the wrong or missing finding ID is `unattributed_rejection`.

## 3. Keep it in pytest and CI

Save the Python blocks above and the following test in
`tests/test_refund_policy.py`. In your application, import the actual fixed
validator instead of copying this illustrative implementation. Keep the cases
unchanged when revising the validator.

```python
def test_refund_policy(narrative):
    narrative.audit_validator(
        validate_refund_after,
        cases,
        obligations=obligations,
        validator_id="refund-policy/2",
    )
```

```sh
python -m pytest tests/test_refund_policy.py --narrative-report=refund-audit.json
```

The default gate requires targeted detection of every eligible fault and preservation
of every eligible control, and fails on broken baselines. Removing the currency
check makes this test fail again; replacing the validator with reject-all also fails.
The plugin retains its JSON report on threshold failure. These thresholds cover
this corpus, not every possible policy input.

## 4. Share sanitized feedback

Use this template when reporting a useful survivor outside the private project.
Replace placeholders with public, synthetic, or redacted values. Do not paste
raw samples, customer identifiers, tokens, receipt contents, stack traces, or
evidence strings that contain application data. The report stores digests rather
than full inputs, but evidence and exception messages still require review.

```text
Title: survivor in <public obligation or rule name>

Library checkout/version: <commit or local version>
Validator adapter version: <public identifier>
Audit validator ID: <public validator_id>

Expected policy (sanitized): <one sentence>
Case ID: <stable public case id>
Relation: VIOLATION or PRESERVE
Validity: VALID
Expected finding IDs: <public IDs only>
Case rationale: <why the baseline and variant are justified>

Observed outcome: survived | detected | preserved | regressed | ...
Observed public finding IDs: <IDs, or none>
Reproduction: <minimal synthetic input or pseudocode with private values removed>
Fix status: <unfixed / fixed locally / fixed in public change>
Regression result after fix: <outcome and control outcome>
```

Include a sanitized `to_markdown()` excerpt only after checking evidence and
exception text. A survivor report is a focused reproducible case, not a claim of
coverage or a claim that the library labels cases automatically.
