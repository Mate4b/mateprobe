# Contributing

Use Python 3.11+ and install the development extras plus the optional pytest package.
Run pytest, Ruff and mypy before proposing a change. A contract contribution must state its
scope, kind, assumptions, failure cases and version. Include positive controls and realistic
counterexamples, not only tests constructed to hit the implementation's threshold.

Keep rule execution pure and offline. Place application-specific policies in adapters/profiles.
Keep changes in evaluator semantics separate from benchmark label changes. Benchmark labels
must not be rewritten to make a new implementation score better. Record provenance, group
related variants together and publish survivors and false positives.

Core and plugin versions are synchronized during alpha. Test wheel installation and pytest
entry-point discovery before releasing. Do not publish packages or claim paper acceptance
from an unreviewed release candidate.
