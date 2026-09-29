# MateProbe and historical package names

**MateProbe by Mate4B** is the current project. Since `0.1.0a4`, install
`mateprobe` and optionally `pytest-mateprobe`, import `mateprobe`, and use the
`mateprobe` CLI and pytest fixture with `--mateprobe-report`.
See the [migration guide](migration-mateprobe.md) for complete commands.

The controlled comparison and historical-validator studies were recorded with
`narrative-contracts==0.1.0a3`. Their source snapshots, protocol files and reports
retain that distribution name and `narrative_contracts` imports. These are
historical identifiers, not instructions for current application integrations.

The [study reproduction guide](validator-study.md#offline-reproduction) separates
byte-for-byte a3 replay from a4 compatibility replay. No frozen corpus, observation,
label or report is renamed or regenerated to make migration checks pass.
