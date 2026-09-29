# Shipping assistant adoption trial

## Scope

This integration uses only the published `narrative-contracts==0.1.0a2` and
`pytest-narrative-contracts==0.1.0a2` APIs. The trusted branch is hard-coded as
`dispatched` in application code. The independently supplied snapshots are
recorded in `build-info.json`. No model calls or Ollama were used.

## Initial failure and fix

Before implementation, this command was run from the trial directory:

```text
.venv/bin/pytest -q test_shipping_contract.py
```

It failed because the test file did not yet exist; the exact output and exit code
are preserved in `initial-failure.txt`. The implementation then added
`shipping_contract.py` and `test_shipping_contract.py`.

## Verification commands and final stdout

```text
.venv/bin/pytest -q test_shipping_contract.py --narrative-report=contract-results.json
.venv/bin/python generate_report.py > scenario-report.json
```

The final pytest stdout is preserved in `final-stdout.txt`. The generated
`contract-results.json` is the automatically discovered `narrative` fixture's
JSON report. `scenario-report.json` contains all six requested adapter cases.

## Limits

The schema enforces required fields, strict scalar types, and no extra fields;
the contract checks only the explicit `status` and `fee` claims against the
trusted snapshot. It does not establish that arbitrary prose in `body` agrees
with those claims, as shown by the deliberately accepted contradictory-prose
case. Missing snapshot evidence is reported as incomplete/undetermined. The
adapter cannot independently prove snapshot provenance beyond receiving it from
the caller, and this trial does not measure general semantic accuracy.
