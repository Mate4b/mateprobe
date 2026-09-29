# pytest-narrative-contracts

Optional pytest integration for `narrative-contracts`, version `0.1.0a3`.

Install both packages from the repository root:

```sh
pip install -e . -e ./packages/pytest-narrative-contracts
```

The `narrative` fixture exposes `check(document, context, contracts, policy=None)` and
`audit(cases, contracts, detection=1.0, preservation=1.0, policy=None)`. Failures identify
the rule, status, surface and evidence. `--narrative-report=report.json` writes all reports,
including failed checks. Audit thresholds require both violation and preservation cases.

Pytest discovers this package through the `pytest11` entry point. The core library has
no pytest dependency. Serial JSON reports only; distributed report merging is not supported.

Alpha software; MIT license. General free-text truthfulness is outside its guarantees.

## Audit existing validators (a3)

Version 0.1.0a3 provides `narrative.audit_validator(validator, cases,
obligations=..., validator_id=..., detection=1.0, preservation=1.0)` for existing
validators. It records JSON results before asserting thresholds, including
failures. Install both packages at `0.1.0a3`; this API is not in older a2 wheels. See [the audit guide](../../docs/validator-audit.md).

`audit_validator` also accepts optional `provenance=...` from the explicit
Git helpers. Its nested report uses schema 2; the aggregate pytest envelope remains
schema 1. Missing metadata is not automatically inferred from CI environment
variables. See [provenance](../../docs/audit-provenance.md).
