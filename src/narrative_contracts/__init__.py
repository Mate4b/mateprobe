"""Deterministic contracts with explicit limits on what has been verified."""

from .engine import Contract, Rule, evaluate
from .model import Claim, Context, Document, Kind, Policy, Report, Status, Surface
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

__version__ = "0.1.0a1"
__all__ = [
    "Claim",
    "Context",
    "Contract",
    "DeclaredClaimsConsistent",
    "Document",
    "ForbiddenPattern",
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
    "evaluate",
]
