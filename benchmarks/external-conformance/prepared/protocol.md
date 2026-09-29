# External conformance pairs: protocol v1

This is a prospective, author-run extension of the MateProbe study. It is not an
independent preregistration, a human evaluation, natural LLM-output evaluation,
or a demonstration that MateProbe discovers more defects than detailed pytest.
The protocol is committed before fetching test-file contents. The corpus, source
revision, adapter and driver are committed again before validator execution.

## Selection fixed before observation

Source: https://github.com/json-schema-org/JSON-Schema-Test-Suite, the commit at
its default branch HEAD when preparation first runs. Record its full commit ID.
Use every group in these six `tests/draft2020-12/` files:
`minProperties.json`, `maxProperties.json`, `uniqueItems.json`, `contains.json`,
`dependentRequired.json`, and `propertyNames.json`. These keyword families were
not the enum, boolean-reference, URL or email triggers in the historical study.
This is a purposive subset, not a random or comprehensive sample of JSON Schema.
Do not add or replace files based on execution results.

For each group, use the first upstream test labeled valid as baseline. Pair it
with every other test in that group. A valid target is PRESERVE; an invalid target
is VIOLATION. The source's `valid` boolean supplies the expectation; never infer
labels from a validator response. Retain a ledger of every source test, including
the selected baseline and excluded targets. Exclude a group lacking a valid
baseline or requiring an external reference (a `$ref` or `$dynamicRef` not starting
with `#`). Exclude canonical-JSON-identical target inputs. Identify groups/tests by
source filename and zero-based indexes, preserving descriptions and source labels.
A shared baseline is not an independent observation for each pair.

## Implementation and execution

Use the already evaluated MateProbe core distributed as narrative-contracts a3,
and jsonschema 4.17.3 (Draft202012Validator) with attrs 26.1.0 and pyrsistent 0.20.0.
Use Python 3.12. Record installed versions, platform, source hashes and raw verdicts.
Perform no remote reference retrieval and no LLM calls. The adapter validates
`data` against the group's unchanged `schema`, preserving package errors in the
raw record. Its diagnostic ID is deliberately coarse: `schema.invalid` for any
ValidationError. This study tests conformance pairs, not keyword-specific or
causal attribution. Do not claim that the coarse ID establishes the defect cause.
Unexpected exceptions are recorded separately and receive no detection credit.

Execute each prepared pair through a capture wrapper, preserving baseline and
variant responses. Feed the same captured verdicts to the existing independent
assertion comparator and the public audit API. Compare all case outcomes. Include
variant exceptions/unknowns in eligible denominators; retain baseline failures
and exclusions. An empty denominator is undefined.

## Reports, stopping rule and interpretation

Execute all eligible pairs once with the frozen adapter. Report total upstream
groups/tests, exclusions by reason, pairs by family and relation, baseline failures,
errors, detections, survivors, preserved/regressed controls and comparator
agreements. Publish the selected source files and their license, the full ledger,
prepared pairs, raw verdicts, manifests and replay results. Verify upstream source
integrity and refuse modified captures in replay. Keep this dataset separate from
the earlier controlled and historical studies. No significance test or population
confidence interval is justified by these purposive, clustered fixtures.

Do not change labels, the selected files, adapter or implementation to improve the
observed score. If an infrastructure repair is necessary, archive the failed
attempt, document the repair and freeze a new revision before rerunning. Unexpected
validator failures remain findings, not a reason to remove a case. Successful
results establish behavior on these externally authored conformance tests; they do
not establish general correctness, production adoption or independent validation.
