# Audit your existing validator

Requires `mateprobe==0.1.0a4`. These APIs are not available in a2.
After publication, install the core and optional pytest plugin from PyPI; see the
[migration guide](migration-mateprobe.md). An editable checkout is only needed for development.

Use `audit_validator` when you already have a validator and want to test its
failure modes. It does not require `Document`, `Context`, `Surface`, model calls,
or a replacement for your existing validation framework. You supply:

1. A small adapter returning `Verdict` from your current validator.
2. An explicit inventory of obligations.
3. Paired baseline/variant cases, each with a justified label and target finding IDs.

The library runs those pairs, attributes detections, keeps false rejections and
execution errors visible, and produces a JSON/Markdown report. This is a test
harness, not automatic grounding or proof of business correctness.

Start with [adoption levels](adoption-levels.md) for boolean validators, finding IDs,
scoped findings and incomplete evidence. [Third-party trials](external-validator-integrations.md)
exercise JSON Schema and Pydantic adapters. [Report provenance](audit-provenance.md)
explains schema 2 and optional observed/supplied Git metadata.

## Minimal runnable example

```python
from mateprobe.mutations import Relation, Validity
from mateprobe.validator_audit import AuditCase, Obligation, Verdict, audit_validator


# Your existing code. Keep its real finding IDs rather than using a generic "bad".
def validate_refund(data):
    errors = () if data["amount_cents"] <= data["limit_cents"] else ("amount_exceeded",)
    return Verdict(accepted=not errors, violations=errors)


baseline = {"amount_cents": 5000, "limit_cents": 6000}
cases = (
    AuditCase(
        id="over-limit",
        obligation="refund-limit",
        baseline=baseline,
        variant={"amount_cents": 6001, "limit_cents": 6000},
        relation=Relation.VIOLATION,
        expected=("amount_exceeded",),
        validity=Validity.VALID,
        provenance="Authored arithmetic case: 6001 > the authoritative limit of 6000.",
    ),
    AuditCase(
        id="at-limit",
        obligation="refund-limit",
        baseline=baseline,
        variant={"amount_cents": 6000, "limit_cents": 6000},
        relation=Relation.PRESERVE,
        validity=Validity.VALID,
        provenance="Authored boundary control: the inclusive limit permits 6000.",
    ),
)
obligations = (Obligation("refund-limit", "Refund must not exceed the permitted amount."),)
report = audit_validator(
    validate_refund,
    cases,
    obligations=obligations,
    validator_id="refund-limit/1",
)
report.assert_thresholds()  # Requires detection AND preservation denominators.
print(report.to_markdown())
```

These two cases do not test negative values, input schemas, identities, permissions,
currency conversion, execution, or prose. Inventory those obligations explicitly
if they matter. This example alone is not a refund authorization implementation.

## Adapting other validators

Normalize the validator's actual acceptance policy and **blocking** finding IDs.
Warnings can go in `evidence`, but an accepted verdict cannot contain violations.
Use stable scoped IDs (`RULE_CODE:$.options[0]`, for example) if a finding at the
wrong location must not count. Use `complete=False` when the validator cannot
establish a result because evidence is missing. Preserve errors as exceptions;
do not turn a crash into a successful detection.

A boolean validator can be wrapped as `Verdict(accepted=bool_result)` to inspect
raw behavior, but a rejection with no finding IDs is **unattributed**, not a
targeted detection. Do not copy the expected case labels into the adapter to
manufacture attribution. The adapter receives the sample, not the case's expected
answer. Schema rejection likewise is not automatically detection of the intended
business violation.

## Results and denominators

| Outcome | Meaning |
|---|---|
| `detected` | The variant was rejected with every expected finding ID. |
| `survived` | An authored invalid variant was accepted. |
| `unattributed_rejection` | Rejected, but expected findings were absent. |
| `preserved` | An authored valid variation was accepted and completely evaluated. |
| `regressed` | An authored valid variation was rejected. |
| `undetermined` | The variant could not be completely evaluated. |
| `error` | The variant evaluation crashed or returned an invalid result. |
| `baseline_failed` | The supposedly valid baseline was rejected, incomplete, or errored. |
| `excluded` | Unreviewed, equivalent, or identical baseline/variant. |

