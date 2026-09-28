# Working on Narrative Contracts

Keep core evaluation pure, offline and independent of LifeCard. Distinguish exact state
invariants from text heuristics in both implementation and public claims. Preserve the
structured-claim versus arbitrary-prose guarantee boundary.

Before a release, run pytest, Ruff, mypy, both package builds, the synthetic benchmark,
and the selected source-mutation audit. Do not alter benchmark labels or remove challenge
families to improve scores. Record implementation changes with rule versions when behavior
changes. Keep private application content out of the source distribution.

The research draft is a feasibility artifact, not a completed independent evaluation.
See docs/roadmap.md and paper/protocol.md for remaining evidence. Public publication needs
a known owner/namespace and explicit publication instruction.
