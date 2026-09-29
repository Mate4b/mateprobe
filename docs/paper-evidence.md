# Rebuilding manuscript evidence

The paper's result tables can be regenerated from recorded verdicts. The generator
replays the controlled, historical and external-conformance captures, freshly
executes the ordinary pytest comparison, and refuses a stored summary that differs
from the recomputed evidence. It does not rerun old third-party packages during
historical replay; fresh execution is a separate step.

From the study checkout with development dependencies installed:

```sh
python scripts/build_paper_evidence.py --output /tmp/mateprobe-paper-evidence
```

The output directory must be new. Outputs are `tables.json`, `facts.json`,
`claims.md` and a manifest. Each fact records its value, source file hash, JSON
pointer or explicit selection operation. Controlled case IDs and the per-case
comparison files connect aggregates to inputs and raw observations. This makes
numerical transcription checkable; it cannot prove that a policy, label or
interpretation is correct. The Markdown/PDF manuscript must consume these outputs
rather than maintain its own copies of table numbers.

- [Controlled and historical studies](validator-study.md)
- [Executable ordinary-pytest comparison](pytest-comparison.md)
- [Externally authored conformance pairs](external-conformance.md)

## Assistance and responsibility

OpenAI Codex assisted with implementation, authored fixtures, experiment drivers,
source discovery, manuscript drafting and revision, and figure/table preparation.
Reported counts come from retained execution records and reproducible scripts.
AI assistance is not independent validation. The named human author must review
and take responsibility for the final manuscript; automated checks do not establish
that this review has happened. Additional systems should be disclosed if used in
work incorporated into a subsequent version.