Variant errors and unknowns stay in the fault/control denominators and do not
count as detections or preservations. Failed baselines cannot support a paired
comparison; they remain visible and fail `assert_thresholds`, even when other
pairs pass. Thus a reject-everything validator cannot earn a passing audit.
Exclusions remain in the report; scores always depend on the declared eligible
corpus. `Validity.VALID` is the author's claim, not independent adjudication.

Each report contains per-obligation outcomes, including declared obligations with
no cases (`untested`). There is deliberately no percentage labelled "agent
coverage": touching a field or passing a case is not proof that an obligation is
fully enforced. Reports record case rationale, expected IDs, verdict evidence,
input digests, and a corpus digest. Full input samples are not embedded, so retain
your corpus separately. Evidence/exception messages may still contain application
data; review reports before sharing them.

The Markdown report leads with known gaps, then incomplete evidence/execution
failures, then untested or unevaluated obligations. Excluded-only obligations are
`not_evaluated`; controls-only and faults-only cases are identified separately.
The table's `no_failures_observed` applies only to the evaluated corpus. Errors
remain visible even when the same obligation also has a survivor.

Mark a deliberately broader-policy obligation with `scope="challenge"`. This
is caller-supplied scope metadata, not a label inferred by the tool. It does **not**
exclude the cases or remove them from scores. In particular, the refund demo's
prose-only contradiction is included in its nine-fault denominator: the result
after correction remains **8/9**, not 8/8.

`validator_id` is a caller-supplied implementation/configuration identifier, not
an automatically verified code hash. The optional `provenance` argument accepts
explicitly observed or supplied Git metadata; default audit execution performs no
Git lookup. `library_version` and `schema_version` are included automatically.
Inputs must be JSON-encodable (including
JSON-valued dataclasses) and deep-copyable. Validators receive isolated copies;
the harness does not sandbox filesystem, network, closure, or service side effects.
Run it against pure validation code or a controlled offline test environment.
One run does not measure stochastic stability or latency.

## Pytest and reports

```python
def test_refund_guard(mateprobe):
    mateprobe.audit_validator(
        validate_refund,
        cases,
        obligations=obligations,
        validator_id="refund-limit/1",
        detection=1.0,
        preservation=1.0,
    )
```

Run `pytest --mateprobe-report=report.json`. The plugin records failed audits
before raising an assertion, so CI reports retain the cases that failed.
Existing `mateprobe.check` and `mateprobe.audit` remain available.

## Full demonstrations

```sh
python examples/audit_existing_validator.py --output /tmp/refund-audit
```

The fictional refund flow preserves the same corpus before and after a code
fix. Initially it detects 3 of 9 authored faults; after checking execution
receipts, it detects 8 of 9. Both valid controls are preserved. The remaining
prose-only contradiction stays visible, as does an untested idempotency obligation.
Missing receipts, timeouts, accepted-but-incomplete operations, and receipts for
another request/customer must not support a claim of successful completion.
A timeout is **not** proof of failure. The example executes no actions and does
not replace authorization or transactional checks in the real backend.

For an independently existing validator, use the opt-in
[LifeCard integration](lifecard-validator-audit.md). Its full pipeline is wrapped
without changing LifeCard or copying its private fixtures into this repository.

## What this saves, and what it does not

Ordinary pytest can express every individual comparison above. The harness adds
shared paired execution, baseline validity checks, attribution, failure accounting,
thresholds, and reports without implementing these mechanics for each project.
It does not save the domain work of defining the obligations, trusted evidence,
sample schema, mutations, or correct labels. We have measured executable examples,
not developer-hours saved, broad semantic accuracy, adoption, or market demand.
