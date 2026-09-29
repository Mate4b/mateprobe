"""Audit an existing validator without adopting documents, claims, or contracts.

Cases and their expected defects are supplied by the caller, not inferred by the
validator under test. Samples must support deepcopy and canonical JSON encoding
(including the package's dataclass encoding). Validators should be pure: copying
inputs isolates in-memory edits, not side effects in databases or external services.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Generic, Literal, TypeVar

from .model import digest, plain
from .mutations import Relation, Validity
from .provenance import GitProvenance
from .version import LIBRARY_VERSION

T = TypeVar("T")


@dataclass(frozen=True)
class Verdict:
    """Normalize an existing validator's result; violations are stable finding IDs.

    Use a scoped ID such as ``reservation.customer@request-123`` where attribution
    needs a location. A rejected verdict without matching IDs is not a detection.
    ``complete=False`` means insufficient evidence, not a proved violation.
    """

    accepted: bool
    violations: tuple[str, ...] = ()
    complete: bool = True
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.accepted) is not bool or type(self.complete) is not bool:
            raise TypeError("Verdict flags must be bool")
        if isinstance(self.violations, str) or isinstance(self.evidence, str):
            raise TypeError("Violations and evidence must be sequences, not bare strings")
        object.__setattr__(self, "violations", tuple(self.violations))
        object.__setattr__(self, "evidence", tuple(self.evidence))
        if any(not isinstance(v, str) or not v for v in self.violations):
            raise ValueError("Violation IDs must be nonempty strings")
        if any(not isinstance(v, str) for v in self.evidence):
            raise TypeError("Evidence must contain strings")
        if len(set(self.violations)) != len(self.violations):
            raise ValueError("Duplicate violation IDs")
        if self.accepted and self.violations:
            raise ValueError("An accepted verdict cannot contain violations")


@dataclass(frozen=True)
class Obligation:
    id: str
    description: str
    scope: Literal["contract", "challenge"] = "contract"

    def __post_init__(self) -> None:
        if not self.id or not self.description:
            raise ValueError("Obligations need an id and description")
        if self.scope not in ("contract", "challenge"):
            raise ValueError("Obligation scope must be contract or challenge")


@dataclass(frozen=True)
class AuditCase(Generic[T]):
    id: str
    obligation: str
    baseline: T
    variant: T
    relation: Relation
    expected: tuple[str, ...] = ()
    validity: Validity = Validity.UNREVIEWED
    provenance: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.expected, str):
            raise TypeError("Expected IDs must be a sequence, not a bare string")
        object.__setattr__(self, "expected", tuple(self.expected))
        if not self.id or not self.obligation:
            raise ValueError("Case id and obligation are required")
        if not isinstance(self.relation, Relation) or not isinstance(self.validity, Validity):
            raise TypeError("Use Relation and Validity enums")
        if self.relation == Relation.VIOLATION and not self.expected:
            raise ValueError("Fault cases need expected violation IDs")
        if self.relation == Relation.PRESERVE and self.expected:
            raise ValueError("Preservation cases cannot expect violations")
        if any(not isinstance(v, str) or not v for v in self.expected):
            raise ValueError("Expected violation IDs must be nonempty strings")
        if len(set(self.expected)) != len(self.expected):
            raise ValueError("Duplicate expected violation IDs")
        if self.validity == Validity.VALID and not self.provenance.strip():
            raise ValueError("Reviewed labels need an independent rationale/provenance")


@dataclass(frozen=True)
class AuditResult:
    id: str
    obligation: str
    relation: Relation
    validity: Validity
    provenance: str
    expected: tuple[str, ...]
    baseline_digest: str
    variant_digest: str
    outcome: str
    reason: str
    baseline: Verdict | None = None
    variant: Verdict | None = None


@dataclass(frozen=True)
class ValidatorAuditReport:
    validator_id: str
    obligations: tuple[Obligation, ...]
    cases: tuple[AuditResult, ...]
    corpus_digest: str
    schema_version: int = 2
    library_version: str = LIBRARY_VERSION
    provenance: GitProvenance | None = None

    @staticmethod
    def _assessment(cases: list[AuditResult]) -> str:
        outcomes = {c.outcome for c in cases}
        if not cases:
            return "untested"
        if outcomes == {"excluded"}:
            return "not_evaluated"
        if outcomes & {"survived", "regressed", "unattributed_rejection"}:
            return "known_gaps"
        if outcomes & {"baseline_failed", "error", "undetermined"}:
            return "incomplete_evidence"
        if "excluded" in outcomes:
            return "partial_evidence"
        if outcomes == {"detected"}:
            return "faults_only_no_controls"
        if outcomes == {"preserved"}:
            return "controls_only_no_faults"
        return "no_failures_observed"

    @staticmethod
    def _evidence_flags(cases: list[AuditResult]) -> dict[str, bool]:
        outcomes = {c.outcome for c in cases}
        eligible = [c for c in cases if c.outcome not in {"excluded", "baseline_failed"}]
        return {
            "has_known_gaps": bool(outcomes & {"survived", "regressed", "unattributed_rejection"}),
            "has_incomplete_evidence": bool(
                outcomes & {"baseline_failed", "error", "undetermined"}
            ),
            "has_fault_tests": any(c.relation == Relation.VIOLATION for c in eligible),
            "has_controls": any(c.relation == Relation.PRESERVE for c in eligible),
            "has_exclusions": "excluded" in outcomes,
        }

    def summary(self) -> dict[str, Any]:
        counts = Counter(c.outcome for c in self.cases)
        # Variant crashes/unknowns stay in denominators: neither is a detection.
        eligible = [c for c in self.cases if c.outcome not in {"excluded", "baseline_failed"}]
        faults = [c for c in eligible if c.relation == Relation.VIOLATION]
        controls = [c for c in eligible if c.relation == Relation.PRESERVE]
        detected = sum(c.outcome == "detected" for c in faults)
        preserved = sum(c.outcome == "preserved" for c in controls)
        return {
            "total": len(self.cases),
            "counts": dict(sorted(counts.items())),
            "eligible_faults": len(faults),
            "detected_faults": detected,
            "detection_score": detected / len(faults) if faults else None,
            "eligible_controls": len(controls),
            "preserved_controls": preserved,
            "preservation_rate": preserved / len(controls) if controls else None,
            "obligations": [
                {
                    "id": obligation.id,
                    "description": obligation.description,
                    "scope": obligation.scope,
                    "assessment": self._assessment(
                        [c for c in self.cases if c.obligation == obligation.id]
                    ),
                    **self._evidence_flags(
                        [c for c in self.cases if c.obligation == obligation.id]
                    ),
                    "counts": dict(
                        sorted(
                            Counter(
                                c.outcome for c in self.cases if c.obligation == obligation.id
                            ).items()
                        )
                    ),
                    "case_ids": [c.id for c in self.cases if c.obligation == obligation.id],
                }
                for obligation in self.obligations
            ],
        }

    def to_dict(self) -> dict[str, Any]:
        return {**plain(self), "summary": self.summary()}

    def to_markdown(self) -> str:
        def cell(value: str) -> str:
            return value.replace("|", "\\|").replace("\n", " ").replace("\r", " ")

        lines = [
            f"# Validator audit: {cell(self.validator_id)}",
            "",
            "Authored obligations and cases only; this is not general semantic coverage.",
            "",
            f"Library version: {cell(self.library_version)}. Report schema: {self.schema_version}.",
            f"Corpus digest: `{self.corpus_digest}`.",
        ]
        if self.provenance is None:
            lines.append("Git provenance: not collected (audit execution does not inspect Git).")
        else:
            revision = self.provenance.commit or "unknown"
            dirty = {True: "dirty", False: "clean", None: "unknown"}[self.provenance.dirty]
            lines.append(
                f"Git provenance: {cell(self.provenance.source)}; revision `{revision}`; tree {dirty}."
            )
            if self.provenance.error:
                lines.append(f"Provenance warning: {cell(self.provenance.error)}.")
            lines.append("Repository metadata does not prove which code the callable executed.")

        obligations = {o.id: o for o in self.obligations}
        lines.extend(["", "## Known gaps", ""])
        gaps = [
            c
            for c in self.cases
            if c.outcome in {"survived", "regressed", "unattributed_rejection"}
        ]
        for case in gaps:
            challenge = (
                " **Scope challenge, included in scores.**"
                if obligations[case.obligation].scope == "challenge"
                else ""
            )
            expected = ", ".join(case.expected) or "accept valid control"
            observed = ", ".join(case.variant.violations) if case.variant else ""
            if not observed:
                observed = "accepted" if case.variant and case.variant.accepted else "rejected"
            lines.append(
                f"- **{cell(case.id)}** ({cell(case.obligation)}): {case.outcome}."
                f" Expected: {cell(expected)}. Observed: {cell(observed)}.{challenge}"
            )
        if not gaps:
            lines.append("No gaps observed in evaluated cases; this is not a completeness claim.")

        lines.extend(["", "## Incomplete evidence and execution failures", ""])
        issues = [
            c for c in self.cases if c.outcome in {"baseline_failed", "error", "undetermined"}
        ]
        for case in issues:
            lines.append(f"- **{cell(case.id)}**: {case.outcome}; {cell(case.reason)}.")
        if not issues:
            lines.append("None observed.")

        rows = self.summary()["obligations"]
        lines.extend(["", "## Untested or unevaluated obligations", ""])
        untested = [row for row in rows if row["assessment"] in {"untested", "not_evaluated"}]
        for row in untested:
            lines.append(
                f"- **{cell(row['id'])}**: {row['assessment']}; {cell(row['description'])}."
            )
        if not untested:
            lines.append("None in the declared inventory; undeclared obligations remain unknown.")

        lines.extend(
            [
                "",
                "## Evidence by obligation",
                "",
                "Outcomes apply only to the supplied corpus. Scope challenges remain in denominators.",
                "",
                "| Obligation | Assessment | Case outcomes |",
                "|---|---|---|",
            ]
        )
        for row in rows:
            counts = ", ".join(f"{key}: {value}" for key, value in row["counts"].items())
            lines.append(
                f"| {cell(row['id'])} ({row['scope']}): {cell(row['description'])} | "
                f"{row['assessment']} | {counts or 'untested'} |"
            )
        lines.extend(["", "## All cases", "", "| Case | Outcome | Reason |", "|---|---|---|"])
        for case in self.cases:
            lines.append(f"| {cell(case.id)} | {case.outcome} | {cell(case.reason)} |")
        return "\n".join(lines) + "\n"

    def assert_thresholds(self, detection: float = 1.0, preservation: float = 1.0) -> None:
        if not 0 <= detection <= 1 or not 0 <= preservation <= 1:
            raise ValueError("Thresholds must be between 0 and 1")
        summary = self.summary()
        failures = [
            f"{c.id}: {c.outcome} ({c.reason})"
            for c in self.cases
            if c.outcome in {"baseline_failed", "error"}
        ]
        for key, threshold in (("detection_score", detection), ("preservation_rate", preservation)):
            value = summary[key]
            if value is None or value < threshold:
                failures.append(f"{key}={value!r}, required >= {threshold}")
        if failures:
            details = [
                f"{c.id} [{c.obligation}]: {c.outcome}; {c.reason}"
                for c in self.cases
                if c.outcome in {"survived", "unattributed_rejection", "regressed", "undetermined"}
            ]
            raise AssertionError("Validator audit failure:\n" + "\n".join(failures + details))


def _run(validator: Callable[[T], Verdict], sample: T) -> tuple[Verdict | None, str]:
    try:
        verdict = validator(deepcopy(sample))
        if not isinstance(verdict, Verdict):
            raise TypeError("Validator must return Verdict; adapt bool/foreign results explicitly")
        return verdict, ""
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def audit_validator(
    validator: Callable[[T], Verdict],
    cases: tuple[AuditCase[T], ...],
    *,
    obligations: tuple[Obligation, ...],
    validator_id: str,
    provenance: GitProvenance | None = None,
) -> ValidatorAuditReport:
    """Run a paired campaign once per case, preserving attribution and failures.

    ``validator_id`` should identify the implementation/config version. It is caller
    metadata, not an automatically verified code fingerprint. No callbacks are called
    for unreviewed/equivalent/no-op cases. No samples are stored in the returned report.
    """
    cases, obligations = tuple(cases), tuple(obligations)
    if provenance is not None and not isinstance(provenance, GitProvenance):
        raise TypeError("provenance must be GitProvenance or None")
    if not validator_id.strip() or not cases or not obligations:
        raise ValueError("Validator id, cases and obligation inventory must be nonempty")
    if len({c.id for c in cases}) != len(cases):
        raise ValueError("Duplicate case IDs")
    ids = {o.id for o in obligations}
    if len(ids) != len(obligations):
        raise ValueError("Duplicate obligation IDs")
    if any(c.obligation not in ids for c in cases):
        raise ValueError("Case refers to an unknown obligation")
    corpus_digest = digest(cases)  # Validate reproducible input before running callbacks.
    results = []
    for case in cases:
        baseline_digest, variant_digest = digest(case.baseline), digest(case.variant)
        original = changed = None
        if case.validity != Validity.VALID:
            outcome, reason = "excluded", f"label_{case.validity.value}"
        elif baseline_digest == variant_digest:
            outcome, reason = "excluded", "identical_variant"
        else:
            original, error = _run(validator, case.baseline)
            if original is None:
                outcome, reason = "baseline_failed", f"baseline_error: {error}"
            elif not original.accepted or not original.complete:
                outcome, reason = "baseline_failed", "baseline_not_accepted_and_complete"
            else:
                changed, error = _run(validator, case.variant)
                if changed is None:
                    outcome, reason = "error", f"variant_error: {error}"
                elif not changed.complete:
                    outcome, reason = "undetermined", "variant_evidence_incomplete"
                elif case.relation == Relation.PRESERVE:
                    outcome = "preserved" if changed.accepted else "regressed"
                    reason = (
                        "accepted_valid_control" if changed.accepted else "valid_control_rejected"
                    )
                elif not changed.accepted and set(case.expected) <= set(changed.violations):
                    outcome, reason = "detected", "all_expected_violations"
                elif changed.accepted:
                    outcome, reason = "survived", "invalid_variant_accepted"
                else:
                    outcome, reason = "unattributed_rejection", "expected_violations_missing"
        results.append(
            AuditResult(
                case.id,
                case.obligation,
                case.relation,
                case.validity,
                case.provenance,
                case.expected,
                baseline_digest,
                variant_digest,
                outcome,
                reason,
                original,
                changed,
            )
        )
    return ValidatorAuditReport(
        validator_id, obligations, tuple(results), corpus_digest, provenance=provenance
    )
