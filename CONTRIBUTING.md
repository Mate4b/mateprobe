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
entry-point discovery before releasing. Release only after the documented executable gates pass. Never claim paper acceptance or
independent validation from an engineering release.


## Community evaluation

Use the issue templates for valid text rejected, missed obligations and new contracts. Include
package/rule versions, a minimal runnable bundle, authoritative state, the full report and a
reasoned expectation. Keep reports fictional or explicitly publishable. A community report is
not automatically a confirmed label: maintainers reproduce it, distinguish in-scope behavior
from a scope extension, and add both a regression case and a valid control when appropriate.

Never rewrite historical benchmark labels to improve a score. Label corrections require a
separate versioned corpus, provenance and a comparison with the previous result. Keep related
scenarios, languages, model variants and mutations grouped when splitting data. No contributor
needs paid model access: CI and replay use committed fixtures and captured outputs offline.

External adoption, human review and calibrated judge comparisons remain welcome; none is a
prerequisite for submitting reproducible counterexamples or shipping this alpha.
