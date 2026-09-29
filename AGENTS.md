# Working on Narrative Contracts

## Install and verify

Use Python 3.11+. From the repository root:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]' -e ./packages/pytest-narrative-contracts
pytest
ruff check .
ruff format --check .
mypy
```

For documentation builds, install `requirements-docs.txt` and run
`python scripts/build_docs.py`. For published-package examples, use a **separate**
environment with the PyPI versions and run `python scripts/check_published_docs.py`;
an editable checkout cannot verify published compatibility. See
[the agent integration guide](docs/agent-guide.md) for consumer instructions.

## Version boundary

The published packages are `0.1.0a2`. The checkout also contains unreleased APIs
(`check_fields`, relational rules, and the independent validator audit). Do not
present those as available from the published wheels. Keep the agent guide,
`llms.txt`, and published API reference consistent with actual installable artifacts.

## Engineering boundaries

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
