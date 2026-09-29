# Expanded mutation campaign

`benchmarks/expanded_mutations.py` is a second, bounded output-mutation campaign for the
alpha release. It is deliberately separate from the original synthetic benchmark and from
`benchmarks/mutate_guards.py`, which mutates source copies. The campaign uses the public
`MutationCase`/`audit()` API and writes deterministic JSON plus a short Markdown summary to
`benchmarks/expanded-results/`.

Run it from the repository root with the development interpreter:

```sh
./.venv/bin/python benchmarks/expanded_mutations.py
```

To compare two runs without overwriting the checked-in artifact directory:

```sh
one=$(mktemp -d)
two=$(mktemp -d)
./.venv/bin/python benchmarks/expanded_mutations.py --output "$one"
./.venv/bin/python benchmarks/expanded_mutations.py --output "$two"
cmp "$one/campaign.json" "$two/campaign.json"
cmp "$one/corpus.json" "$two/corpus.json"
cmp "$one/summary.json" "$two/summary.json"
cmp "$one/summary.md" "$two/summary.md"
```

The corpus is authored with seed `20260929` and contains 21 paired cases. State invariants
and text heuristics are reported independently. The current checked-in run has 5 valid
invariant faults (4 detected) and 8 valid heuristic faults (4 detected). It also has 5 valid
preservation controls (4 preserved); the negated formula control is retained as a heuristic
false positive. Exact branch-claim mismatches and typed fact changes are attributed to
invariant rules, while long lexical copies and literal forbidden phrases exercise the
heuristics.

Several cases are intentional guarantee-boundary challenges. Undeclared prose contradictions,
paraphrased forbidden phrases or premises, semantic restatements, and paraphrased history
are labelled from transparent operator intent and remain visible as survivors when the
configured rule cannot establish the claim. A missing state snapshot is explicitly excluded
because the rule reports `undetermined`, not a violated check. Unicode normalization is an
explicit equivalent exclusion, and arbitrary prose meaning is an explicit not-applicable
exclusion. `audit()` never infers these labels from its own output.

These numbers are construction checks for the configured synthetic cases. They are not
natural-output semantic-accuracy estimates, independent annotation results, or evidence of
generalization to model output.
