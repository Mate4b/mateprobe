# Alpha a4 scope: audit existing validators

Version 0.1.0a4 packages the audit and state-binding APIs developed after a2.
Install `mateprobe==0.1.0a4` for these additions; a2 wheels do not include them. Frozen benchmark artifacts are not rewritten.

## Delivered scope

- Independent audit API with plain samples and a small verdict adapter.
- Caller-defined obligation inventory, attributable faults, controls, errors,
  unknowns, exclusions, and JSON/Markdown reports.
- Optional pytest entry point for external-validator audits.
- Executable before/after refund demonstration, with an intentionally retained
  prose contradiction and an explicitly untested obligation.
- Opt-in execution of LifeCard's existing full validation pipeline, with local
  fixture loading and source fingerprints; no edits to the application.
- `check_fields` for explicit output-to-state bindings without constructing claims.
- Bounded relational checks (`eq`, numeric `le`, and allowed transitions).

## Deliberate boundaries

The engine still checks supplied data and explicit obligations. It does not
discover missing API calls without trustworthy instrumentation, infer claims from
arbitrary prose, or verify arbitrary text against the state. An output schema
remains the application's responsibility. A matched field says nothing about
an unbound field or omitted prose assertion.

The refund receipt example distinguishes a proposed operation from evidence of
completion. The backend must enforce permissions and limits at execution time;
these offline checks do not solve stale state, concurrency, idempotency, or access
control. A missing receipt is not evidence that no invocation occurred.

Pydantic users can pass an explicit `model_dump` projection to `check_fields`.
There are no new decorators, no native Pydantic integration, and no dependency on
Pydantic. The simpler mapping interface is sufficient to evaluate the integration
cost before introducing another model-definition layer.

Scope exclusions: semantic judge integration, claim-span reasoning, a contract DSL,
automatic label generation, SaaS, universal coverage scores, and a project rename.

## Evidence and open questions

New campaigns are authored tests, not independent human evaluation. The local
LifeCard run demonstrates integration with pre-existing application code; it does
not establish that a previously unknown defect was discovered or that longer
restatements violate the current short-text rule. They are recorded as an explicit
broader-policy challenge.

The development question is whether another team can connect its own validator,
find a useful missed fault, and reproduce it as a regression without adopting the
whole library. The demos make this testable. External adoption and measured effort
savings remain unestablished.

See [audit guide](validator-audit.md), [state bindings](state-bindings.md), and
[LifeCard integration](lifecard-validator-audit.md). Historical pilot reports and
mutation scores remain separate and unchanged.
