# State bindings and relational contracts

Requires `mateprobe==0.1.0a4`. These APIs are not available in a2.

These optional helpers cover small, explicit relationships between structured
output and state. They do not parse prose, evaluate expressions, or introduce
a model validation dependency.

`check_fields(output, state, bindings)` accepts flat mappings of JSON scalar
values. A binding maps an output name to a state key. The result is the normal
`Report` object used by the package. Missing fields produce an
`undetermined` check, and equality is type-sensitive: `True`, `1`, and `1.0`
are different values. Unbound fields are not checked; the application decides
which fields are required. The mapping must represent the actual business
relationship: refund eligibility, approval, and completed execution are different
facts and must not be equated.

```python
from mateprobe import check_fields

report = check_fields(
    output={"reservation_confirmed": True},  # Structured output from the LLM.
    state={"booking.confirmed": False},  # Authoritative API result.
    bindings={"reservation_confirmed": "booking.confirmed"},
)
assert not report.accepted
print(report.to_dict())
```

The caller obtains the authoritative state, validates the output schema, and
decides whether to block, retry, or show a fallback. A timeout is not a confirmed
failure: omit an unknown fact rather than inventing `False`. Missing facts are
undetermined and blocked by the returned strict policy. An explicit `None` is a
known JSON null, not an automatic unknown marker. The helper never reads message
prose and cannot detect prose/field contradictions.

Applications using Pydantic can adapt an explicit flat projection, for example:

```python
bindings = {"reservation_confirmed": "booking.confirmed"}
report = check_fields(
    output_model.model_dump(mode="json", include=set(bindings)),
    trusted_state,
    bindings,
)
```

Here `output_model` is the application's validated model and `trusted_state` is
its backend projection. Nested objects need explicit flattening. There is no
native Pydantic integration or new dependency; schema validation and business
validation remain distinct. Use integer minor currency units when possible;
this helper accepts JSON scalars, not Decimal objects or implicit coercion.

Relational rules use `FieldRef(state_ref, key)` to select fields from a
`Context`. `CompareFields` supports exact typed equality (`eq`) and numeric
ordering (`le`). Ordering accepts finite integers and floats, excluding bool;
unsupported types return an error check. `AllowedTransition` checks an exact,
typed `(before, after)` pair against its finite allow-list. Missing branch or
field references are undetermined.

All behavior is version 1 and deterministic. Configure relationships as data
and use the regular engine, for example:

```python
from mateprobe.engine import evaluate
from mateprobe.model import Context, Document, Surface
from mateprobe.relations import AllowedTransition, FieldRef

document = Document((Surface("out", ""),))
context = Context({"before": {"status": "draft"}, "after": {"status": "ready"}})
rule = AllowedTransition(
    "status-transition",
    FieldRef("before", "status"),
    FieldRef("after", "status"),
    (("draft", "ready"),),
)
report = evaluate(document, context, (rule,))
```

For a proposed amount and a trusted limit:

```python
from mateprobe import CompareFields

context = Context({"action": {"cents": 5000}, "trusted": {"limit_cents": 6000}})
rule = CompareFields(
    "within-limit", FieldRef("action", "cents"), FieldRef("trusted", "limit_cents"), "le"
)
assert evaluate(document, context, (rule,)).accepted
```

The caller assigns state references and supplies trusted snapshots. These are
Python APIs; the alpha JSON CLI allowlist is unchanged and does not decode the
new relational rules. An empty transition allow-list denies all known transitions.
Checking a proposed action is not proof of execution and does not replace the
backend's authorization, concurrency, or transactional checks.
