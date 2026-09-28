# Protocol for an independent study

Status: proposed, not preregistered and not executed. Freeze and timestamp this protocol
before collecting final test labels. The included synthetic corpus is a development artifact
and must not become the final held-out test set.

## Questions

- RQ1: Which state-conditioned obligations can be checked with useful precision and recall
  on independently labelled natural outputs?
- RQ2: Does attributed mutation detection predict natural-error recall across validator profiles?
- RQ3: What valid variations produce false positives, and how much quality is lost by gating?
- RQ4: What do branch scoping, explicit unknowns and state projections add beyond simple assertions?
- RQ5: What are execution cost, latency, annotation cost and ongoing rule-maintenance effort?

## Corpus and labels

Use at least two independently implemented applications, ideally three, including LifeCard.
Collect natural outputs from several generator families at documented prompts/settings and
preserve authoritative state, selected branch, history, permitted facts and obligations.
Sample success-looking outputs as well as known failures; do not select only outputs that a
particular guard rejects. Record generator version, date, prompt digest and sampling procedure.

A starting collection target is 300 independent scenarios, balanced by application; this is
a planning target, not a power calculation. Use a pilot to estimate error prevalence and choose
a final sample size for a preregistered confidence-width or power requirement. Related outputs,
mutants and paraphrases remain grouped with their original scenario. Separate calibration,
development and held-out evaluation by scenario and, where practical, by fault family.

Two independent annotators judge each sample using the supplied authoritative context and
rubric without seeing evaluator outputs. Label each obligation as violated, satisfied or
not determinable, identify supporting spans, and record confidence. Adjudicate disagreements
with a third reviewer. Report agreement per obligation and distinguish ambiguous examples;
never silently remove them. Annotation provenance must be independent of the tested predicate.

## Mutations and invariances

Define operators and semantic preconditions before final evaluation. Examples: swap branch
outcomes; negate an authorized fact; replace an actor; reoffer a settled decision; remove a
required consequence; add unsupported state; zero a projected state delta. Independently verify
that each transformation induces its claimed violation. Separate equivalent, inapplicable and
unreviewed cases. Include harder preserved variants: legitimate repetition, quotations,
negation, paraphrases, inflection and Unicode changes.

Keep the original and every derivative in the same split. Inspect compound mutations separately
from single-obligation mutations; unrelated rejection does not establish target detection.

## Comparators

1. Simple Python assertions / configured deterministic-tool baseline.
2. Proposed profiles, including invariant-only and heuristic-only ablations.
3. At least two capable LLM judges, calibrated on the development split, with fixed rubrics.
4. A hybrid cascade, with the exact handoff policy frozen in advance.
5. Always-accept and always-reject controls.

Provide equivalent state and obligations to all comparators. Allow sensible rule authoring
and judge prompt calibration, then freeze both before test evaluation. Record that effort.
Use independent human labels as reference; a model judge must not label the test set that
will be used to establish its own or the proposed evaluator's quality.

## Analysis

Report per-obligation precision/recall, false-positive rate on valid variants, attribution
accuracy, unknown/error rates, acceptance coverage and mutation exclusions. Distinguish
micro-averages from macro-averages over applications and fault families. Analyze reject-all
and accept-all behavior explicitly. Use paired comparisons and uncertainty estimated at the
scenario/application grouping level, not independent bootstrap of individual mutants.

Measure whether mutation metrics predict natural-error detection across multiple independently
frozen profiles; do not infer predictive validity from a single profile. Report latency
median/p95, infrastructure and token cost, retries, and human authoring/maintenance time.
Perform error analysis on survivors and false positives before claiming practical utility.

## Release criteria

Publish raw permitted examples, labels, code, contract versions, prompt configurations, random
seeds, environment lockfiles and aggregate reports. Remove private application content or use
reproducible consented replacements. Publish failures and exclusions. Select publication venue
and contribution claim only after seeing independent evidence. No submission or public release
has occurred as part of the alpha artifact.
