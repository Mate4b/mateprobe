# Five-minute quickstart

This walkthrough is fully offline. It uses the deterministic `0.1.0a3` API and
does not call a model, a service, or a network endpoint while evaluating a
document. The runnable version is [`examples/five_minute_demo.py`](../examples/five_minute_demo.py).

## Install from PyPI

A fresh Python 3.11+ environment can install both published alpha packages:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install narrative-contracts==0.1.0a3 pytest-narrative-contracts==0.1.0a3
```

The pytest plugin is optional. It adds the `narrative` pytest fixture and the
`--narrative-report` option; the core package has no pytest dependency. When
working from this checkout, the equivalent editable install is:

```sh
python -m pip install -e '.[dev]' -e ./packages/pytest-narrative-contracts
```

## Run the offline tour

If you have the repository checkout, run from its root:

```sh
.venv/bin/python examples/five_minute_demo.py
```

Without a checkout, download the pinned example, then run it with your activated environment:

```sh
curl -fsSL https://raw.githubusercontent.com/Mate4b/narrative-contracts/fe771c43e8c56a7aee71509dbea316af650b01b2/examples/five_minute_demo.py -o five_minute_demo.py
python five_minute_demo.py
```

Installing packages and downloading the example require network access. The demo itself is offline.

The flow is deliberately visible in the output:

1. **State:** trusted application code computes `refund_eligible` and supplies
   `current`, `refund_eligible`, and `refund_ineligible` scalar snapshots.
2. **Text:** a `Surface` carries reply text, a `state_ref`, and explicit
   `Claim` annotations. The text never chooses or mutates a snapshot.
3. **Contract:** `RequiredFact`, `StateChanged`, and
   `DeclaredClaimsConsistent` check exact facts; `MinimumTokens` is labelled a
   heuristic lexical check.
4. **Diagnosis:** each check prints its status, rule ID, finding code, scope,
   and evidence. A report is accepted only under its `Policy`, and complete
   means no check is `undetermined` or `error`.

The accepted case has claims matching the selected branch. The wrong-branch
declaration copies `refund.eligible=False` and `refund.action="deny"` into the
eligible branch; `DeclaredClaimsConsistent` rejects it with an attributable
`CLAIM_STATE_MISMATCH` finding. The final text explicitly says that the refund
is ineligible and will be denied, while retaining the original correct claims.
It is accepted because the library checks the declared claims against state and
does not parse arbitrary prose for entailment.
That acceptance is a visible guarantee boundary, not evidence that the prose is
true or useful. A controlled renderer or a separately validated text-to-state
step is needed for that stronger guarantee.

The final section runs a two-case mutation audit: one valid, manually labelled
wrong-branch fault and one valid paraphrase control. `audit()` counts the fault
only when the expected rule ID, finding code, and scope are all violated. It
counts the control only when it remains accepted and complete. `Validity.VALID`
and its provenance are caller-supplied labels; this small audit is a diagnostic
example, not an independent semantic adjudicator.

## Add the pytest fixture

The plugin is discovered through its `pytest11` entry point after installing the
pytest plugin. A minimal test can reuse the same objects from an application
module:

```python
from narrative_contracts import Claim, Context, DeclaredClaimsConsistent, Document, Surface


def test_reply_contract(narrative):
    document = Document(
        (
            Surface(
                "reply",
                "The request is ready for the next step.",
                state_ref="current",
                claims=(Claim("request.status", "ready"),),
            ),
        )
    )
    context = Context({"current": {"request.status": "ready"}})
    contracts = (DeclaredClaimsConsistent("reply-claims", ("reply",)),)
    report = narrative.check(document, context, contracts)
    assert report.accepted and report.complete
```

Run it serially and optionally write the structured reports:

```sh
.venv/bin/pytest \
  --narrative-report=contract-results.json
```

The plugin records checks and mutation audits in JSON. It does not add prose
entailment, distributed report merging, or a semantic truth oracle. For the
full result-state and mutation semantics, see [`docs/contracts.md`](contracts.md).
