# Contract semantics and limits

A contract evaluates `(document, context)` and emits checks with a stable rule ID,
version, kind, result status, finding code, surface/state scope, evidence and numeric
metrics where applicable. A finding code names the tested property; status determines
whether it was satisfied or violated. A satisfied check can therefore carry a code
such as `NO_DOMAIN_CHANGE` without asserting a failure occurred.

## Result states

- `satisfied`: this configured predicate was satisfied on the supplied inputs.
- `violated`: this configured predicate was falsified on the supplied inputs.
- `undetermined`: required evidence, annotations or supported recognizers are missing.
- `error`: rule execution failed or returned invalid attribution.

No state establishes general narrative quality. `Report.accepted` applies the configured
policy. `Report.complete` describes execution coverage, not natural-language completeness.

## Structured truth boundary

`RequiredFact` checks state, not whether prose mentions it. `DeclaredClaimsConsistent`
checks annotated key/value declarations in the snapshot named by that surface. It does
not establish that all sentences have been annotated, that a claim accurately captures
a sentence, or that a trusted engine snapshot was actually supplied by the caller.

Both numbers and booleans are type-sensitive: `1`, `1.0`, `true` and `"1"` are distinct.
Missing facts are unknown, never silently coerced to false or the empty string.
Contexts accept flat string keys and finite JSON scalar values only. Rich domain objects
should be projected explicitly into this representation by an adapter.

For end-to-end semantic guarantees, applications need a controlled renderer or a separately
validated extraction/anchoring mechanism. Attaching LLM-generated metadata alone does not
close that gap. This alpha deliberately exposes it.

## Text normalization

Token heuristics use Unicode NFKC, casefold, then NFC. Word tokens must contain at least one
alphabetic character; counts include occurrences, diversity uses distinct words. Pattern
checks can additionally strip combining marks. Regex patterns are authored for the normalized
text (accent-free literals when accent folding is enabled), with `IGNORECASE` matching.
Pattern evidence is an excerpt from the normalized text, not an offset into the original.

Accent folding can merge words that differ in meaning. Regex matching does not understand
negation, quotation, modality, sarcasm or who said a sentence. Token-set novelty ignores order
and can be gamed with unrelated unique words. These properties are intentionally heuristics.

## Mutation audit

For each valid, changed variant with an accepted, complete baseline:

- A fault is detected only when every expected `(rule_id, code, scope)` is violated.
- An exception, unknown result or unrelated rejection is not a targeted detection.
- A valid variation is preserved only if accepted and complete.
- Identical, explicitly equivalent or unreviewed variants, and invalid baselines, are excluded
  with reasons. Excluded cases remain visible and never inflate a denominator.

Detection score = detected eligible faults / eligible faults. Preservation rate = accepted,
complete valid variations / eligible valid variations. Undefined denominators serialize as
`null`; pytest threshold assertions reject them. These are conditional diagnostic metrics,
not estimates of production accuracy. A policy that makes heuristic violations advisory can
accept an output whose violation is still correctly detected; detection and rejection differ.

The runner does not automatically decide semantic equivalence or validate the supplied label.
`Validity.VALID` requires provenance but is a declaration, not an independent adjudication.
For research, review mutation labels without seeing guard outputs and group related cases
in sampling, confidence intervals and dataset splits.
