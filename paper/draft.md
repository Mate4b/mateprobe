# State-Conditioned Narrative Contracts: Deterministic Validation with Mutation and Invariance Audits

**Technical report, alpha artifact v0.1.0a2 with follow-up evidence — 29 September 2026.**

Status: public engineering report, not submitted or peer reviewed. The artifact includes synthetic author-constructed cases, a second independent software integration, and a small frozen corpus of actual model generations. There are no independent human labels or LLM-judge labels. Natural-output acceptance is not semantic accuracy.

## Abstract

Language-generation systems that maintain authoritative structured state can evaluate a useful subset of output obligations without another language model. We present Narrative Contracts, a dependency-free Python library that separates exact predicates over structured state and declared claims from lexical heuristics over prose. Contracts produce four-valued outcomes with branch-local scope, versioned configuration and diagnostic evidence. An accompanying mutation audit requires attributable detections and valid-variation controls, and exposes equivalent, unreviewed and baseline-invalid cases rather than counting them as successful tests. A synthetic feasibility corpus contains 720 paired cases in 48 shared scenario groups. The strict profile detects 384 of 480 authored faults and accepts 192 of 240 valid variations. Retained failures expose three boundaries: semantic restatement without lexical overlap, contradictions outside supplied claim annotations and negated phrases rejected by regex. An additional 21-case mutation campaign retains five survivors and one valid-control regression. A frozen 32-request pilot with two local model families records structural failures and contract findings without assigning semantic-accuracy labels. A follow-up 32-response corpus from larger user-installed models supports a 384-case authored mutation audit: 64 declaration faults, 96 lexical faults and 96 schema faults are detected; 48 changed controls are preserved and 16 no-ops excluded. All 64 inserted prose-only contradictions pass and are reported separately from in-scope scores. A separate customer-support workflow demonstrates trusted branch selection outside LifeCard. These artifacts illustrate behavior and limitations; they do not establish natural-output accuracy, superiority to LLM judges or broad cross-domain generalization. Independent evaluation is future work, not a prerequisite for releasing the engineering artifact.

## 1. Problem and intended contribution

Consider an application where a trusted engine decides state transitions and a text generator describes them. The engine may know that an offer is closed, which branch was selected and which resources changed. A generator can still repeat a settled premise, describe another branch's outcome, omit an actual consequence or add unsupported prose.

Deterministic checks are attractive when the application already possesses the necessary evidence. Their reproducibility does not by itself establish construct validity: a length threshold can be implemented perfectly and remain a poor measure of informative content. We therefore treat the evaluator as an object requiring testing.

The artifact contributes (1) an explicit boundary between structured invariants and textual heuristics, (2) branch-scoped checks and four-valued results, and (3) an audit connecting labelled violations to individual rule/code/scope targets while also measuring preservation of valid variants. The present contribution is an engineering artifact and experimental protocol. A claim of research novelty or broad effectiveness awaits the study below.

## 2. Related work

IFEval operationalizes verifiable instructions using reproducible checks [1]. It establishes that programmatic evaluation of language-model outputs is an existing research approach. CheckList organizes behavioral tests around linguistic capabilities and test types, including invariance testing [2]. We adopt the need to test both expected changes and preserved behavior.

Mutation-based meta-evaluation also has close antecedents. Breaking Models to Test the Judge introduces controlled semantic defects in domain class diagrams to evaluate semantic judges [3]. When Knowledge Changes uses mutations and metamorphic relations to assess RAG under evolving corpora [4]. We do not claim to introduce mutation testing for semantic evaluators.

LLM-as-a-judge work documents both useful agreement with human preferences and systematic biases [5]. Those results motivate careful evaluator calibration, not a blanket claim that judges are ineffective. Existing tools such as Promptfoo already support deterministic assertions and custom code [6]. The proposed study must therefore investigate the value of state-conditioned obligations, diagnostic attribution and audit methodology beyond ordinary assertions.

## 3. Model and semantics

Let a document D contain surfaces s = (id, text, state_ref, claims). Let S map state references to immutable flat mappings of typed JSON scalar facts. The trusted application supplies these snapshots; the library does not execute generated state updates. A context additionally contains supplied history and closed premise identifiers.

Each configured contract C_i maps (D, S, context) to a nonempty sequence of findings. A finding contains rule identifier and version, kind, status, code, scope, evidence and optional measurements. Status is one of satisfied, violated, undetermined or error. The last two distinguish absent evidence from execution failure. Acceptance is a separate policy; the default blocks both and blocks all violations. Applications may make heuristic violations advisory without removing them from reports.

