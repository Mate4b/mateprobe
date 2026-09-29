# Mutation audit on real model outputs

This campaign applies authored mutations to the 32 captured responses from the user's
installed `gemma4:26b-mlx-hermes` and `qwen3.8:27b` tags. It makes no new model calls.
These are fictional public scenarios, not production LifeCard sessions. All 32 original
responses passed the configured profile, which does not certify their prose as true.

## Results

| Evidence lane | Cases | Eligible | Result |
| --- | ---: | ---: | --- |
| Exact declaration faults | 64 | 64 | 64 targeted detections |
| Lexical heuristic faults | 96 | 96 | 96 targeted detections |
| JSON/adapter schema faults | 96 | 96 | 96 structure rejections |
| Meaning-preserving controls | 64 | 48 | 48 preserved; 16 identical variants excluded |
| Prose contradictions outside configured guarantees | 64 | 64 | All 64 accepted |

Both models have the same counts in each lane. The corpus shares **eight scenario groups**;
384 derivatives are not 384 independent observations. No semantic precision/recall or model
ranking is estimated. Perfect detection on these deliberately narrow operators is not a
claim of general robustness: earlier synthetic campaigns retain survivors and regressions.

The two exact operators change credits by one or copy the other branch's declarations.
The latter changes both status and credits: 32 cases produce 64 findings. Count cases,
not individual fields or diagnostic messages, in the mutation denominator.

The heuristic operators empty the body, repeat an option label as the outcome, or insert
a literal configured phrase. Label repetition also triggers the lexical-diversity floor
in all 32 cases. Detection requires the expected restatement rule/code/scope, not just any
rejection; co-findings are retained in `violation_findings_by_family`. This is not an isolated
ablation of the restatement guard. Schema checks reject missing credit claims, boolean
credits and reordered branches before constructing a `Document`.

Whitespace and canonical Unicode NFD controls preserve the original text. Sixteen English
NFD variants are byte-identical to their bases and excluded; they are not easy successes.
Controls establish stability under those transforms, not the truth of the original prose.

The challenges append explicit wrong balances or opposite-branch status assertions to
prose, keeping the structured declarations correct. All 64 pass. No configured contract
extracts those assertions from prose. Challenges remain a separate table; their acceptance
must not be concealed, called semantic detection, or mixed into an in-scope mutation score.

## Architecture findings and changes

No in-scope rule failure was demonstrated by this campaign, so built-in rule semantics and
thresholds remain unchanged. The useful implementation changes are in evidence handling:

- The collector serializes model batches, explicitly unloads each model, and stops if the
  server does not confirm an empty residency list. Other clients require coordination.
- Replay rejects unknown or mismatched model/scenario IDs, incorrect grouping, duplicate
  records and requests that differ from the frozen configuration, including thinking,
  streaming and residency controls. Missing generations remain explicit.
- Mutation preparation records missing model/scenario attempts and excludes truncated or
  unparsable baselines. Evaluation excludes rejected/incomplete baselines and no-ops.
- The trusted JSON adapter continues to obtain branch mappings from the application.
  These mutations test claims at a fixed mapping, not correctness of arbitrary external
  wiring or an LLM's ability to choose authoritative reference snapshots.

Hashes detect accidental inconsistencies; they are not a signed provenance or adversarial
anti-tampering guarantee. Anyone who edits data and all corresponding hashes can forge a
self-consistent artifact. Published Git history supplies the comparison point.

## Reproduction

Install the current checkout's development dependencies as in the README. No Ollama or
network access is needed for evaluation:

```sh
python benchmarks/real_mutations.py evaluate \
  --prepared benchmarks/real-mutation-results/prepared --output /tmp/real-mutations-new
cmp benchmarks/real-mutation-results/evaluation/summary.json /tmp/real-mutations-new/summary.json
cmp benchmarks/real-mutation-results/evaluation/cases.json /tmp/real-mutations-new/cases.json
```

Preparation is a separate operation and never selects cases based on contract verdicts:

```sh
python benchmarks/real_mutations.py prepare \
  --input benchmarks/remote-results --output /tmp/real-mutations-prepared-new
cmp benchmarks/real-mutation-results/prepared/prepared.json /tmp/real-mutations-prepared-new/prepared.json
```

Output directories must be new. The frozen inputs, protocol, exact generator/adapter source
and their hashes are in `benchmarks/real-mutation-results/prepared`; individual baseline and
variant reports are in its sibling `evaluation`. The rule profile is pinned. Changes require
an explicitly versioned campaign, not rewriting old outcomes.

Version 1 was committed as `c7f11cf` before an integrity review. Version 2 adds complete
request-field checks and missing-attempt accounting; operators, labels, thresholds and all
outcomes are unchanged. To reproduce version 1, check out that commit in a separate worktree
and use its commands. The version change is not a second independent experiment.

See the [frozen protocol](../paper/real-mutation-protocol.md), [raw collection](https://github.com/Mate4b/narrative-contracts/blob/main/benchmarks/remote-results/README.md),
[machine-readable results](https://github.com/Mate4b/narrative-contracts/blob/main/benchmarks/real-mutation-results/evaluation/summary.json),
and [five-minute demo](quickstart.md).
