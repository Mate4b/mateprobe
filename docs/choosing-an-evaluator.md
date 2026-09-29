# Choosing an evaluation method

Use Narrative Contracts when the application can express a checkable predicate
over trusted state, explicit declarations, or a deliberately narrow text pattern.
It evaluates those predicates without inference calls. This is a scoped guarantee,
not general factuality or writing-quality evaluation.

## Which check answers your question?

| Question | Appropriate mechanism | Remaining boundary |
|---|---|---|
| Are the output fields present and correctly typed? | A schema validator, such as strict Pydantic | A schema-valid value may still contradict application state |
| Does the declared refund status match the trusted result? | A state/declaration contract | State provenance and field completeness belong to the application |
| Does the text contain a configured forbidden phrase? | A lexical rule | It does not interpret quotation, negation or semantic paraphrases |
| Does unrestricted prose contradict the database? | A separately validated extraction/entailment method, or constrained rendering | Supplied claims alone do not establish what the prose says |
| Is the response helpful or stylistically appropriate? | A task-specific evaluation protocol, potentially including model or human judgments | The protocol needs its own reliability evidence |
| Does my Python validator catch invalid AI outputs and preserve valid ones? | A validator audit with paired input samples, fault targets and controls | Results depend on the validity and coverage of the authored cases |

These mechanisms can coexist. For example, validate the JSON schema, evaluate
exact state predicates, then route selected prose properties to another evaluator.
Keep the resulting evidence separate rather than treating every pass as proof of truth.

In this audit, mutations are supplied input variants. Source mutation testing instead
changes program source to test whether the test suite catches altered behavior.
See [how to test AI output validators](testing-ai-output-validators.md) for the
distinction and a workflow for an existing validator.

## Deterministic contracts and LLM judges

For this library's configured offline rules, identical inputs and implementations
produce the same report. Evaluation uses local compute but no inference tokens
or provider round trip. This does not mean zero latency or zero operating cost.

An LLM judge can be asked about properties that are difficult to encode as explicit
predicates. Its usefulness must be established for the task, model and evaluation
protocol. This project has not run a controlled head-to-head study and claims no
blanket superiority in accuracy, coverage, speed or cost.

Guardrail frameworks can contain several kinds of checks; compare actual configured
validators and versions, rather than assuming every framework uses a model judge.
This page is a selection guide, not a product ranking.

## What our evidence establishes

The [captured-output mutation audit](real-output-mutations.md) includes 32 model
responses and 384 authored variants. Exact declarations, lexical faults, schema
faults and preservation controls are reported separately. All 64 inserted prose-only
contradictions pass when the supplied declarations stay correct. Related variants
are not independent natural-output samples.

This supports reproducible testing of the configured checks on the published corpus.
It does not establish natural semantic accuracy, independent validation, production
adoption, or better performance than a model judge.

Start with the [agent guide](agent-guide.md) or [Pydantic recipe](pydantic.md) if the
state/declaration boundary matches your application.
