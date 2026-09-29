# Validator audit: refund-demo/before/1

Authored obligations and cases only; this is not general semantic coverage.

Library version: 0.1.0a3. Report schema: 2.
Corpus digest: `69a949c723697af129502ea6aca958053ff3bc11393f2871e7e4ca609dfa0972`.
Git provenance: not collected (audit execution does not inspect Git).

## Known gaps

- **missing-receipt** (completion): survived. Expected: completion_not_supported. Observed: accepted.
- **timeout** (completion): survived. Expected: completion_not_supported. Observed: accepted.
- **accepted-not-completed** (completion): survived. Expected: completion_not_supported. Observed: accepted.
- **stale-receipt** (completion): survived. Expected: completion_not_supported. Observed: accepted.
- **wrong-receipt-customer** (completion): survived. Expected: completion_not_supported. Observed: accepted.
- **prose-only-contradiction** (prose): survived. Expected: prose_contradiction. Observed: accepted. **Scope challenge, included in scores.**

## Incomplete evidence and execution failures

None observed.

## Untested or unevaluated obligations

- **idempotency**: untested; Repeated requests must not execute twice (not tested here)..

## Evidence by obligation

Outcomes apply only to the supplied corpus. Scope challenges remain in denominators.

| Obligation | Assessment | Case outcomes |
|---|---|---|
| customer (contract): The action concerns the authenticated customer. | faults_only_no_controls | detected: 1 |
| order (contract): The action concerns the authorized order. | faults_only_no_controls | detected: 1 |
| amount (contract): Positive integer cents do not exceed the authoritative limit. | faults_only_no_controls | detected: 1 |
| completion (contract): A success claim needs a matching completed receipt. | known_gaps | preserved: 2, survived: 5 |
| prose (challenge): The user-facing text must not contradict the evidence (scope challenge). | known_gaps | survived: 1 |
| idempotency (contract): Repeated requests must not execute twice (not tested here). | untested | untested |

## All cases

| Case | Outcome | Reason |
|---|---|---|
| wrong-customer | detected | all_expected_violations |
| wrong-order | detected | all_expected_violations |
| excessive-amount | detected | all_expected_violations |
| missing-receipt | survived | invalid_variant_accepted |
| timeout | survived | invalid_variant_accepted |
| accepted-not-completed | survived | invalid_variant_accepted |
| stale-receipt | survived | invalid_variant_accepted |
| wrong-receipt-customer | survived | invalid_variant_accepted |
| valid-paraphrase | preserved | accepted_valid_control |
| honest-uncertainty | preserved | accepted_valid_control |
| prose-only-contradiction | survived | invalid_variant_accepted |
