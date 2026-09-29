# LifeCard validator audit

Requires `narrative-contracts==0.1.0a3`. These APIs are not available in a2.

`examples/lifecard_validator_audit.py` is an opt-in, read-only demonstration of
the validator audit API against a local LifeCard checkout. It imports
LifeCard's existing Phase 4 fixture helpers at runtime; no LifeCard card,
state, or private fixture is copied into this repository.

Run it with the Python environment that has LifeCard and its dependencies
installed:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python examples/lifecard_validator_audit.py \
  --lifecard-root /path/to/Lifecard \
  --output /tmp/lifecard-audit.json
```

The JSON output includes the audit report, an SHA-256 manifest for the LifeCard
runtime and fixture source files, and the stable finding attribution used for
violation IDs (`lifecard.CardValidatorPipeline:<code>:<path>`).
The adapter constructs a fresh pipeline, spec, and state for every case and
never writes to the LifeCard checkout.

The generated JSON includes the local `lifecard_root` path and validator evidence.
Keep reports from a private checkout local; remove private paths and review finding
messages before sharing a sanitized reproduction. These generated reports are not
included in this repository.

The cases are authored targeted stress cases. They demonstrate three useful
boundaries: a short label restatement is reported; padding the repeated label
to at least 90 characters bypasses the current anti-bureaucracy guard; and a
whitespace-only control remains accepted. An empty-effects case exercises the
meaningful effect finding. The padded case is separately inventoried as a
broader, length-independent policy challenge, beyond the current guard's
declared scope. These labels are policy declarations for this demonstration,
not an independent gold set or a claim that the adapter discovered unknown
defects.

The 90-character behavior is intentional context for the example: LifeCard's
current guard only computes overlap for outcome bodies shorter than 90
characters. The padded survivor does not violate that stated short-text contract;
it exposes a gap only against the separate, broader length-independent obligation.
The adapter records the observed
result and does not change LifeCard.

Ordinary LifeCard pytest tests answer whether individual examples satisfy the
validator. This audit adds paired baseline/variant cases, explicit relation
and validity labels, stable violation IDs, and aggregate reporting. It does
not replace LifeCard's tests or claim a reduction in test code.
