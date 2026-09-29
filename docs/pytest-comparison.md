# What MateProbe adds to an ordinary pytest test

Both approaches can express the same checks. The executable comparison uses the
same refund validators, 11 authored pairs and stable diagnostic IDs. No time,
maintenance effort, usability or superiority measurement is inferred from it.

## Run the comparison

From the a3 study checkout, with its development dependencies installed:

```sh
python benchmarks/pytest_comparison.py --output /tmp/mateprobe-pytest-comparison
```

The output directory must be new. The command launches ordinary pytest with plugin
autoload disabled, retains its JUnit results, then runs the public MateProbe audit
on the same cases. The driver succeeds only when all case-level outcomes agree.
The underlying example pytest run intentionally returns exit code 1: its failures
are the surviving faults that the comparison is demonstrating.

| Validator | Ordinary pytest | MateProbe fault detection | Valid controls |
|---|---|---|---|
| Before receipt repair | 5 passed, 6 failed | 3/9 | 2/2 preserved |
| After receipt repair | 10 passed, 1 failed | 8/9 | 2/2 preserved |

There are 22 paired classifications with zero disagreements. Passing pytest cases
include valid controls; the audit's fault denominator excludes those controls.
Do not compare 10/11 pytest passes to 8/9 fault detections as though they measured
the same property. The remaining failure in both approaches is the prose-only
contradiction. Neither validator checks arbitrary text entailment.

[Plain pytest implementation](../examples/pytest_audit_comparison.py) ·
[Execution driver](../benchmarks/pytest_comparison.py) ·
[Every comparison](../benchmarks/pytest-comparison/evaluation/comparisons.json) ·
[Raw pytest output](../benchmarks/pytest-comparison/evaluation/pytest-output.txt) ·
[Audit report after repair](../benchmarks/pytest-comparison/evaluation/after-audit.md).

## Work shared by both approaches

The maintainer defines authoritative context, adapts the validator, supplies
baseline/variant pairs, assigns relations and expected IDs, and reviews labels.
MateProbe does not automatically perform these steps. Both approaches must update
fixtures or diagnostic expectations when the application policy changes.

## What the examples implement

| Concern | This plain pytest implementation | MateProbe audit |
|---|---|---|
| Accepted, complete baseline | Explicit assertions | Built-in prerequisite, reported per case |
| Rejected fault with expected IDs | Explicit assertions | Built-in diagnostic matching |
| Preserved valid variation | Explicit assertion | Separate preservation outcome and denominator |
| Unexpected exception | pytest error/failure information | Separate audit error or baseline failure |
| Missing coverage for a declared obligation | Not implemented in this short suite | Inventory identifies untested idempotency |
| Counts by obligation and separate eligible denominators | Would need aggregation code | Included in the JSON/Markdown report |
| CI failure and diagnostics | Built into pytest | Audit gates integrate with pytest |

The last two reporting features can also be implemented in ordinary Python and
pytest. This table compares the supplied examples, not the maximum capabilities
of either tool. For equivalent accounting across baseline failures, wrong IDs,
unknowns and crashes, the [controlled study](validator-study.md) includes a more
complete assertion-based reference and reports agreement on all 1,152 outcomes.

A detection ID demonstrates an observed diagnostic match, not correct internal
reasoning. Known gaps and untested obligations remain visible even when an
aggregate detection threshold passes.
