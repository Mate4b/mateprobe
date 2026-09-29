# MateProbe: Attributable Mutation Audits for State-Aware Validators

**Technical report, a3 validator study with preserved a2 evidence — 29 September 2026.**

The project was renamed to **MateProbe by Mate4B** in `0.1.0a4`. Reported experiments
retain their original package versions, names and frozen artifacts; the rename is
not a new evaluation.

Status: public engineering report, not submitted or peer reviewed. The artifact includes synthetic author-constructed cases, a second author-implemented application integration, and a small frozen corpus of actual model generations. There are no independent human labels or LLM-judge labels. Natural-output acceptance is not semantic accuracy.

## Abstract

MateProbe by Mate4B (formerly Narrative Contracts; the study used alpha a3
as `narrative-contracts`) provides a dependency-free Python core and an optional
pytest plugin for
attributable mutation audits of existing validators and bounded state-conditioned
checks. An audit pairs accepted baselines with authored faults and valid variations,
requires the intended diagnostic findings, and preserves crashes, incomplete evidence,
false rejections and untested obligations. A new controlled study evaluates 144 pairs
from three exact policies under eight authored validator profiles. Detailed ordinary
Python assertions and the audit agree on all 1,152 classifications. A boolean-rejection
comparator counts 96 wrong-ID rejections as detections, while a fault-only view hides
24 rejected valid controls. These are constructed accounting examples, not a measured
frequency of defects or evidence of superiority over careful pytest tests. A separate
retrospective study screens ten public candidates and executes four historical package
comparisons. After disclosed environment-compatibility corrections, three fixes are
reproduced across jsonschema and Marshmallow; the fourth selected input passes before
and after, and remains a non-reproduction. Earlier a2 artifacts include 720 synthetic
pairs, an expanded mutation campaign, and frozen model outputs, with prose-grounding
failures retained. The evidence supports a reusable engineering protocol and diagnostic
artifact. It does not establish natural-output accuracy, independent adoption, lower
authoring effort, a novel general mutation algorithm, or replacement of LLM judges.

## 1. Problem and intended contribution

Consider an application where a trusted engine decides state transitions and a text generator describes them. The engine may know that an offer is closed, which branch was selected and which resources changed. A generator can still repeat a settled premise, describe another branch's outcome, omit an actual consequence or add unsupported prose.

Deterministic checks are attractive when the application already possesses the necessary evidence. Their reproducibility does not by itself establish construct validity: a length threshold can be implemented perfectly and remain a poor measure of informative content. We therefore treat the evaluator as an object requiring testing.

The original a2 artifact contributes (1) an explicit boundary between structured invariants and textual heuristics, (2) branch-scoped checks and four-valued results, and (3) an audit connecting labelled violations to individual rule/code/scope targets while also measuring preservation of valid variants. The a3 contribution additionally packages independent-validator adapters, obligation inventories and auditable outcome accounting. The controlled and historical experiments below evaluate this engineering artifact; broad effectiveness and research novelty beyond this combination remain unestablished.

## 2. Related work

IFEval operationalizes verifiable instructions using reproducible checks [1]. It establishes that programmatic evaluation of language-model outputs is an existing research approach. CheckList organizes behavioral tests around linguistic capabilities and test types, including invariance testing [2]. We adopt the need to test both expected changes and preserved behavior.

Mutation-based meta-evaluation also has close antecedents. Breaking Models to Test the Judge introduces controlled semantic defects in domain class diagrams to evaluate semantic judges [3]. When Knowledge Changes uses mutations and metamorphic relations to assess RAG under evolving corpora [4]. We do not claim to introduce mutation testing for semantic evaluators.

LLM-as-a-judge work documents both useful agreement with human preferences and systematic biases [5]. Those results motivate careful evaluator calibration, not a blanket claim that judges are ineffective. Existing tools such as Promptfoo already support deterministic assertions and custom code [6]. The controlled study below therefore compares diagnostic attribution and audit accounting with ordinary assertions; it does not establish greater detection power or lower authoring cost.

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

