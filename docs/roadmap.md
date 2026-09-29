# Roadmap and release gates

## Alpha engineering milestone

- [x] Dependency-free core with state, branch and lexical contracts.
- [x] Explicit satisfied / violated / undetermined / error outcomes.
- [x] Configurable acceptance policy and reproducible reports.
- [x] Mutation audit with attributable findings, positive controls and visible exclusions.
- [x] Pytest package, CLI and LifeCard adapter demonstration.
- [x] Synthetic benchmark with intentionally retained survivors and false positives.
- [x] Research draft and independent evaluation protocol.
- [ ] Publish the source repository at https://github.com/pablomate4b/narrative-contracts.
- [ ] First PyPI release (package namespace and publishing credentials).

## Research milestone — not completed by the synthetic benchmark

- [ ] Freeze contract semantics and preregister evaluation questions.
- [ ] Collect natural outputs and errors from several generator families and applications.
- [ ] Independently annotate defects and valid variations; adjudicate disagreement.
- [ ] Hold out scenarios and fault families; separate calibration from final evaluation.
- [ ] Compare against calibrated LLM judges and existing assertion tools on the same information.
- [ ] Report cluster-aware uncertainty, error analysis, maintenance effort and authoring cost.
- [ ] Recruit an external adopter and reproduce outside LifeCard.
- [ ] Reassess contribution and submit an appropriate paper with the completed evidence.

## Architecture follow-ups

- [ ] Profile schema/versioning and documented compatibility policy after adopter feedback.
- [ ] Controlled-language rendering/anchoring experiment for a stronger text-to-state guarantee.
- [ ] Applicability masks per contract, richer structured evidence and source-text span mapping.
- [ ] Distributed pytest report aggregation if users need it.
- [ ] Temporal obligations over typed event traces; bounded reachability remains an adapter concern.

Shipping the alpha is useful independently of the research milestones. No synthetic score
should be represented as a claim that arbitrary LLM output is semantically verified.
