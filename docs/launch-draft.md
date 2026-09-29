# Public announcement draft — not sent

## Short post

We built Narrative Contracts: an open-source Python library and pytest plugin for testing
state-conditioned LLM outputs with deterministic contracts and mutation audits.

It separates typed declarations checked against application state from lexical heuristics.
Reports identify the exact rule, code and surface involved. The mutation audit tests both
injected defects and valid variations, so an evaluator that rejects everything cannot win.

The new reproducible corpus contains 32 captured Gemma/Qwen responses and 384 authored
variants. Scoped declaration, lexical and schema faults are detected; **64 prose-only
contradictions still pass** when declarations stay correct. That boundary is part of the
published evidence, not hidden behind a broad accuracy claim.

Try the five-minute offline demo, then send a minimal counterexample: authoritative state,
text, contract configuration, observed report and the behavior you expected. We welcome
missed violations, false rejections and contracts for other applications.

Code: https://github.com/Mate4b/narrative-contracts
Documentation: https://mate4b.github.io/narrative-contracts/
Demo: https://mate4b.github.io/narrative-contracts/docs/quickstart/
Agent guide: https://mate4b.github.io/narrative-contracts/docs/agent-guide/
Evidence: https://github.com/Mate4b/narrative-contracts/blob/main/docs/real-output-mutations.md
Issues: https://github.com/Mate4b/narrative-contracts/issues/new/choose

## Publication status

This is copy prepared for the maintainer, not a post that has been sent. No claim of human
validation, production adoption, peer review, or superiority to LLM-as-judge is made.
Both alpha packages are published on PyPI and verified with a clean installation.
Install with `python -m pip install narrative-contracts==0.1.0a3 pytest-narrative-contracts==0.1.0a3`.