The core uses Python dataclasses and the standard library. The original a2 core exposes a contract protocol, eight built-in rule classes, a strict allowlisted JSON loader, a CLI, a LifeCard-shaped adapter and a mutation runner. The optional pytest package provides fixtures, threshold assertions and JSON reports. Neither package calls an LLM.

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

## 8. Independent validator audits in a3

The a3 `audit_validator` interface adapts plain application samples and a small
`Verdict` rather than requiring the library's document/claim model. Stable finding
IDs encode diagnostic targets and optional scope. A rejection for an unrelated ID
is recorded as `unattributed_rejection`; exceptions and incomplete verdicts remain
errors and unknowns. An obligation inventory reports untested items without claiming
to discover missing obligations. Field bindings and bounded relational rules support
explicit equality, numeric limits and allowed transitions; they do not establish
arbitrary-prose entailment or full state-machine reachability.

The controlled protocol was committed at `5de4a06` before executing prepared
cases/source (`97005d6`). Three policies concern receipt-supported refund completion,
shipment transitions/ownership, and reservation capacity/resource identity. Eight
baseline groups per policy receive four faults and two controls: 144 pairs in 24
groups, evaluated under eight authored validator profiles (1,152 classifications).
A separately implemented policy oracle verifies relations before validator execution.
All comparison methods consume the same recorded outcomes. The ordinary-assertion
reference has the same inputs, completeness information and expected diagnostic IDs.

| Profile | Boolean detections | Attributed detections | Preserved controls |
|---|---:|---:|---:|
| Correct | 96/96 | 96/96 | 48/48 |
| Omit first obligation | 24/96 | 24/96 | 48/48 |
| Wrong diagnostic ID | 96/96 | 0/96 | 48/48 |
| Reject valid variation | 96/96 | 96/96 | 24/48 |
| Crash on faults | 0/96 | 0/96 | 48/48 |
| Unknown on faults | 0/96 | 0/96 | 48/48 |
| Accept all | 0/96 | 0/96 | 48/48 |
| Reject all | Undefined | Undefined | Undefined |

There are zero classification disagreements between detailed assertions and the
audit. Reject-all fails all 144 baselines, leaving no eligible denominator. Removing
controls hides 24 regressions in the wording-sensitive profile. Deliberately crediting
crashes would change 0/96 to 96/96; discarding every unknown produces an empty
denominator. One inventoried obligation per policy remains untested. These ablations
illustrate information requirements, not the prevalence of poor testing practices.
The wrong-ID profile rejects actual faults; its failure is diagnostic attribution,
not proof that the application accepted unsafe output.

The detailed comparator's agreement is evidence against a claim of additional
detection power over correctly implemented pytest checks. The artifact packages
paired execution and evidence accounting. Authoring-effort savings were not measured.
There is no held-out natural corpus; values within a policy reuse few templates.
See [protocol](validator-study-protocol.md) and
[complete data and reproduction](../docs/validator-study.md).

## 9. Retrospective historical reproduction

Ten purposively selected public candidates were screened using primary issue and
release records. Four were included, with two changed pairs each: a trigger and a
valid control. Six were excluded for scope or insufficient before/after evidence.
The labels originate in documented upstream behavior, while adapters and minimal
reproducers are author-written. Two preflight label/configuration mistakes were
corrected after reading original reports and before executing historical packages;
original preparation and deviations are retained. This is not independent evaluation.

| Public issue | Final version comparison | Trigger before → after | Reproduced |
|---|---|---|---|
| jsonschema #575: enum boolean/numeric equality | 3.0.1 → 3.0.2 | Survived → detected | Yes |
| jsonschema #1018: cached boolean schemas | 4.17.1 → 4.17.3 | Error → preserved | Yes |
| Marshmallow #2891: uppercase FILE scheme | 4.2.0 → 4.2.1 | Regressed → preserved | Yes |
| Marshmallow #2936: IDN email | 4.2.3 → 4.2.4 | Preserved → preserved | No |

