"""Mutation audit of validators, not source-code mutation testing.

Expected defects are caller-supplied labels. The framework does not infer that a
text edit is a semantic defect. Declare validity independently of the evaluated rules.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from enum import Enum
from typing import Any

from .engine import Contract, evaluate
from .model import Context, Document, Policy, Report, Status, digest, plain


class Relation(str, Enum):
    VIOLATION = "violation"
    PRESERVE = "preserve"


class Validity(str, Enum):
    VALID = "valid"
    EQUIVALENT = "equivalent"
    UNREVIEWED = "unreviewed"


@dataclass(frozen=True)
class Sample:
    document: Document
    context: Context


@dataclass(frozen=True)
class Target:
    rule_id: str
    code: str
    scope: str

    def detected(self, report: Report) -> bool:
        return any(
            c.status == Status.VIOLATED
            and c.rule_id == self.rule_id
            and c.code == self.code
            and c.scope == self.scope
            for c in report.checks
        )


@dataclass(frozen=True)
class MutationCase:
    id: str
    family: str
    relation: Relation
    baseline: Sample
    variant: Sample
    expected: tuple[Target, ...] = ()
    validity: Validity = Validity.UNREVIEWED
    provenance: str = ""
    group: str = ""

    def __post_init__(self) -> None:
        if not self.id or not self.family:
            raise ValueError("Case id and family are required")
        if self.relation == Relation.VIOLATION and not self.expected:
            raise ValueError("Violations need explicit rule/code/scope targets")
        if self.relation == Relation.PRESERVE and self.expected:
            raise ValueError("Preservation cases must not expect violations")
        if self.validity == Validity.VALID and not self.provenance:
            raise ValueError("Known-valid labels need provenance")


@dataclass(frozen=True)
class CaseResult:
    id: str
    family: str
    group: str
    relation: Relation
    outcome: str
    reason: str
    baseline: Report
    variant: Report | None
    expected: tuple[Target, ...]


@dataclass(frozen=True)
class CampaignReport:
    cases: tuple[CaseResult, ...]
    corpus_digest: str
    schema_version: int = 1

    def summary(self) -> dict[str, Any]:
        counts = Counter(c.outcome for c in self.cases)
        eligible = [c for c in self.cases if c.outcome != "excluded"]
        faults = [c for c in eligible if c.relation == Relation.VIOLATION]
        controls = [c for c in eligible if c.relation == Relation.PRESERVE]
        killed = sum(c.outcome == "detected" for c in faults)
        preserved = sum(c.outcome == "preserved" for c in controls)
        families: dict[str, dict[str, int]] = {}
        for case in self.cases:
            count = families.setdefault(case.family, {})
            count[case.outcome] = count.get(case.outcome, 0) + 1
        return {
            "total": len(self.cases),
            "eligible": len(eligible),
            "counts": dict(counts),
            "valid_faults": len(faults),
            "detected_faults": killed,
            "detection_score": killed / len(faults) if faults else None,
            "valid_controls": len(controls),
            "preserved_controls": preserved,
            "preservation_rate": preserved / len(controls) if controls else None,
            "families": families,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "corpus_digest": self.corpus_digest,
            "summary": self.summary(),
            "cases": [
                {
                    **plain(c),
                    "baseline": c.baseline.to_dict(),
                    "variant": c.variant.to_dict() if c.variant else None,
                }
                for c in self.cases
            ],
        }

    def assert_thresholds(self, detection: float = 1.0, preservation: float = 1.0) -> None:
        if not 0 <= detection <= 1 or not 0 <= preservation <= 1:
            raise ValueError("Thresholds must be between 0 and 1")
        summary = self.summary()
        for key, threshold in (("detection_score", detection), ("preservation_rate", preservation)):
            value = summary[key]
            if value is None or value < threshold:
                raise AssertionError(
                    f"{key}={value!r}, required >= {threshold}; counts={summary['counts']}"
                )


def audit(
    cases: tuple[MutationCase, ...], contracts: tuple[Contract, ...], policy: Policy | None = None
) -> CampaignReport:
    if len({c.id for c in cases}) != len(cases):
        raise ValueError("Duplicate mutation case ids")
    rule_ids = {r.rule_id for r in contracts}
    if any(t.rule_id not in rule_ids for c in cases for t in c.expected):
        raise ValueError("Mutation target refers to an unknown rule")
    results = []
    for case in cases:
        original = evaluate(case.baseline.document, case.baseline.context, contracts, policy)
        reason = ""
        if case.validity != Validity.VALID:
            reason = f"label_{case.validity.value}"
        elif not original.accepted or not original.complete:
            reason = "baseline_not_accepted_and_complete"
        elif digest(case.baseline) == digest(case.variant):
            reason = "identical_variant"
        if reason:
            results.append(
                CaseResult(
                    case.id,
                    case.family,
                    case.group,
                    case.relation,
                    "excluded",
                    reason,
                    original,
                    None,
                    case.expected,
                )
            )
            continue
        changed = evaluate(case.variant.document, case.variant.context, contracts, policy)
        if case.relation == Relation.VIOLATION:
            outcome = "detected" if all(t.detected(changed) for t in case.expected) else "survived"
            reason = "all_expected_violations" if outcome == "detected" else "target_not_detected"
        else:
            outcome = "preserved" if changed.accepted and changed.complete else "regressed"
            reason = "accepted_and_complete" if outcome == "preserved" else "valid_variant_rejected"
        results.append(
            CaseResult(
                case.id,
                case.family,
                case.group,
                case.relation,
                outcome,
                reason,
                original,
                changed,
                case.expected,
            )
        )
    return CampaignReport(tuple(results), digest(cases))


def replace_text(sample: Sample, surface_id: str, text: str) -> Sample:
    sample.document.surface(surface_id)  # Fail on a typo instead of silently making a no-op.
    return replace(
        sample,
        document=Document(
            tuple(
                replace(s, text=text) if s.id == surface_id else s for s in sample.document.surfaces
            )
        ),
    )
