from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeVar

import pytest

from narrative_contracts import Context, Contract, Document, Policy, Report, evaluate
from narrative_contracts.mutations import CampaignReport, MutationCase, audit
from narrative_contracts.validator_audit import (
    AuditCase,
    Obligation,
    ValidatorAuditReport,
    Verdict,
    audit_validator,
)

_REPORTS: pytest.StashKey[list[dict[str, Any]]] = pytest.StashKey()
T = TypeVar("T")


@dataclass
class NarrativeAssertions:
    records: list[dict[str, Any]] = field(default_factory=list)
    node_id: str = ""

    def check(
        self,
        document: Document,
        context: Context,
        contracts: tuple[Contract, ...],
        policy: Policy | None = None,
    ) -> Report:
        report = evaluate(document, context, contracts, policy)
        self.records.append({"test": self.node_id, "type": "evaluation", **report.to_dict()})
        report.assert_accepted()
        return report

    def audit(
        self,
        cases: tuple[MutationCase, ...],
        contracts: tuple[Contract, ...],
        *,
        detection: float = 1.0,
        preservation: float = 1.0,
        policy: Policy | None = None,
    ) -> CampaignReport:
        report = audit(cases, contracts, policy)
        self.records.append({"test": self.node_id, "type": "mutation_audit", **report.to_dict()})
        report.assert_thresholds(detection, preservation)
        return report

    def audit_validator(
        self,
        validator: Callable[[T], Verdict],
        cases: tuple[AuditCase[T], ...],
        *,
        obligations: tuple[Obligation, ...],
        validator_id: str,
        detection: float = 1.0,
        preservation: float = 1.0,
    ) -> ValidatorAuditReport:
        report = audit_validator(
            validator, cases, obligations=obligations, validator_id=validator_id
        )
        self.records.append({"test": self.node_id, "type": "validator_audit", **report.to_dict()})
        report.assert_thresholds(detection, preservation)
        return report


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.getgroup("narrative-contracts").addoption(
        "--narrative-report", metavar="PATH", help="Write narrative contract reports as JSON"
    )


def pytest_configure(config: pytest.Config) -> None:
    config.stash[_REPORTS] = []
    # Avoid silently losing worker results; distributed report merging is not implemented.
    if config.getoption("narrative_report") and getattr(config.option, "numprocesses", None):
        raise pytest.UsageError("--narrative-report currently requires a non-xdist run")


@pytest.fixture
def narrative(request: pytest.FixtureRequest) -> NarrativeAssertions:
    return NarrativeAssertions(request.config.stash[_REPORTS], request.node.nodeid)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    path = session.config.getoption("narrative_report")
    if path:
        output = {"schema_version": 1, "reports": session.config.stash[_REPORTS]}
        try:
            Path(path).write_text(
                json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        except OSError as exc:
            raise pytest.UsageError(f"Cannot write narrative report: {exc}") from exc
