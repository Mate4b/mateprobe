# Roadmap and release gates

## MateProbe alpha a4

The current namespace is `mateprobe`, with optional `pytest-mateprobe` integration.
Version `0.1.0a4` renames the project under Mate4B while preserving MIT licensing,
rule behavior and historical research artifacts. See the [migration guide](migration-mateprobe.md).

## Historical public alpha a3

- [x] Audit existing validators through plain samples and normalized verdicts.
- [x] Independent evidence flags, actionable reports and optional Git provenance.
- [x] Progressive adoption and a permanent-regression pytest recipe.
- [x] Authored JSON Schema/Pydantic configuration trials with explicit limits.
- [x] Publish synchronized core/plugin a3 packages; verify artifact hashes and clean PyPI installation.

Feature expansion is paused while collecting useful integration cases. Independent
adoption and corpus relevance remain open questions, not claims established by CI.

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

The release verification records identify the exact published state.
Both a2 and a3 remain available on PyPI under their original Narrative Contracts names.

## Additional published evidence

- Controlled faults and valid transformations over 32 larger-model responses.
- Separate accounting for schema failures and prose-only scope challenges.
- Collector residency handling, replay identity/configuration checks and explicit missing attempts.
- Offline demos and published-package installation checks.

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
