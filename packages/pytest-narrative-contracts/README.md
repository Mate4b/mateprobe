# pytest-narrative-contracts

Optional pytest integration for `narrative-contracts`, version `0.1.0a2`.

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
