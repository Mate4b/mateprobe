# Documentation-guided agent smoke protocol v1

> Historical evidence/reference from Narrative Contracts. The current project is
> **MateProbe by Mate4B**; see the [migration guide](migration-mateprobe.md).
> Original package names, versions and recorded results below identify that earlier work.

This is a maintainer-run usability smoke test. It is not independent human
validation, a discovery/ranking study, or an estimate of agent success rates.
The task and checks below are fixed before the trial. A single agent receives
the documentation entry URL and task in a fresh context; it does not inherit
the implementation conversation.

## Task supplied to the agent

Using only the public documentation at
`https://mate4b.github.io/narrative-contracts/llms.txt` (the original, frozen trial URL) as the starting point and
the published PyPI packages, create a small pytest integration for a shipping
assistant. Use a new isolated Python environment and do not read the local
Narrative Contracts repository, its source, or the library implementation.
You may follow public documentation links and run the installed library.

The application has independently supplied snapshots:

```json
{
  "dispatched": {"shipment.status": "dispatched", "shipment.fee": 5},
  "cancelled": {"shipment.status": "cancelled", "shipment.fee": 0}
}
```

The trusted selected branch is `dispatched`. The generated JSON fields are
`status`, `fee`, and `body`. Require all three fields, strict types, and no
unexpected fields. The output may not select its snapshot. Build a callable
function that takes an output mapping plus independently supplied snapshots
and returns the contract report after schema validation. Include pytest cases
and a JSON contract report. Do not download or invoke a generation model.

Demonstrate: a valid output, a typed but incorrect fee, missing state evidence,
a boolean fee, correct structured fields with contradictory prose, and an
attempt to choose another branch via an extra field. Explain the limits and
which API version was used. Record the commands, package versions, docs URLs,
problems encountered and final tests. Do not alter the library or docs to pass.

## Fixed acceptance checks

1. Uses installed core and plugin `0.1.0a2`, with no source checkout dependency
   or imports of unreleased APIs.
2. Accepts valid `dispatched`, integer fee `5` and nonempty body; preserves a
   different valid wording with identical structured fields.
3. Rejects a schema-valid wrong fee through an attributable violated
   `CLAIM_STATE_MISMATCH`, rather than an unrelated lexical rejection.
4. Missing expected state evidence produces a blocking incomplete report.
5. Schema rejects boolean fees and model-supplied branch fields; a fully
   `cancelled` output cannot select the `cancelled` snapshot to pass.
6. Demonstrates that contradictory prose with correct declarations remains
   accepted, and explains why this is not evidence of prose truthfulness.
7. Runs pytest with the automatically discovered fixture and writes a report;
   reports commands, versions, docs used, and any failures honestly.

The maintainer re-runs the submitted tests and applies additional inputs against
the submitted function, without changing it. Retain the original attempt if it
fails. Improvements are a new trial or explicitly identified repair, not a
retroactively clean first attempt. Related checks within one task are not
independent samples.

## Evidence to retain

Save the task, agent/model identifier, public docs build revision, implementation,
tests, stdout, installed versions, reviewer checks and any observed limitations.
Do not publish machine-specific home paths or credentials. A successful trial
supports only that this agent completed this prompted integration using these
docs and versions. It does not establish unprompted recommendations, web-search
discoverability, training inclusion or adoption by other developers.
