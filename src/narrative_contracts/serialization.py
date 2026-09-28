"""Strict, allowlisted JSON configuration. No eval or dynamic code imports."""

from __future__ import annotations

import types
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from typing import Any, TypeVar, Union, get_args, get_origin, get_type_hints

from .engine import Contract
from .model import Context, Document, Policy
from .rules import (
    DeclaredClaimsConsistent,
    ForbiddenPattern,
    LexicalRestatement,
    MinimumTokens,
    NoRepeatedText,
    RequiredFact,
    SettledPremise,
    StateChanged,
)

T = TypeVar("T")
RULES: dict[str, type[Contract]] = {
    cls.__name__: cls
    for cls in (
        DeclaredClaimsConsistent,
        ForbiddenPattern,
        LexicalRestatement,
        MinimumTokens,
        NoRepeatedText,
        RequiredFact,
        SettledPremise,
        StateChanged,
    )
}


def decode(annotation: Any, value: Any) -> Any:
    origin, args = get_origin(annotation), get_args(annotation)
    if origin in (types.UnionType, Union):
        for arg in args:
            try:
                return decode(arg, value)
            except (TypeError, ValueError):
                pass
        raise TypeError(f"Value does not match {annotation}")
    if origin is tuple:
        if not isinstance(value, (list, tuple)):
            raise TypeError("Expected array")
        if len(args) == 2 and args[1] is Ellipsis:
            return tuple(decode(args[0], v) for v in value)
        if len(args) != len(value):
            raise TypeError("Incorrect tuple length")
        return tuple(decode(a, v) for a, v in zip(args, value, strict=True))
    if origin is Mapping:
        if not isinstance(value, dict):
            raise TypeError("Expected object")
        return {decode(args[0], k): decode(args[1], v) for k, v in value.items()}
    if isinstance(annotation, type) and is_dataclass(annotation):
        return from_data(annotation, value)
    if annotation is float and type(value) is int:
        return float(value)
    if type(value) is not annotation:
        raise TypeError(f"Expected {annotation}, got {type(value).__name__}")
    return value


def from_data(cls: type[T], data: Any) -> T:
    if not isinstance(data, dict):
        raise TypeError(f"Expected object for {cls.__name__}")
    field_names = {f.name for f in fields(cls)}  # type: ignore[arg-type]
    unknown = data.keys() - field_names
    if unknown:
        raise ValueError(f"Unknown {cls.__name__} fields: {sorted(unknown)}")
    hints = get_type_hints(cls)
    return cls(**{k: decode(hints[k], v) for k, v in data.items()})


def load_bundle(data: Any) -> tuple[Document, Context, tuple[Contract, ...], Policy]:
    if not isinstance(data, dict) or set(data) - {"document", "context", "contracts", "policy"}:
        raise ValueError("Expected a bundle with document, context, contracts and optional policy")
    rules = []
    if not isinstance(data.get("contracts"), list):
        raise TypeError("contracts must be an array")
    for spec in data["contracts"]:
        if not isinstance(spec, dict) or spec.get("type") not in RULES:
            raise ValueError("Unknown contract type")
        cls = RULES[spec["type"]]
        rules.append(from_data(cls, {k: v for k, v in spec.items() if k != "type"}))
    return (
        from_data(Document, data["document"]),
        from_data(Context, data["context"]),
        tuple(rules),
        from_data(Policy, data.get("policy", {})),
    )
