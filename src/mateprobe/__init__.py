"""Deterministic contracts with explicit limits on what has been verified."""

from .bindings import check_fields
from .engine import Contract, Rule, evaluate
from .model import Claim, Context, Document, Kind, Policy, Report, Status, Surface
from .relations import AllowedTransition, CompareFields, FieldRef
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
from .version import LIBRARY_VERSION

__version__ = LIBRARY_VERSION
__all__ = [
    "AllowedTransition",
    "Claim",
    "Context",
    "CompareFields",
    "Contract",
    "DeclaredClaimsConsistent",
    "Document",
    "ForbiddenPattern",
    "FieldRef",
    "Kind",
    "LexicalRestatement",
    "MinimumTokens",
    "NoRepeatedText",
    "Policy",
    "Report",
    "RequiredFact",
    "Rule",
    "SettledPremise",
    "StateChanged",
    "Status",
    "Surface",
    "check_fields",
    "evaluate",
]
