# Controlled comparisons and historical reproductions

This author-run a3 study tests validator-audit accounting and reproduces public
historical defects. It does not evaluate natural-language truth, independent
adoption, user effort, or commercial demand. It uses no LLM calls or new model
weights. Historical examples are software-validator bugs, not natural LLM errors.

## Controlled comparison

The [protocol](../paper/validator-study-protocol.md) was committed before execution
(`5de4a06`); the corpus and source were frozen at `97005d6`. Three authored policies
(refund receipts, shipment transitions/ownership, and reservation capacity/resource)
produce 144 pairs in 24 shared baseline groups: 96 faults and 48 valid controls.
Each pair is evaluated under eight authored validator profiles, giving 1,152 paired
classifications. Numeric/identifier repetitions do not create independent domains.

Comparators consume identical recorded verdicts: boolean rejection, detailed
ordinary Python assertions exercised through pytest, and `audit_validator`.
The detailed comparator includes the same baseline, completeness and target checks
as the audit. It does not call the audit's classifier.

| Validator profile | Boolean detections | Attributed detections | Preserved controls | Other observed results |
|---|---:|---:|---:|---|
| Correct | 96/96 | 96/96 | 48/48 | None |
| Missing first obligation | 24/96 | 24/96 | 48/48 | 72 survivors |
| Wrong finding ID | 96/96 | 0/96 | 48/48 | 96 unattributed rejections |
| Reject valid wording | 96/96 | 96/96 | 24/48 | 24 false rejections |
| Crash on faults | 0/96 | 0/96 | 48/48 | 96 execution errors |
| Unknown on faults | 0/96 | 0/96 | 48/48 | 96 incomplete verdicts |
| Accept all | 0/96 | 0/96 | 48/48 | 96 survivors |
| Reject all | Undefined | Undefined | Undefined | All 144 baselines fail |

**Detailed assertions and the audit agree on all 1,152 classifications.** This
supports equivalent accounting on these cases, not greater detection power than
well-written pytest. A wrong diagnostic ID does not prove the rejection was unsafe;
it fails to establish the particular diagnostic obligation under test.

Ablations expose the information lost by weaker accounting: removing controls hides
24 false rejections; counting crashes as detections would falsely change 0/96 to
96/96; dropping all unknowns produces an empty denominator, not 100%. Ignoring
baselines makes reject-all appear to reject all 96 faulty variants. These examples
are constructed demonstrations of failure modes, not estimates of their prevalence.
The declared inventory also retains one untested obligation per policy. That does
not discover obligations the author failed to list.

[Stable results](../benchmarks/validator-study/evaluation/summary.json) ·
[All comparisons](../benchmarks/validator-study/evaluation/comparisons.json) ·
[Prepared corpus](../benchmarks/validator-study/prepared/corpus.json).

## Historical package execution

A purposive screening ledger contains ten public candidates; four were included
and six excluded with reasons. Before collection, upstream reports were read and
minimal inputs/relations were frozen. Initial preparation errors, environment
failures and subsequent compatibility corrections are documented in the
[historical protocol](../paper/historical-validator-protocol.md) and the
[follow-up protocol](../paper/historical-followup-protocol.md). This is retrospective
reproduction, not independent preregistration or discovery of previously unknown bugs.

Each included issue has a trigger pair and a separate changed valid-control pair.
The packages execute in isolated environments with exact versions, installed
dependency locks, downloaded artifact hashes and raw normalized outcomes retained.
Only the enum trigger is a violation; the other triggers are valid inputs which
should remain accepted. Exceptions are retained as errors, not detections.

| Upstream issue | Versions finally exercised | Trigger before → after | Valid control | Result |
|---|---|---|---|---|
| [jsonschema #575](https://github.com/python-jsonschema/jsonschema/issues/575), enum `0` vs `False` | 3.0.1 → 3.0.2 | Survived → detected | Preserved in both | Reproduced |
| [jsonschema #1018](https://github.com/python-jsonschema/jsonschema/issues/1018), cached boolean schema | 4.17.1 → 4.17.3 | Error → preserved | Preserved in both | Reproduced |
| [Marshmallow #2891](https://github.com/marshmallow-code/marshmallow/issues/2891), uppercase FILE | 4.2.0 → 4.2.1 | Regressed → preserved | Preserved in both | Reproduced |
| [Marshmallow #2936](https://github.com/marshmallow-code/marshmallow/issues/2936), IDN email | 4.2.3 → 4.2.4 | Preserved → preserved | Preserved in both | Not reproduced by selected input |

The first run reproduced only FILE: jsonschema 3.0.x could not import
`pkg_resources`, 4.17.2 was unavailable from the package index, and the chosen IDN
input already passed. An explicit follow-up pinned setuptools 70.3.0 for both old
jsonschema versions and substituted available 4.17.1 for 4.17.2. A first follow-up
lockfile conflict is also retained. The corrected follow-up reproduces three fixes
across two packages; the IDN case remains unchanged and unsuccessful. There is no
claim about the unavailable 4.17.2 artifact. Three of four purposively selected
cases is not a population success rate or evidence of three external adopters.

[Initial results](../benchmarks/historical-validator-results/evaluation/summary.json) ·
[Final compatibility results](../benchmarks/historical-validator-results/compatibility-followup-v2/evaluation/summary.json) ·
[Screening ledger](../benchmarks/historical-validator-results/prepared/inputs.json).

## Offline reproduction

Install both a3 packages, or the current checkout. From a repository checkout:

```sh
python benchmarks/validator_study.py replay --prepared benchmarks/validator-study/prepared --captured benchmarks/validator-study/evaluation --output /tmp/controlled-replay
python benchmarks/historical_validator_study.py replay --captured benchmarks/historical-validator-results/captured --output /tmp/historical-initial-replay
python benchmarks/historical_followup.py replay --captured benchmarks/historical-validator-results/compatibility-followup-v2/captured --output /tmp/historical-final-replay
```

Output directories must be new. Replay verifies hashes, reclassifies recorded
verdicts and requires no historical packages, model or network. Tests compare the
stable JSON outputs byte-for-byte. It does not independently re-execute third-party
packages. For fresh execution of the final version pairs, explicitly permit downloads:

```sh
python benchmarks/historical_followup.py collect --network --work /tmp/historical-envs --output /tmp/historical-fresh
python benchmarks/historical_followup.py replay --captured /tmp/historical-fresh --output /tmp/historical-fresh-evaluation
```

Use Python 3.12 for the recorded historical environment. Installation requires
package-index availability and uses the frozen dependency versions; captured pip
reports record the actual downloaded artifact hashes. Install commands pin versions,
not wheel hashes, so compare manifests if verifying download identity. Operating
system/build differences may matter. Failed setup is not a successful reproduction.

## Interpretation

The study adds independently originated bug reports, actual old/new package runs,
a detailed comparator with zero disagreements, and explicit component ablations.
It does not establish a new mutation algorithm, natural-output accuracy, adoption,
or reduced engineering effort. The main demonstrated benefit is a reusable protocol
and report for paired evidence; careful handwritten tests can express the same checks.
The original a2 synthetic/model evidence remains separate and unchanged.
