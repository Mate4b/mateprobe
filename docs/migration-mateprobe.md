# Migrating to MateProbe

MateProbe by Mate4B is the renamed distribution and import namespace for the
current release. Update application configuration and test code as follows:

| Before | Current |
| --- | --- |
| `narrative-contracts` | `mateprobe` |
| `pytest-narrative-contracts` | `pytest-mateprobe` |
| `narrative_contracts` | `mateprobe` |
| `pytest_narrative_contracts` | `pytest_mateprobe` |
| `narrative` pytest fixture | `mateprobe` pytest fixture |
| `--narrative-report` | `--mateprobe-report` |
| `narrative-contracts` CLI | `mateprobe` CLI |

For example, change imports such as `from narrative_contracts import ...` to
`from mateprobe import ...`, rename a test parameter from `narrative` to
`mateprobe`, and install the two current distributions with:

```sh
python -m pip install mateprobe==0.1.0a4 pytest-mateprobe==0.1.0a4
```

The a2 and a3 records, reports, research artifacts, and references describe the
versions that produced them and remain frozen. The old published distributions
also remain available; this migration does not rewrite or republish them.

Built-in rule configuration `type` identifiers retain their original
`narrative_contracts.*` strings as stable report metadata, not executable imports.
This preserves configuration digests and frozen replay comparisons. Custom rules
continue to use their own fully qualified class names.

To replay the original real-output mutation experiment against the renamed library,
run `python benchmarks/replay_renamed_mutations.py --output /tmp/mateprobe-replay`.
It verifies and executes the frozen generator and adapter bytes in a subprocess,
with historical import names bound to MateProbe only in that process. The original
source and corpus integrity checks remain active.
