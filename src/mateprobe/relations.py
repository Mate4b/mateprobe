"""Bounded relational contracts over explicit state fields."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, TypeGuard

from .engine import Rule
from .model import Check, Context, Document, Scalar, Status, same, scalar


@dataclass(frozen=True)
class FieldRef:
    state_ref: str
    key: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.state_ref, str)
            or not self.state_ref
            or not isinstance(self.key, str)
            or not self.key
        ):
            raise ValueError("FieldRef requires a state reference and key")


def _read(context: Context, ref: FieldRef) -> tuple[bool, Scalar | None]:
    facts = context.states.get(ref.state_ref)
    return (facts is not None and ref.key in facts, facts.get(ref.key) if facts else None)


@dataclass(frozen=True)
class CompareFields(Rule):
    left: FieldRef
    right: FieldRef
    operator: Literal["eq", "le"] = "eq"

    def __post_init__(self) -> None:
        if not isinstance(self.left, FieldRef) or not isinstance(self.right, FieldRef):
            raise TypeError("CompareFields requires explicit FieldRef operands")
        if self.operator not in ("eq", "le"):
            raise ValueError("CompareFields operator must be 'eq' or 'le'")

    def evaluate(self, document: Document, context: Context) -> tuple[Check, ...]:
        left_exists, left = _read(context, self.left)
        right_exists, right = _read(context, self.right)
        scope = f"compare:{self.left.state_ref}.{self.left.key}{self.operator}{self.right.state_ref}.{self.right.key}"
        if not left_exists or not right_exists:
            return (
                self.result(
                    Status.UNDETERMINED,
                    "FIELD_UNAVAILABLE",
                    scope,
                    "Both referenced fields are required",
                ),
            )
        if self.operator == "eq":
            passed = same(left, right)
        else:
            if not _ordered_number(left) or not _ordered_number(right):
                return (
                    self.result(
                        Status.ERROR,
                        "ORDERING_TYPE_ERROR",
                        scope,
                        "The 'le' operator requires finite int or float values; bool is excluded",
                    ),
                )
            passed = left <= right
        return (
            self.result(
                Status.SATISFIED if passed else Status.VIOLATED,
                "FIELDS_COMPARE" if passed else "FIELDS_MISMATCH",
                scope,
                f"Observed left={left!r}, right={right!r}, operator={self.operator!r}",
            ),
        )


@dataclass(frozen=True)
class AllowedTransition(Rule):
    before: FieldRef
    after: FieldRef
    allowed: tuple[tuple[Scalar, Scalar], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.before, FieldRef) or not isinstance(self.after, FieldRef):
            raise TypeError("AllowedTransition requires explicit FieldRef operands")
        object.__setattr__(self, "allowed", tuple(tuple(pair) for pair in self.allowed))
        for transition in self.allowed:
            if len(transition) != 2:
                raise ValueError("Each allowed transition must contain before and after values")
            scalar(transition[0])
            scalar(transition[1])

    def evaluate(self, document: Document, context: Context) -> tuple[Check, ...]:
        before_exists, before = _read(context, self.before)
        after_exists, after = _read(context, self.after)
        scope = f"transition:{self.before.state_ref}.{self.before.key}->{self.after.state_ref}.{self.after.key}"
        if not before_exists or not after_exists:
            return (
                self.result(
                    Status.UNDETERMINED,
                    "FIELD_UNAVAILABLE",
                    scope,
                    "Both transition fields are required",
                ),
            )
        passed = any(same(before, old) and same(after, new) for old, new in self.allowed)
        return (
            self.result(
                Status.SATISFIED if passed else Status.VIOLATED,
                "ALLOWED_TRANSITION" if passed else "TRANSITION_FORBIDDEN",
                scope,
                f"Observed transition {before!r}->{after!r}",
            ),
        )


def _ordered_number(value: Scalar) -> TypeGuard[int | float]:
    # Arbitrarily large Python integers are finite; float conversion can overflow.
    return type(value) is int or (type(value) is float and math.isfinite(value))
