# Alpha verification record

Verified locally on 2026-09-28 with CPython 3.12.13 on macOS arm64. The exact development
package versions are in `requirements-dev.lock`.

- 66 pytest tests passed, including subprocess tests of plugin failure reporting, report export,
  audit thresholds, CLI statuses, branch isolation, Unicode handling and documented scope limits.
- Ruff lint and formatting passed; mypy strict passed for both source packages.
- Core and pytest plugin built as wheel and sdist with Hatchling.
- Both wheels installed into a separate clean virtual environment. Isolated Python imports
  resolved from `site-packages`; pytest automatically discovered the installed plugin; the
  fixture and installed CLI passed a smoke test without a source-tree import path.
- The example mutation campaign, JSON bundle and LifeCard-shaped adapter example executed.
- A separate local integration probe adapted the actual LifeCard challenger fixture into
  11 surfaces and used LifeCard's trusted engine to simulate its three branches. All three
  projected state-change contracts passed. This probe did not modify LifeCard or copy its
  proprietary fixture into the distribution.
- The 720-case synthetic benchmark was rerun into a separate directory: corpus, per-case
  campaign and summary JSON were byte-identical. Latency records are intentionally separate.
- Eight selected source-code mutants were killed by assertion failures; no source mutants
  survived or failed collection. This is a bounded regression check, not exhaustive mutation
  analysis. See `benchmarks/results/source-mutations.json` for attributed failing tests.

Python 3.11–3.14 CI is configured but the remote workflow has not run. No natural-output study,
independent annotation, model-judge comparison, public package publication or paper submission
has been performed. These are tracked explicitly in the roadmap and research protocol.
