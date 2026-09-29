# Externally authored conformance pairs

This author-run extension uses labeled cases from the
[JSON Schema Test Suite](https://github.com/json-schema-org/JSON-Schema-Test-Suite/tree/5b0ee1613e45fcc2bddac00e07c19cd49b00d8a8).
The [protocol](../paper/external-conformance-protocol.md) fixed six keyword families
before test-file retrieval (commit d1c9d33); commit 02a8e55 froze the source snapshot,
labels, adapter, driver and MateProbe core hashes before package execution.
This is prospective ordering in the project history, not independent preregistration.

The source contains 152 tests in 28 schema groups. For each group the first valid
input becomes the baseline and every other input becomes a variant, using the
upstream validity label to determine its expected relation. One group has only
its baseline. Thus 124 pairs span 27 groups; the 28 baseline selections account for
the remaining source tests. There are no other exclusions in this capture.
The ledger retains every source test, including the group with no pair.

| Keyword family | Faults detected | Controls preserved | Pairs |
|---|---|---|---|
| minProperties | 2 | 6 | 8 |
| maxProperties | 3 | 4 | 7 |
| uniqueItems | 19 | 44 | 63 |
| contains | 10 | 4 | 14 |
| dependentRequired | 6 | 10 | 16 |
| propertyNames | 5 | 11 | 16 |
| Total | 45 | 79 | 124 |

jsonschema 4.17.3 rejects all 45 invalid variants and preserves all 79 valid
variants; all evaluated baselines pass. There are no errors, unknowns, survivors
or regressed controls. The independent assertion classifier and MateProbe agree
on all 124 outcomes. These are conformance results, not newly discovered bugs.

The adapter deliberately uses the coarse ID `schema.invalid` for any validation
error. Its raw records also retain the original package errors. No claim of
keyword-level or causal attribution is supported by this extension. This study
adds externally authored inputs and expectations; it does not measure natural
LLM output, general semantic correctness, independent execution, user effort or
adoption. The selected files are purposive and their shared baselines create
clusters. The paired variants need not be minimal or single-defect mutations.

## Reproduce

Offline replay requires the a3 study checkout and its core; jsonschema itself is
not imported during replay:

```sh
python benchmarks/external_conformance.py replay --captured benchmarks/external-conformance/evaluation --output /tmp/external-replay
```

For fresh execution, use Python 3.12 and install the exact dependencies before
running the capture command. No model or external references are requested by
these prepared cases:

```sh
python -m pip install jsonschema==4.17.3 attrs==26.1.0 pyrsistent==0.20.0
python benchmarks/external_conformance.py capture --output /tmp/external-fresh
```

Use new output directories. Preparation downloaded the six files and their MIT
license from the recorded full upstream commit, rather than following future HEAD
changes. Replay checks hashes and reconstructs pair selection from upstream labels.
Manifests detect mismatches; they are not signatures or tamper-proof attestations.

[Source and selection ledger](../benchmarks/external-conformance/prepared/ledger.json) ·
[Prepared pairs](../benchmarks/external-conformance/prepared/pairs.json) ·
[Raw package outcomes](../benchmarks/external-conformance/evaluation/observations.json) ·
[Results](../benchmarks/external-conformance/evaluation/summary.json) ·
[Source license](../benchmarks/external-conformance/prepared/upstream/LICENSE).
