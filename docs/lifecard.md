# LifeCard migration boundary

This project was implemented independently after reviewing the Layer 4 validator and its
tests. It does not copy the LifeCard engine, catalogs, prompts, product policies or generated
content into this distribution. The generic adapter targets a compatible dictionary shape.
LifeCard itself is unchanged.

## Shadow-mode integration

1. At the existing trusted simulation boundary, retain the pre-state and the post-state of
   **each** outcome separately. Copy relevant scalar facts into `Context.states` under
   `current` and `<option-id>/<outcome-id>`.
2. Adapt the card with `lifecard_document`. Paths are JSON-like surface IDs, e.g.
   `$.options[0].outcomes[0].body_template`.
3. Construct `RequiredFact` from the planner's typed obligations. Reject unknown operators
   in the adapter; do not parse informal strings or infer authorization from prose.
4. Attach explicit claim annotations only where provenance is understood. Missing claims
   produce unknown results if claim consistency is required. Do not promote these findings
   as proof of arbitrary-text truthfulness.
5. Select contract profiles by domain and language. Log reports in shadow mode before changing
   existing publication gates. Compare new and old decisions with independent human review.
6. Promote individual contracts only after acceptable false-positive and miss rates are measured.

`StateChanged` compares an explicit domain projection of snapshots rather than checking the
names of effect operations. A zero add, saturated stat or bookkeeping-only update should not
satisfy an advancement obligation. Some scenes legitimately have no domain-state change;
the planner decides when the obligation applies.

The adapter does not build snapshots from generated effects. Executing and validating those
effects remains the trusted engine's responsibility. No part of this library permits text
or declared claims to mutate state.