For a declared claim (k, v) on a surface referencing branch b, consistency is typed equality S[b][k] = v. A missing state or key is undetermined. Another branch cannot supply evidence for this equality. Crucially, this checks the supplied declaration, not whether every assertion in arbitrary prose is correctly represented by it. Claims supplied by a generator do not close the text-grounding gap.

For a projected state-change obligation with keys K, advancement holds when at least one k in K differs between the supplied before and after snapshots. Every projected key must be present. This avoids counting bookkeeping operations or zero-valued effects as domain advancement, while leaving the planner responsible for whether advancement is required in a particular scene.

Text contracts implement token-count/diversity floors, source-token coverage combined with lexical novelty, normalized phrase patterns, context-conditioned premise recognition and normalized history repetition. These are declared heuristics. Lexical restatement has no character-length exemption, but unrelated novel words can still defeat it. Phrase matching does not reason about negation or quotation.

## 4. Auditing the evaluator

A mutation case supplies an original sample, a changed sample, a relation, a family, scenario-group identity, label validity, provenance and expected diagnostic targets. Labels are supplied independently of evaluator outputs; the framework cannot establish their semantic correctness automatically.

A fault is eligible only if its label is declared valid, the variant differs from the original and the baseline is accepted and complete. It is detected only if all expected (rule_id, code, scope) targets return violated. Rejection by an unrelated rule or a rule exception is insufficient. Equivalent, unreviewed, identical and baseline-invalid cases remain in the report with exclusion reasons.

For eligible fault set F and valid-variation set V:

- Detection score = attributable detections / |F|.
- Preservation rate = accepted and complete valid variations / |V|.

An empty denominator is undefined. A validator that rejects everything is separately evaluated as a degenerate control: it can have perfect binary recall while accepting no valid variations. Binary rejection metrics complement targeted diagnostic metrics; they are not interchangeable.

The separate source-mutation experiment changes selected evaluator implementations and asks whether pytest detects the implementation regression. That experiment assesses the test suite, whereas output mutation assesses the evaluator.

## 5. Implementation

The core uses Python dataclasses and the standard library. It exposes a contract protocol, eight built-in rule classes, a strict allowlisted JSON loader, a CLI, a LifeCard-shaped adapter and a mutation runner. The optional pytest package provides fixtures, threshold assertions and JSON reports. Neither package calls an LLM.

Reports include SHA-256 digests of canonical inputs and configured contracts, rule and package versions, and policy. They omit timestamps. Configuration digests identify declared settings, not executable source; release hashes and environment records complement them. The adapter maps each outcome to its own state reference and leaves trusted state execution in the application.

## 6. Feasibility experiment

### Construction

`benchmarks/run.py`, seed 1729, creates 48 scenario groups: three domain labels, two languages and eight numeric state variations. Each group has ten fault variants and five valid variants, yielding 480 faults and 240 controls. All cases are authored transformations. Domain labels change surface vocabulary; they do not constitute independent application deployments. Related rows share templates and state schemas.

Eight fault families exercise intended coverage: lexical spam, padded restatement, no domain delta, cross-branch claims, Unicode phrase variants, closed-premise reoffers, repeated scenes and unmet required facts. Two challenge families exceed the relevant lexical/annotation guarantees: semantic restatement using different words and free-prose contradiction with unchanged valid annotations. Four control families preserve text properties. A fifth control introduces a negated formulaic phrase and tests the heuristic's semantic false positives.

The comparison includes the strict contract profile, an explicitly simplified adaptation of the original excerpt's lexical/state predicates, and always-accept/always-reject controls. The excerpt baseline is **not the complete LifeCard pipeline**, Promptfoo, or a calibrated LLM judge. Differences in available checks account for part of the observed gap.

### Results

| Validator | TP | FN | FP | TN | Precision | Recall | Valid-variant acceptance |
|---|---:|---:|---:|---:|---:|---:|---:|
| Contracts, strict | 384 | 96 | 48 | 192 | 88.9% | 80.0% | 80.0% |
| Excerpt baseline | 96 | 384 | 48 | 192 | 66.7% | 20.0% | 80.0% |
| Always accept | 0 | 480 | 0 | 240 | Undefined | 0.0% | 100.0% |
| Always reject | 480 | 0 | 240 | 0 | 66.7% | 100.0% | 0.0% |

