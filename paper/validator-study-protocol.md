# Validator audit study protocol, version 1

Frozen before executing the new controlled experiment. This is an author-run,
prospective engineering experiment, not independent preregistration, a user study,
or an evaluation of natural-language truth. Historical reproduction has its own
protocol and candidate ledger; its results must not be pooled with this corpus.

## Questions and fixed scope

1. Which failures of specified validator policies are visible to a boolean
   rejection test, a detailed ordinary-Python/pytest comparator, and the a3 audit?
2. How do targeted attribution, valid controls, and explicit execution/unknown
   accounting affect the reported evidence on the same paired inputs?
3. Can historical public validator fixes be reproduced without an external team?

No claim of superiority over well-written pytest is hypothesized. The detailed
comparator should agree with the library on per-case classifications; disagreement
is a study defect to investigate and disclose, not an observation to suppress.
No inference calls, new model downloads, or human annotation are needed.

## Controlled corpus

Three authored policies have mechanically checkable labels:

- Refund completion requires a completed receipt for the same request.
- Shipment transitions must belong to a fixed application transition relation,
  and the order must belong to the authenticated customer.
- A reservation must have a positive integer quantity no greater than available
  capacity, and refer to the authoritative resource.

For each policy construct eight baseline groups, four single-obligation faults
and two valid variations per group: 144 paired cases in 24 groups. Variations in
numeric values and identifiers exercise plumbing; they are not independent
semantic phenomena. There is no held-out natural corpus. No precision/recall on
natural errors, population confidence interval, usability or effort claim follows.

Case labels and expected diagnostic IDs are fixed by the policy construction,
before evaluating a validator. A separate specification oracle verifies each
baseline and relation and identifies the intended violation. The implementation
under audit never receives the case label or expected IDs. Keep valid fields and
schema intact when mutating a domain obligation. Controls change irrelevant text
or another field while preserving the full specified policy.

## Validator profiles

Each policy has the same eight authored profiles: correct, omit-first-obligation,
wrong-diagnostic-ID, reject-valid-variation, crash-on-fault, unknown-on-fault,
accept-all, reject-all. Profiles are illustrative transformations of validators,
not discovered production bugs. All comparators observe the same recorded
baseline/variant outcomes; each callable is executed once per input for capture.

The boolean comparator checks accepted, complete baselines, then accepts any
completed rejection as detection and requires acceptance of valid controls.
It retains crashes and unknowns. The detailed comparator independently implements
explicit pytest-style checks for the expected finding IDs, completeness, valid
controls and valid baselines. The a3 audit consumes the same normalized recorded
outcomes, with one declared but untested obligation per policy to exercise the
inventory. This inventory is caller-supplied, not inferred coverage.

## Ablations and reporting

- No attribution: report the boolean comparator next to targeted results.
- No controls: retain fault counts and mark preservation undefined; never invent
  a perfect preservation score when the denominator is empty.
- Count errors as detection (deliberately invalid accounting): expose how much
  this would increase the apparent score; retain the proper result alongside it.
- Hide unknowns from the denominator (deliberately invalid accounting): show both
  the reduced denominator and undefined values if it removes every eligible fault.

Publish every pair, normalized baseline/variant outcome, detailed comparison,
library audit, profile counts, and disagreements. Broken baselines are counted
explicitly and excluded from eligible mutation denominators, never counted as
detections. A separate raw variant-rejection count explains why reject-all cannot
be trusted. Report counts by policy and profile; pooled counts are descriptive.
No runtime or authoring-effort advantage is inferred from this experiment.

## Freeze, reproduction and deviations

Commit this protocol before running the corpus. The prepare command writes the
corpus and records hashes of this protocol and generator/comparator source before
capture/evaluation. Evaluation checks those hashes and refuses changed inputs.
Publish results with dependency/runtime metadata and a separate stable replay
output. Offline replay must reproduce classifications byte-for-byte. Changes
after first execution require a disclosed deviation; never relabel a case or
alter a library rule just to improve a score. Existing a2 research stays frozen.

The study can support a tool demonstration with explicit limitations. External
adoption, commercial demand, time savings and arbitrary-prose correctness remain
unmeasured regardless of the results.
