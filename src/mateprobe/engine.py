from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, ClassVar, Protocol

from .model import Check, Context, Document, Kind, Policy, Report, Status, digest, plain

# Stable wire identifiers for rules released before the project rename. These
# strings are report metadata, not import paths; changing them changes digests.
_LEGACY_RULE_TYPES = {
    f"mateprobe.{module}.{name}": f"narrative_contracts.{module}.{name}"
    for module, names in (
        (
            "rules",
            (
                "RequiredFact",
                "DeclaredClaimsConsistent",
                "StateChanged",
                "MinimumTokens",
                "LexicalRestatement",
                "ForbiddenPattern",
                "SettledPremise",
                "NoRepeatedText",
            ),
        ),
        ("relations", ("CompareFields", "AllowedTransition")),
    )
    for name in names
}


class Contract(Protocol):
    @property
    def rule_id(self) -> str: ...

    version: ClassVar[str]
    kind: ClassVar[Kind]

    def evaluate(self, document: Document, context: Context) -> tuple[Check, ...]: ...
    def configuration(self) -> Mapping[str, Any]: ...


@dataclass(frozen=True)
class Rule:
    rule_id: str
    version: ClassVar[str] = "1"
    kind: ClassVar[Kind] = Kind.INVARIANT

    def configuration(self) -> Mapping[str, Any]:
        identity = f"{type(self).__module__}.{type(self).__qualname__}"
        return {
            "type": _LEGACY_RULE_TYPES.get(identity, identity),
            "version": self.version,
            "kind": self.kind.value,
            "parameters": plain(self),
        }

    def result(
        self,
        status: Status,
        code: str,
        scope: str,
        evidence: str,
        **metrics: str | int | float | bool | None,
    ) -> Check:
        return Check(
            self.rule_id,
            self.version,
            self.kind,
            status,
            code,
            scope,
            evidence,
            tuple(sorted(metrics.items())),
        )


def evaluate(
    document: Document,
    context: Context,
    contracts: Iterable[Contract],
    policy: Policy | None = None,
) -> Report:
    rules = tuple(contracts)
    ids = [r.rule_id for r in rules]
    if not ids or any(not i for i in ids) or len(set(ids)) != len(ids):
        raise ValueError("Contracts need nonempty unique rule ids; empty evaluation is invalid")
    configuration = [r.configuration() for r in rules]
    findings: list[Check] = []
    for rule in rules:
        try:
            checks = tuple(rule.evaluate(document, context))
            if not checks or any(
                not isinstance(c, Check)
                or not isinstance(c.status, Status)
                or c.rule_id != rule.rule_id
                or c.version != rule.version
                or c.kind != rule.kind
                for c in checks
            ):
                raise ValueError("Rule returned empty or incorrectly attributed checks")
        except Exception as exc:
            checks = (
                Check(
                    rule.rule_id,
                    rule.version,
                    rule.kind,
                    Status.ERROR,
                    "RULE_ERROR",
                    "$",
                    f"{type(exc).__name__}: {exc}",
                ),
            )
        findings.extend(checks)
    return Report(
        tuple(findings),
        digest({"document": document, "context": context}),
        digest(configuration),
        policy or Policy(),
    )
