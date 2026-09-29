# Alpha a2 verification record

Verified locally on 2026-09-29 with CPython 3.12.13 on macOS arm64.
The development tool versions are recorded in `requirements-dev.lock`.

- 91 pytest tests pass, including the second-domain workflow, collector/replay boundaries,
  branch isolation, malformed/truncated outputs, mutation attribution and valid controls.
- Ruff lint/format pass; mypy strict passes for the two source packages.
- Core and plugin build as wheel/sdist. An isolated environment installs both wheels,
  imports from site-packages and auto-discovers the pytest plugin; fixture, report and CLI pass.
- The source-mutation runner detects all eight hand-selected mutants through failing tests;
  collection failures are excluded, never counted as kills. The runner now exposes benchmark
  modules on the test path while preserving the mutated package's precedence.
- The 720-case original synthetic corpus retains its authored labels and scores. Reports
  were regenerated with a2 package metadata, without changes to built-in rule semantics.
- The separate 21-case expanded campaign retains eight detections, five survivors, four
  preserved controls, one control regression and three explicit exclusions.
- The real-model pilot retains all 32 requested outputs, 16 from each family. Exact model
  digests/configuration are pinned. There are no semantic gold labels or model-judge labels.
- Captured-model `reports.json` and `summary.json` reproduce byte-for-byte through offline
  replay. Timing is excluded from this identity claim and stored separately.
- CI checks Python 3.11–3.14, package builds, expanded mutations and offline natural replay.
  See the exact remote run linked from the release provenance/PROJECT_STATUS.md.

`benchmarks/natural-results/collector-source.py.txt` retains the collection-time script.
The release collector additionally omits local model-file paths and respects installed
package import precedence; prompts and rule thresholds were not tuned on observed outputs.

No production traffic, independent human annotation, external adoption or LLM-judge quality
comparison has been evaluated. This is an installable engineering artifact with bounded
reproducible evidence, not a validated general semantic evaluator or accepted research paper.
