# Validator audit: refund-demo/after/1

Authored obligations and cases only; this is not general semantic coverage.

Library version: 0.1.0a3. Report schema: 2.
Corpus digest: `69a949c723697af129502ea6aca958053ff3bc11393f2871e7e4ca609dfa0972`.
Git provenance: not collected (audit execution does not inspect Git).

## Known gaps

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
| completion (contract): A success claim needs a matching completed receipt. | no_failures_observed | detected: 5, preserved: 2 |
| prose (challenge): The user-facing text must not contradict the evidence (scope challenge). | known_gaps | survived: 1 |
| idempotency (contract): Repeated requests must not execute twice (not tested here). | untested | untested |

## All cases

| Case | Outcome | Reason |
|---|---|---|
| wrong-customer | detected | all_expected_violations |
| wrong-order | detected | all_expected_violations |
| excessive-amount | detected | all_expected_violations |
| missing-receipt | detected | all_expected_violations |
| timeout | detected | all_expected_violations |
| accepted-not-completed | detected | all_expected_violations |
| stale-receipt | detected | all_expected_violations |
| wrong-receipt-customer | detected | all_expected_violations |
| valid-paraphrase | preserved | accepted_valid_control |
| honest-uncertainty | preserved | accepted_valid_control |
| prose-only-contradiction | survived | invalid_variant_accepted |
