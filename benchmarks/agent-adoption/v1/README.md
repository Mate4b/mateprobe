# Agent documentation smoke: v1

One fresh-context `gpt-5.6-luna` agent implemented a shipping-assistant integration
starting from the public `llms.txt` and the published PyPI packages. It was instructed
not to read the local repository or installed implementation. This was a cooperative
instruction, not an operating-system sandbox or an independent third-party study.

The task and behavioral checks were published before execution in
[`protocol.md`](protocol.md), at docs commit
`1343c410a90637a984998a13ba9d1d1cf002be72`. The agent wrote eight passing tests;
sixteen maintainer checks then passed against its unchanged implementation.
These are related checks of one task, not 24 independent agent trials.

## Evidence

- `submission/`: original consumer source (`.py.txt` to keep frozen code out of
  repository lint/collection), agent-authored tests, reports, versions, and logs.
- `reviewer_checks.py.txt`: additional behavior checks. Assertions use the returned
  dictionary and schema rejection record, rather than requiring a particular report
  object or exception interface. The behavioral criteria were unchanged.
- `docs-snapshot/`: public documents recovered by the maintainer immediately after
  the trial, before changing the docs. Consulted URLs are the agent's report.
- `manifest.json`: model identifier, revision, artifact hashes, outcomes and limitations.

The initial exit 4 is retained: pytest was invoked before a test file existed.
It is a setup mistake, not a detected library defect. The agent did not retain all
requested documentation snapshots and saved custom metadata as `build-info.json`.
The maintainer therefore recovered the actual site's build metadata and pages;
these are identified separately rather than presented as agent-captured artifacts.

The consumer's schema-error wrapper returns `complete=true` even though the core
contract engine has not run. It also returns `accepted=false`, so the rejection is
preserved. That wrapper field must not be interpreted as a completed core evaluation.
The documentation now makes this integration distinction explicit. The frozen
consumer implementation is not silently repaired.

## Replay

Use a separate Python 3.11+ environment with:

```sh
python -m pip install narrative-contracts==0.1.0a2 pytest-narrative-contracts==0.1.0a2 pydantic==2.13.5
python benchmarks/replay_agent_adoption.py --output /tmp/agent-adoption-replay
```

Run the second command from the repository with that environment's interpreter.
The output directory must be new. The replay checks artifact hashes, copies the
frozen source into the output directory and runs 8 consumer + 16 maintainer tests.
Installing dependencies needs network access; this replay makes no model calls.

This supports usability for this prompted integration. It does not measure search
ranking, unprompted recommendations, general agent success, production adoption,
independent validation or the semantic accuracy of generated prose.