The targeted contract audit agrees with the strict binary counts in this construction: 384 attributable detections, 96 survivors, 192 preserved variants and 48 regressions. No cases are excluded. Every intended-coverage family is detected in all 48 repetitions. Each semantic challenge fault survives in all 48 repetitions. All 48 negated-formula controls are rejected.

The repetitions exercise data plumbing and reproduction, not 48 independent demonstrations of linguistic generalization. We therefore report descriptive proportions without a population-confidence interpretation. `benchmarks/results` contains the full corpus, per-case reports, summary and separate local latency observations. Latency includes report hashing and is a warm-process measurement, not a production SLA or comparison against model evaluation.

### Interpretation

Removing a character-count exemption and checking actual projected state changes repair specific failure mechanisms. More importantly, the deliberately retained failures show why a single mutation score is insufficient. The evaluator cannot detect free-text contradictions absent from annotations, and lexical recognizers cannot resolve general paraphrase or contextual negation. The current experiment supports these bounded observations only.

### Follow-up: mutations of captured larger-model outputs

A second capture uses the exact local tags `gemma4:26b-mlx-hermes` and `qwen3.8:27b`,
with model digests and runtime metadata archived. These are user-installed aliases, not
independently verified upstream identities. Sixteen shared authored scenarios per model
produce 32 complete, structurally valid outputs, all accepted by the unchanged profile.
Median request times were 4.38 s and 12.30 s, respectively; these include network/load
behavior and do not form a controlled model-speed comparison. Models ran serially with
explicit unloading and residency checks. Original prompts, states and outputs are retained.

The [follow-up mutation protocol](real-mutation-protocol.md) fixes 12 operators per baseline
before variant evaluation. The existing audit supplies rule/code/scope attribution for
contract faults; schema failures and prose scope challenges have separate accounting:

| Lane | Eligible | Outcome |
| --- | ---: | --- |
| Typed declarations | 64 | 64 attributable detections |
| Lexical heuristics | 96 | 96 attributable detections |
| Adapter/schema | 96 | 96 structure rejections |
| Valid controls | 48 | 48 preserved; 16 no-op variants separately excluded |
| Prose-only contradiction challenges | 64 | 64 accepted; no semantic detection claim |

Branch-claim swapping is a compound field mutation. Lexical restatement also activates the
content floor in 32 cases; reports retain both findings and require the declared target for
a detection. These are controlled faults authored on real-output baselines, not spontaneous
errors independently labelled in natural text. Baseline acceptance is not a factuality label.

All derivatives share eight scenario groups; no independent-binomial intervals are inferred.
The 100% in-scope figures characterize narrow configured operators, not general semantic
sensitivity, and do not supersede survivors in the earlier synthetic campaigns. The 64
accepted prose contradictions demonstrate that annotation consistency does not establish
prose entailment. A versioned integrity revision additionally verifies complete request
configuration and accounts for missing baseline attempts; labels and outcomes are unchanged.
See [reproduction and limitations](../docs/real-output-mutations.md).

## 7. Additional a2 evidence

### Expanded output-mutation campaign

A separate 21-case campaign uses new operator-authored fault/control pairs. Of 13 eligible
faults, eight have attributable detections and five survive; four of five valid controls are
preserved. Three cases are explicitly excluded as equivalent or unreviewed/not applicable.
The retained valid-control regression involves a negated formula. Survivors include
undeclared contradictions and semantic/paraphrase challenges beyond literal recognizers.
These proportions are descriptive results for the authored corpus, not natural error rates.
Full inputs, diagnostic targets and outcomes are in `benchmarks/expanded-results`.

### Independent customer-support integration

`examples/support_workflow.py` implements a trusted refund-policy transition from an order
snapshot, distinct from LifeCard. A custom exact `BranchSelection` rule prevents a reply
from selecting a convenient but unauthorized state reference. Built-in contracts check
declarations and domain changes; lexical checks remain heuristics. Tests include eligibility
boundaries, wrong-branch claims, cross-branch masking and legitimate paraphrases. An unrelated
sentence with correct declarations is deliberately accepted to expose the text-grounding gap.
The built-in-only JSON demonstration is explicitly weaker than the Python custom-rule version.
This is a second implemented domain, not an independently deployed or user-validated application.

### Frozen real-model pilot

