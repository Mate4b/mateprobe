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

## Follow-up evidence verification

The post-a2 repository additions passed 108 tests, Ruff, strict core/plugin mypy, both
package builds, synthetic and expanded campaigns, and all eight selected source mutants.
The 384-case real-output campaign is prepared before evaluation; v1 and its integrity-only
v2 revision have identical labels and outcomes. CI replays both captured collections and
compares frozen real-mutation summary/cases byte for byte. The demo runs against the a2 API.

The PyPI workflow stages only the four original a2 release files by pinned SHA-256;
newly built development artifacts are not replacements for that release. A dry run checks
metadata and installed-wheel behavior before any publishing job. Both packages are now
published to PyPI. Downloaded wheel/sdist bytes match all four pinned release hashes.
A fresh CPython 3.12 environment installed both packages solely from PyPI: pytest automatically
discovered the plugin and its fixture/report smoke test passed; the offline demo and CLI also
passed. [Publishing runs and recovery details](pypi-publishing.md).
