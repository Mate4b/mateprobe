# Working on MateProbe

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
environment with `narrative-contracts==0.1.0a3`, `pytest-narrative-contracts==0.1.0a3`,
and `pydantic==2.13.5`, then run `python scripts/check_published_docs.py`;
an editable checkout cannot verify published compatibility. See
[the agent integration guide](docs/agent-guide.md) for consumer instructions.

## Project identity

The public project and paper name is **MateProbe**, formerly Narrative Contracts.
Published a2/a3 distribution names, Python imports, CLI/pytest entry points and
repository URLs remain the existing identifiers until a separately verified
technical migration. Do not invent `import mateprobe` for those wheels or rewrite
frozen protocols, captured sources, historical results or release hashes for branding.
See docs/project-name.md.

## Version boundary

The current release is `0.1.0a3`, including independent audits and state bindings.
Verify built distributions in an isolated environment with
`python scripts/check_alpha_install.py --output /tmp/alpha-check` (install the
optional integration requirements first). Keep frozen a2 research artifacts and
the agent-adoption replay pinned to a2; do not rewrite historical evidence.
Keep the agent guide, `llms.txt`, and API reference consistent with installable artifacts.

## Public repository boundary

Every tracked file is public, even if it is excluded from the documentation site.
Keep announcement drafts, presentation scripts, conversation recaps, internal plans,
and maintainer handoff notes outside this repository. Do not stage them here.
Public usage guides, examples, contributor instructions and reproducible research
artifacts belong here. New documentation pages require an explicit entry in the
publication allowlist in `scripts/build_docs.py`; review the content before adding it.

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
