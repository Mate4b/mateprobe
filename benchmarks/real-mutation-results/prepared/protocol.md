# Mutations of captured model outputs — protocol v2

Written before this campaign is evaluated. This is an authored engineering audit, not
an independent human study, preregistration service record, or natural-output accuracy study.
The raw collection already exists and all 32 baselines passed the configured profile.
Acceptance does not establish that baseline prose is factually correct.

## Fixed evidence and inclusion

Use every record in `benchmarks/remote-results`: 16 scenarios each from the exact local
tags `gemma4:26b-mlx-hermes` and `qwen3.8:27b`. Preserve the collection manifest, raw
responses, prompts, model digests, grouping and rule configuration. Eight scenario groups
pair language and model variants; derivatives are not independent samples. No new model
calls, threshold tuning, prompt changes, repairs, human labels or LLM judges.

Freeze variant inputs, operator definitions, expected rule/code/scope targets, protocol
hash and generator source before evaluating the campaign. A separate `prepare` command
writes these artifacts; `evaluate` consumes them without selecting variants by verdict.
Store every baseline and exclusion, not only accepted or syntactically valid inputs.
Failed/unparseable baselines cannot enter a mutation denominator and remain visible.

## Fixed operator matrix (one of each per parseable base, 384 planned cases)

| Lane | Operator | Construction | Expected target |
| --- | --- | --- | --- |
| exact | claim_credits | Add one to outcome 0 declared credits; authoritative state unchanged | claims / CLAIM_STATE_MISMATCH / outcome.0 |
| exact | branch_claims | Copy outcome 1 declarations to outcome 0; keep branch IDs and app mapping | claims / CLAIM_STATE_MISMATCH / outcome.0 |
| heuristic | empty_body | Replace body with the empty string | content / LOW_LEXICAL_CONTENT / body |
| heuristic | lexical_restatement | Repeat outcome 0 label twelve times as its outcome | restatement.0 / LEXICAL_RESTATEMENT / outcome.0 |
| heuristic | literal_formula | Prefix body with `Sin duda, ` or `Without a doubt, ` | formula / FORBIDDEN_PATTERN / body |
| schema | missing_claim | Remove outcome 0 credits declaration | invalid_structure |
| schema | boolean_credits | Replace outcome 0 credits with JSON boolean true | invalid_structure |
| schema | branch_order | Reverse the options list | invalid_structure |
| control | whitespace | Wrap each prose surface with whitespace and expand internal whitespace | complete accepted variant |
| control | unicode_nfd | Apply canonical Unicode NFD to every prose surface | complete accepted variant; unchanged cases excluded |
| challenge | prose_wrong_credits | Append an explicit assertion of authoritative outcome 0 credits +100, leaving declarations correct | no semantic detector is configured |
| challenge | prose_wrong_status | Append an explicit assertion of the opposite branch status, leaving declarations correct | no semantic detector is configured |

All reference snapshots and mappings are trusted application inputs. Mutating `state_ref`
would be a different adapter/threat-model test: this JSON adapter obtains it from the
scenario, never the model. Wrong credits/status challenge assertions are authored and
provably inconsistent with supplied state; this does not label the rest of the prose.
Operator intent establishes the inserted defect, not the semantic validity of natural
baselines. Whitespace and canonical Unicode controls preserve the supplied text's meaning;
they do not certify it as good writing. Label replay dependencies/version explicitly.

## Accounting

- Exact and heuristic faults use the existing mutation audit with independent authored
  provenance, complete/accepted baseline, changed variant and exact target attribution.
  An unrelated rejection, error or undetermined result never counts as a detection.
- Schema cases have their own denominator. Only `invalid_structure` counts as detection,
  not a library error or any arbitrary rejected report. These are adapter checks.
- Controls report preserved, regressed and excluded counts. No-op variants are excluded
  and reported, not counted as easy successes.
- Challenges report pipeline status and accepted/rejected counts separately. Even a
  rejected challenge cannot be called detection of its semantic contradiction unless a
  justified semantic target exists. Challenges never dilute the in-scope mutation score.
- Keep per-model, per-family and scenario-group identifiers. Do not compute independent
  binomial confidence intervals over correlated derivatives or claim generalization.
- No judge comparison, natural precision/recall, semantic accuracy or blanket replacement
  of LLM-as-judge follows. Perfect detection on these authored operators remains narrow.

The prepared corpus is immutable after evaluation. Future fixes use a new profile and
report both old and new outcomes; do not relabel cases or delete survivors to improve scores.

## Integrity-only revision

Version 1 is preserved at Git commit `c7f11cf`. Version 2 keeps exactly the same
operators, reference data, labels and rule thresholds. It additionally verifies all
request fields (`stream`, `keep_alive`, `think` included), lists missing model/scenario
attempts against the manifest, and excludes truncated generations at preparation.
The original captured collection has none of these anomalies. Version 2 is prepared
and hashed before its evaluation; this is not a new independent experiment.
