# Audit adoption increment

This increment follows review of the independent-validator audit. It is source
development after published alpha `0.1.0a2`. That increment did not publish a new
package; its APIs are now included in [alpha a3](api-a3.md).

| Work | Why | Acceptance evidence |
|---|---|---|
| Audit-first README and adoption levels | Explain utility without requiring an architecture migration | Runnable entry point; boolean vs targeted attribution limits explicit |
| Actionable report | Make survivors and missing evidence visible first | Tests for mixed outcomes, excluded-only obligations, challenges and missing controls |
| Report provenance | Make archived results interpretable | Version/schema, corpus digest, supplied vs observed Git tests; no hidden IO |
| Two additional existing engines | Exercise adapters outside our own validator implementation | Real JSON Schema/Pydantic calls, pinned dependencies, paired controls, before/after config |
| Regression and integration checks | Preserve prior evidence while extending UX | Old frozen outputs unchanged; new cases in optional CI job; full core checks |

No new domain-contract DSL, universal semantic evaluator, or requirement for human
evaluation is added. Scope challenges remain in score denominators. No obligation
is labelled universally "covered" or "fully correct" after a finite case suite.

The trials measure adapter size and authored case counts. They do not measure
independent developer integration time, adoption, production fault frequency, or
novel bug discovery. Default library behavior weaker than an authored domain policy
is described as a configuration gap, not a defect in the external library.

Deliverables are source, documentation, report examples, optional integration tests,
and GitHub CI. The future external-adoption question remains whether an independent
team can reproduce a useful missed fault in its own validator with acceptable effort.
