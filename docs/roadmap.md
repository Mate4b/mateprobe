# Roadmap and release gates

## Public alpha a2

- [x] Dependency-free, deterministic core; explicit exact/heuristic boundaries.
- [x] Pytest plugin, CLI, versioned reports, LifeCard adapter.
- [x] Second executable integration: trusted customer-support refund workflow.
- [x] Original synthetic benchmark plus a separate expanded campaign with valid controls,
  attributable detections, exclusions, survivors and false positives.
- [x] Frozen engineering pilot protocol; two real local model families and offline replay.
- [x] Community issue templates and evidence-based contribution process.
- [x] Technical report with limitations; independent human labels are not a release gate.
- [x] Alpha a2 GitHub release with pinned installable wheels/sdists; CI runs on Python 3.11–3.14.
  The release provenance records the verified commit and CI run.

The release verification record and PROJECT_STATUS.md identify the exact published state.
PyPI distribution is optional follow-up, not a prerequisite to install the published wheels.

## Follow-up launch milestones

- [x] Audit controlled faults and valid transformations on the 32 larger-model responses.
- [x] Report schema failures and prose-only scope challenges separately.
- [x] Harden residency handling, replay identity/configuration checks and missing-attempt accounting.
- [x] Add a five-minute offline demo and update the technical report with follow-up evidence.
- [x] Prepare PyPI Trusted Publishing of the original verified a2 artifacts.
- [x] Publish the core to PyPI and verify original hashes, clean installation, demo and CLI.
- [x] Resolve the plugin pending publisher, publish it and verify pytest discovery from PyPI.
- [x] Prepare a public announcement and counterexample request.
- [ ] Publish the announcement on the maintainer's chosen channel.

## External validation and research — future work

- [ ] Independent review and adoption outside the authoring team.
- [ ] Natural-output labels, adjudication and cluster-aware error/uncertainty analysis.
- [ ] Held-out applications and fault families, with calibration separated from evaluation.
- [ ] Calibrated LLM judges and existing assertion tools compared on the same evidence.
- [ ] Maintenance/authoring effort, production-scale costs and controlled text grounding.
- [ ] Research submission with claims proportional to the resulting evidence.

Shipping code invites scrutiny; it does not establish external validation. The labelled study
protocol remains available in `paper/protocol.md` for contributors who want to pursue it.

## Architecture follow-ups

- [ ] Stable profile schema/compatibility policy informed by adopter feedback.
- [ ] Controlled-language rendering for stronger text-to-state guarantees.
- [ ] Applicability masks and source-text evidence spans.
- [ ] Distributed pytest report aggregation.
- [ ] Typed temporal traces and separately scoped bounded reachability adapters.
