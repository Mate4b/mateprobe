"""Small, explicit checks for mapping output fields to state fields."""

from __future__ import annotations

from collections.abc import Mapping

from .model import Check, Kind, Policy, Report, Scalar, Status, digest, same, scalar


def check_fields(
    output: Mapping[str, Scalar],
    state: Mapping[str, Scalar],
    bindings: Mapping[str, str],
) -> Report:
    """Check named output fields against the state keys they represent.

    A binding is an explicit ``output_name -> state_key`` relationship.  Both
    sides must be present; absence is unknown rather than a successful empty
    assertion.  Equality is JSON-scalar type-sensitive (so ``True``, ``1``
    and ``1.0`` remain distinct).
    """

    if not isinstance(bindings, Mapping):
        raise TypeError("bindings must be a mapping")
    if not bindings:
        raise ValueError("At least one field binding is required")
    _validate_facts(output, "output")
    _validate_facts(state, "state")
    if any(not isinstance(name, str) or not name for name in bindings):
        raise ValueError("Binding output names must be nonempty strings")
    if any(not isinstance(key, str) or not key for key in bindings.values()):
        raise ValueError("Binding state keys must be nonempty strings")

    checks: list[Check] = []
    for output_key, state_key in sorted(bindings.items()):
        scope = f"binding:{output_key}->{state_key}"
        if output_key not in output or state_key not in state:
            missing = []
            if output_key not in output:
                missing.append(f"output {output_key!r}")
            if state_key not in state:
                missing.append(f"state {state_key!r}")
            checks.append(
                Check(
                    "field-bindings",
                    "1",
                    Kind.INVARIANT,
                    Status.UNDETERMINED,
                    "FIELD_UNAVAILABLE",
                    scope,
                    "Missing " + " and ".join(missing),
                )
            )
            continue
        actual, expected = output[output_key], state[state_key]
        checks.append(
            Check(
                "field-bindings",
                "1",
                Kind.INVARIANT,
                Status.SATISFIED if same(actual, expected) else Status.VIOLATED,
                "FIELD_MATCH" if same(actual, expected) else "FIELD_MISMATCH",
                scope,
                f"Output {output_key!r}={actual!r}; state {state_key!r}={expected!r}",
            )
        )

    return Report(
        tuple(checks),
        digest({"output": output, "state": state, "bindings": bindings}),
        digest({"type": "field-bindings", "version": "1", "bindings": bindings}),
        Policy(),
    )


def _validate_facts(facts: Mapping[str, Scalar], label: str) -> None:
    if not isinstance(facts, Mapping):
        raise TypeError(f"{label} must be a mapping")
    for key, value in facts.items():
        if not isinstance(key, str) or not key:
            raise ValueError(f"{label} keys must be nonempty strings")
        scalar(value)
