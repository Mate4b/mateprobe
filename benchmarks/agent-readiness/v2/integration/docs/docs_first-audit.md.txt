# Your first validator audit

**Bring an existing validator. You do not need to adopt Document, Claim, or a new
policy language.** This small example targets published `0.1.0a3` and runs offline
after installation. The walkthrough is designed for a short demo; five minutes
is a presentation target, not measured integration time.

## Install and run without cloning the repository

Python 3.11+ is required. In a new directory:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install narrative-contracts==0.1.0a3 pytest-narrative-contracts==0.1.0a3
curl -fL https://mate4b.github.io/narrative-contracts/examples/first_audit.py -o first_audit.py
python first_audit.py --output audit-report
python -m pytest first_audit.py --narrative-report=pytest-audit.json
```

On Windows, activate with `.venv\Scripts\Activate.ps1` in PowerShell and download
[the same script](../examples/first_audit.py) into your directory. You can also
inspect or copy that single file before running it. No API keys, model, database,
Pydantic or JSON Schema package is needed. Installation and download use the network;
the example itself makes no network calls.

## What you will see

The initial validator only checks that a completion declaration is a boolean.
The correction additionally requires a completed backend receipt for the same
request whenever the declaration claims success.

| Supplied case | Before | After |
| --- | --- | --- |
| Claims completion without a receipt | survived | detected |
| Claims completion using another request's receipt | survived | detected |
| Honestly says completion is unconfirmed | preserved | preserved |
| Prose claims completion while the structured claim stays false | survived | survived |

The result is **0/3 → 2/3 targeted detections**, with **1/1 valid control preserved**.
The prose challenge remains inside the denominator. This tiny authored corpus is
not a measure of production accuracy or total policy coverage.

Open `audit-report/after.md` to see the known prose gap first, then the evidence
by obligation. Keep the JSON files if you want to compare subsequent validator
versions using the same cases. The larger [refund example](../examples/audit_existing_validator.py)
has a different corpus: 3/9 → 8/9, with two controls. Do not combine the scores.

## Keep the correction as a regression

`test_refund_policy` runs through the pytest fixture and records its audit. It
requires both completion faults to be detected and the valid control to survive.
It also asserts the identity of the one known prose survivor. The explicit 2/3
threshold acknowledges that survivor; it does not move the challenge out of the
score or allow another missed fault to replace it.

To see a regression fail, temporarily replace `after` with `before` in the
`narrative.audit_validator(...)` call inside `test_refund_policy`, then rerun pytest.
The command fails and `pytest-audit.json` retains the findings. Restore `after`.
A validator that rejects all samples fails baseline validation as well.

## Connect your own validator

Keep only the harness pattern; replace the example's domain code and fixtures:

1. Wrap your actual validator's result in `Verdict`. For a boolean function, use
   `Verdict(accepted=your_validator(sample))`. Rejections without finding IDs are
   unattributed; do not copy the case's expected IDs into the adapter.
2. Name one obligation from your actual policy. Supply a known-valid baseline,
   two justified invalid variants, and a valid variation that should still pass.
3. Use findings emitted by the validator for attribution, and inspect survivors,
   errors and controls before choosing CI thresholds. The adapter never receives
   test expectations. Keep future missed faults as permanent regression cases.

The caller supplies the schema-validated shape and trusted execution evidence.
In this demo the request ID identifies the operation; a real integration may also
need customer, order, amount and tenant bindings. A missing receipt does **not**
prove an API was never called, and a timeout does not prove the operation failed.
The library neither obtains that evidence nor verifies arbitrary prose.

[Adoption levels](adoption-levels.md) explain boolean and finding-based adapters.
[The regression guide](policy-regression.md) expands the CI workflow.
[Share an integration report](integration-feedback.md) even if you got stuck or
found no useful survivor; that is useful evidence too.
