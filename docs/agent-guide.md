# Integrate Narrative Contracts in an agent project

This guide targets **published alpha 0.1.0a3**, Python 3.11+. Use it when an
application has authoritative state and needs to test explicit declarations in
generated outputs against that state. The check itself makes no model or network calls.

Already have a validator? Start with [testing AI output validators](testing-ai-output-validators.md)
and the [one-file audit](first-audit.md). `audit_validator` accepts a sample-only
adapter and caller-authored baseline/variant pairs; you do not need to migrate to
the `Document`/`Claim` representation used in the state-check example below.

## Install the published API

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install narrative-contracts==0.1.0a3 pytest-narrative-contracts==0.1.0a3
```

The second package supplies pytest and the automatically discovered `narrative`
fixture. Do not also load it with `-p`. Pin the alpha versions rather than assuming
an unqualified pip install selects a prerelease. See [API reference](api-a3.md).

## Choose the source of authority

1. Obtain state from trusted application code, a database projection, or a receipt.
2. Validate the output schema and required fields. The [Pydantic recipe](pydantic.md)
   illustrates this step; Pydantic is optional and is not a core dependency.
3. Map an explicit allowlist of output fields to claims. Preserve JSON scalar types.
4. Choose `state_ref` in trusted code. Never let the generated output pick whichever
   snapshot makes its own claims pass. Do not populate expected state from the output.
5. Evaluate the configured rules, inspect `accepted` and `complete`, and handle rejection
   in the application. Evaluation does not execute actions or enforce backend permissions.

`RequiredFact` only checks state. `DeclaredClaimsConsistent` checks supplied claims;
it does not ensure that every required output field was declared or that prose agrees.

## A complete pytest example

Save as `test_reply.py`. This includes both a detected state mismatch and the
prose-only failure that remains outside the guarantee.

```python
import pytest

from narrative_contracts import (
    Claim,
    Context,
    DeclaredClaimsConsistent,
    Document,
    Surface,
    evaluate,
)


def test_reply_contract(narrative):
    # This snapshot is provided by the application, independently of the output.
    context = Context({"current": {"ticket.status": "resolved"}})
    rules = (DeclaredClaimsConsistent("ticket-claims", ("reply",)),)

    def reply(status, text):
        return Document(
            (
                Surface(
                    "reply",
                    text,
                    state_ref="current",
                    claims=(Claim("ticket.status", status),),
                ),
            )
        )

    accepted = narrative.check(reply("resolved", "Your ticket is resolved."), context, rules)
    assert accepted.accepted and accepted.complete

    wrong = reply("open", "Your ticket remains open.")
    rejected = evaluate(wrong, context, rules)
    assert rejected.complete and not rejected.accepted
    assert any(
        check.rule_id == "ticket-claims"
        and check.code == "CLAIM_STATE_MISMATCH"
        and check.status.value == "violated"
        for check in rejected.checks
    )
    # The fixture records the report and raises on rejection.
    with pytest.raises(AssertionError):
        narrative.check(wrong, context, rules)

    # Correct declaration, contradictory prose: deliberately still accepted.
    prose_gap = narrative.check(
        reply("resolved", "Your ticket remains open."),
        context,
        rules,
    )
    assert prose_gap.accepted and prose_gap.complete
```

```sh
python -m pytest -q test_reply.py --narrative-report=contract-results.json
```

Expected: one passing test with three recorded evaluations. The prose challenge
passes its test because the test explicitly asserts this documented limitation.
Use a serial pytest run; distributed report merging is not supported.

## Diagnose a result

| Result | Meaning | Application response |
|---|---|---|
| `satisfied` | The configured predicate holds | Continue only if the full report meets policy |
| `violated` | The configured predicate fails | Inspect rule, code, scope, and evidence |
| `undetermined` | Evidence or support is missing | Supply the missing information; do not call it success |
| `error` | Rule execution failed | Fix the rule/integration; do not count it as fault detection |

Default policy blocks violations, unknowns and errors. Heuristics can be advisory
with `Policy(block_heuristics=False)`. `complete` only means no unknown/error result;
it does not mean every sentence or required business obligation was checked.

If schema validation fails before evaluation, report that stage separately
(for example, `schema_valid=False`, `evaluation_ran=False`, `accepted=False`).
Do not set an engine-style `complete=True` when no contract report was produced.

## Audit the checks

Use [the runnable mutation example](../examples/mutation_audit.py) and
[mutation semantics](contracts.md#mutation-audit). Include accepted baselines,
attributable faulty variants, valid controls, and label provenance. Report detection
and preservation separately, with exclusions and missed faults visible.

## API version

`check_fields`, `CompareFields`, `AllowedTransition`, and the independent
validator-audit API are included in **0.1.0a3**. Older a2 wheels do not provide them.
See [the a3 API index](api-a3.md) and [adoption levels](adoption-levels.md). Pin the
package version rather than silently switching a consumer to `main`.

For free-form factual correctness or writing quality, this library alone is
insufficient. See [choosing an evaluator](choosing-an-evaluator.md).