All final preservation controls pass before and after. A first run reproduced only
the FILE case: old jsonschema imports failed on `pkg_resources`, version 4.17.2 was
unavailable, and the selected IDN input passed both releases. An explicitly
exploratory compatibility follow-up pinned setuptools 70.3.0 and substituted 4.17.1.
A conflicting first follow-up lockfile was also retained and corrected before a
further run. Inputs and labels were never changed in response to these outcomes.
The final run reproduces three fixes in two packages; unsuccessful IDN reproduction
is not evidence against the upstream fix, only against this chosen trigger.

Exact package/dependency versions, installed-artifact hashes, raw outcomes, labels
and adapters are archived. Offline replay reclassifies those outcomes; it is not a
fresh run of old packages. Fresh execution uses isolated environments and explicit
package downloads. The historical and controlled datasets are not pooled. This
small retrospective sample demonstrates applicability to real validator defects;
it does not estimate natural LLM error detection, bug-discovery rate, usability,
or independently adopted deployments. Ordinary tests could detect these same bugs.
See the [screening protocol](historical-validator-protocol.md),
[compatibility follow-up](historical-followup-protocol.md), and
[primary links and results](../docs/validator-study.md).

The frozen studies retain their a3 package names, runner sources and report metadata.
The current MateProbe checkout provides `benchmarks/study_replay.py`, which verifies
unchanged hashes and compares reclassified results while permitting only the explicit
library-version metadata transition. CI also replays the original drivers with the
published a3 package and checks exact outputs. Neither replay is a new third-party
package execution; see [the reproduction guide](../docs/validator-study.md).

## 10. Threats to validity

**Construction bias:** the authors designed both rules and most transformations. Covered-family success is expected and cannot validate real-world semantic accuracy. Challenge labels are author judgments and have not been independently adjudicated.

**Limited diversity:** labels for three domains and two languages share few templates and the same schema. Numeric variations do not create independent semantic phenomena. The natural pilot contains small local models and authored scenarios, not production traffic. No held-out fault taxonomy or external adopter was evaluated; generation failures can dominate the observed pipeline.

**Comparator limitations:** the a2 excerpt baseline omits parts of LifeCard and has fewer capabilities. The a3 detailed-assertion reference agrees with the audit on the controlled corpus; it was implemented by the same authors, not an independently developed comparator. No result establishes superiority to a full existing tool or LLM judge. Historical failures are software-validator defects, not spontaneous LLM errors.

**Oracle gap:** declaration consistency is not textual entailment. Grounding, annotation completeness and authoritative context remain application responsibilities. A complete report is complete only for executed checks.

**Operational scope:** bounded snapshots and supplied history do not establish global reachability, liveness or future narrative quality. Regex configuration and normalization are language-specific maintenance obligations.

## 11. Optional independent study and community validation

The accompanying protocol specifies frozen research questions, corpus separation, independent annotations, judge calibration, matched-input comparisons, ablations, cluster-aware statistics and cost accounting. The highest-priority question is whether attributable synthetic mutation detection predicts recall on independently labelled natural errors while maintaining an acceptable valid-output rejection rate. This question remains unanswered. The public alpha ships with issue templates for reproducible counterexamples and contribution guidance; community publication invites scrutiny but does not itself constitute independent validation. Human review and calibrated model-judge comparisons are optional follow-up studies rather than release gates.

## References

1. Zhou et al. (2023). [Instruction-Following Evaluation for Large Language Models](https://arxiv.org/abs/2311.07911).
2. Ribeiro et al. (2020). [Beyond Accuracy: Behavioral Testing of NLP Models with CheckList](https://aclanthology.org/2020.acl-main.442/).
3. Delcourt et al. (2026). [Breaking Models to Test the Judge: A Mutation Testing Approach for Semantic Evaluators of Domain Class Diagrams](https://arxiv.org/abs/2608.14315).
4. Kim, Pasini and Tonella (2026). [When Knowledge Changes: Metamorphic Testing of RAG Systems with Mutations](https://arxiv.org/abs/2607.26843).
5. Zheng et al. (2023). [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena](https://arxiv.org/abs/2306.05685).
6. Promptfoo. [Deterministic metrics documentation](https://www.promptfoo.dev/docs/configuration/expected-outputs/deterministic/). Accessed 28 September 2026.
