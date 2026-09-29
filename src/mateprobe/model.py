"""Small immutable JSON-domain models; no model provider or application dependency."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, TypeAlias

from .version import LIBRARY_VERSION

Scalar: TypeAlias = str | int | float | bool | None


def scalar(value: Scalar) -> Scalar:
    if type(value) not in (str, int, float, bool, type(None)):
        raise TypeError("Facts must be JSON scalars, not containers or custom objects")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Facts must be finite")
    return value


def plain(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: plain(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Mapping):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(v) for v in value]
    return value


def canonical(value: Any) -> str:
    return json.dumps(
        plain(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def same(left: Scalar, right: Scalar) -> bool:
    """Type-sensitive JSON equality: true, 1 and 1.0 are distinct facts."""
    return canonical(left) == canonical(right)


@dataclass(frozen=True)
class Claim:
    """An explicit declaration. Its presence is NOT proof of textual entailment."""

    key: str
    value: Scalar

    def __post_init__(self) -> None:
        if not self.key:
            raise ValueError("Claim key is required")
        scalar(self.value)


@dataclass(frozen=True)
class Surface:
    id: str
    text: str
    state_ref: str = "current"
    claims: tuple[Claim, ...] = ()

    def __post_init__(self) -> None:
        if not self.id or not self.state_ref:
            raise ValueError("Surface id and state_ref are required")
        if not isinstance(self.text, str):
            raise TypeError("Surface text must be a string")
        object.__setattr__(self, "claims", tuple(self.claims))


@dataclass(frozen=True)
class Document:
    surfaces: tuple[Surface, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "surfaces", tuple(self.surfaces))
        ids = [s.id for s in self.surfaces]
        if not ids or len(set(ids)) != len(ids):
            raise ValueError("Document needs nonempty, uniquely identified surfaces")

    def surface(self, surface_id: str) -> Surface:
        return next(s for s in self.surfaces if s.id == surface_id)


@dataclass(frozen=True)
class Context:
    states: Mapping[str, Mapping[str, Scalar]]
    closed_premises: tuple[str, ...] = ()
    history: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        copied = {}
        for ref, facts in self.states.items():
            if not isinstance(ref, str) or not ref:
                raise ValueError("State references must be nonempty strings")
            if any(not isinstance(k, str) or not k for k in facts):
                raise ValueError("Fact keys must be nonempty strings")
            copied[ref] = MappingProxyType({k: scalar(v) for k, v in facts.items()})
        object.__setattr__(self, "states", MappingProxyType(copied))
        object.__setattr__(self, "closed_premises", tuple(self.closed_premises))
        object.__setattr__(self, "history", tuple(self.history))


class Status(str, Enum):
    SATISFIED = "satisfied"
    VIOLATED = "violated"
    UNDETERMINED = "undetermined"
    ERROR = "error"


class Kind(str, Enum):
    INVARIANT = "invariant"
    HEURISTIC = "heuristic"


@dataclass(frozen=True)
class Check:
    rule_id: str
    version: str
    kind: Kind
    status: Status
    code: str
    scope: str
    evidence: str
    metrics: tuple[tuple[str, Scalar], ...] = ()


@dataclass(frozen=True)
class Policy:
    """Strict by default. Heuristic violations may optionally be advisory."""

    block_heuristics: bool = True
    block_undetermined: bool = True

    def blocks(self, check: Check) -> bool:
        if check.status == Status.ERROR:
            return True
        if check.status == Status.UNDETERMINED:
            return self.block_undetermined
        return check.status == Status.VIOLATED and (
            check.kind == Kind.INVARIANT or self.block_heuristics
        )


@dataclass(frozen=True)
class Report:
    checks: tuple[Check, ...]
    input_digest: str
    contracts_digest: str
    policy: Policy
    library_version: str = LIBRARY_VERSION
    schema_version: int = 1

    @property
    def accepted(self) -> bool:
        return bool(self.checks) and not any(self.policy.blocks(c) for c in self.checks)

    @property
    def complete(self) -> bool:
        return bool(self.checks) and all(
            c.status not in (Status.ERROR, Status.UNDETERMINED) for c in self.checks
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = plain(self)
        result.update(accepted=self.accepted, complete=self.complete)
        return result

    def assert_accepted(self) -> None:
        if not self.accepted:
            messages = [
                f"{c.rule_id} [{c.status.value}] {c.scope}: {c.evidence}"
                for c in self.checks
                if self.policy.blocks(c)
            ]
            raise AssertionError("MateProbe contract failure:\n" + "\n".join(messages))