Before generation, the collector froze `paper/release-protocol.md`, prompts, rule configuration
and sixteen authored scenarios. Support and interactive-fiction workloads each have English
and Spanish variants at four numeric settings. Languages/models share eight scenario families.
Two local quantized model families received one request each per scenario, without retries,
repairs, verdict-based selection or prompt tuning after collection. Ollama JSON mode was used;
model digests, templates, sampling settings, requests, raw responses and timings are published.
The exact collector source is archived; local weights-file paths are redacted from metadata.

| Model tag | Requests | Structurally valid | Declaration profile accepted | Strict profile accepted |
|---|---:|---:|---:|---:|
| Qwen3 1.7b | 16 | 16 | 16 | 0 |
| Gemma3 1b | 16 | 0 | Not evaluated | Not evaluated |

All 32 requests returned responses; none are missing. Gemma3's responses failed the requested
envelope rather than being silently dropped. Qwen3's two outcome bodies per response triggered
32 lexical-content findings; eight restatement findings also occurred. Its declaration-only
profile passed all 16 envelopes. Heuristic-only and simple character-length profiles accepted
none. These counts expose structure and declared-property behavior, not a semantic-quality
ranking. For example, one Qwen response supplies the symbolic string `refund_pending` as the
outcome body: it is structurally a string but does not satisfy the lexical floor.

Generation median wall times were approximately 3.23 seconds for Qwen3 and 2.87 seconds for
Gemma3 on the collection host, with load/cache effects included. The models produced 2,839 and
2,982 output tokens respectively. Local provider API fees were zero; electricity, hardware and
maintenance costs were not measured. Raw timing data and separate replay measurements are
published. No production latency guarantee or judge-cost comparison is inferred.

No human or model-judge labels were collected. Therefore natural-output semantic precision,
recall and false-positive/negative rates are unidentified. Replaying the frozen outputs
reproduces deterministic reports; regenerating outputs is not promised to be byte-identical
across runtime versions and hardware. The evaluation was replayed under a2 package metadata,
with unchanged rule semantics. Source-mutation checks still kill all eight selected mutants.

## 8. Threats to validity

**Construction bias:** the authors designed both rules and most transformations. Covered-family success is expected and cannot validate real-world semantic accuracy. Challenge labels are author judgments and have not been independently adjudicated.

**Limited diversity:** labels for three domains and two languages share few templates and the same schema. Numeric variations do not create independent semantic phenomena. The natural pilot contains small local models and authored scenarios, not production traffic. No held-out fault taxonomy or external adopter was evaluated; generation failures can dominate the observed pipeline.

**Comparator limitations:** the excerpt baseline omits parts of LifeCard and has fewer capabilities. No result here establishes superiority to a full existing tool or LLM judge. A future comparison must give competitors equivalent state, history and obligations.

**Oracle gap:** declaration consistency is not textual entailment. Grounding, annotation completeness and authoritative context remain application responsibilities. A complete report is complete only for executed checks.

**Operational scope:** bounded snapshots and supplied history do not establish global reachability, liveness or future narrative quality. Regex configuration and normalization are language-specific maintenance obligations.

## 9. Optional independent study and community validation

The accompanying protocol specifies frozen research questions, corpus separation, independent annotations, judge calibration, matched-input comparisons, ablations, cluster-aware statistics and cost accounting. The highest-priority question is whether attributable synthetic mutation detection predicts recall on independently labelled natural errors while maintaining an acceptable valid-output rejection rate. This question remains unanswered. The public alpha ships with issue templates for reproducible counterexamples and contribution guidance; community publication invites scrutiny but does not itself constitute independent validation. Human review and calibrated model-judge comparisons are optional follow-up studies rather than release gates.

## References

1. Zhou et al. (2023). [Instruction-Following Evaluation for Large Language Models](https://arxiv.org/abs/2311.07911).
2. Ribeiro et al. (2020). [Beyond Accuracy: Behavioral Testing of NLP Models with CheckList](https://aclanthology.org/2020.acl-main.442/).
3. Delcourt et al. (2026). [Breaking Models to Test the Judge: A Mutation Testing Approach for Semantic Evaluators of Domain Class Diagrams](https://arxiv.org/abs/2608.14315).
4. Kim, Pasini and Tonella (2026). [When Knowledge Changes: Metamorphic Testing of RAG Systems with Mutations](https://arxiv.org/abs/2607.26843).
5. Zheng et al. (2023). [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena](https://arxiv.org/abs/2306.05685).
6. Promptfoo. [Deterministic metrics documentation](https://www.promptfoo.dev/docs/configuration/expected-outputs/deterministic/). Accessed 28 September 2026.
