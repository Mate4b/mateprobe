"""Run a small, opt-in audit against a local LifeCard checkout.

This adapter deliberately imports LifeCard's own test helpers only after the
checkout is supplied on the command line.  No LifeCard card or state fixture is
stored in this repository.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

# The adapter only reads the external checkout; avoid creating __pycache__
# files there while importing its test helpers.
sys.dont_write_bytecode = True

_ATTRIBUTION = "lifecard.CardValidatorPipeline"


def _finding_id(finding: Any) -> str:
    """Keep findings attributable to LifeCard code and its reported path."""

    return f"{_ATTRIBUTION}:{finding.code}:{finding.path}"


def _load_fixture_module(root: Path) -> Any:
    path = root / "tests" / "unit" / "test_phase4_layer4_challenger.py"
    spec = importlib.util.spec_from_file_location("lifecard_audit_fixture", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import LifeCard fixture module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_environment(root: Path) -> tuple[Any, Any, Any, Any, Any, Any]:
    """Build LifeCard's real pipeline using its local test configuration."""

    src = root / "src"
    sys.path.insert(0, str(src))
    from lifecard.content import load_catalog
    from lifecard.product_policy import ProductPolicyRegistry
    from lifecard.registry import Registry
    from lifecard.runtime import SimulationRunner, default_adult

    fixture = _load_fixture_module(root)
    registry = Registry.load(root / "content" / "tag_registry.yaml")
    policies = ProductPolicyRegistry.load(root / "content" / "product_policy_registry.yaml")
    catalog = load_catalog(root / "content" / "examples" / "cards.json", registry, policies)
    runner = SimulationRunner(catalog, registry)
    spec = fixture.make_spec()
    state = default_adult(42, catalog_version=catalog.version)
    return fixture, registry, catalog, runner, spec, state


def _with_variant(
    card: dict[str, Any],
    *,
    label: str | None = None,
    outcome_body: str | None = None,
    empty_effects: bool = False,
    body_suffix: str = "",
) -> dict[str, Any]:
    variant = copy.deepcopy(card)
    option = variant["options"][0]
    outcome = option["outcomes"][0]
    if label is not None:
        option["label_template"] = label
    if outcome_body is not None:
        outcome["body_template"] = outcome_body
    if empty_effects:
        outcome["effects"] = []
    if body_suffix:
        variant["body_template"] += body_suffix
    return variant


def _run(root: Path) -> tuple[Any, dict[str, str], dict[str, Any]]:
    from mateprobe.mutations import Relation, Validity
    from mateprobe.validator_audit import (
        AuditCase,
        Obligation,
        Verdict,
        audit_validator,
    )

    fixture, registry, catalog, runner, spec, state = _build_environment(root)
    clean = fixture.get_clean_card_dict()

    def invoke(card: dict[str, Any]) -> Verdict:
        # Recreate the trusted inputs for every call.  The audit library also
        # deep-copies case values, but this protects LifeCard's mutable inputs.
        validator = fixture.make_validator(catalog, registry, runner)
        report = validator.validate(
            copy.deepcopy(card), copy.deepcopy(spec), copy.deepcopy(state), []
        )
        # LifeCard's ``approved`` projection treats warnings as non-blocking;
        # keep those in evidence but expose only blocking/high findings as
        # audit violations so Verdict's accepted/violations invariant holds.
        findings_list = [
            _finding_id(item)
            for item in report.findings
            if item.severity.value in {"high", "blocker"}
        ]
        findings = tuple(dict.fromkeys(findings_list))
        evidence = tuple(item.evidence for item in report.findings)
        return Verdict(
            accepted=report.approved,
            violations=findings,
            complete=True,
            evidence=evidence,
        )

    anti_short = f"{_ATTRIBUTION}:NARRATIVE_ANTI_BUREAUCRACY:$.options[0].outcomes[0].body_template"
    anti_long = anti_short
    significance = f"{_ATTRIBUTION}:SIGNIFICANCE_OUTCOME_WITHOUT_ADVANCE:$.options[0].outcomes[0]"
    cases = (
        AuditCase(
            id="short-label-restatement",
            obligation="layer4-anti-bureaucracy",
            baseline=clean,
            variant=_with_variant(
                clean, label="Promoción aceptada", outcome_body="Promoción aceptada."
            ),
            relation=Relation.VIOLATION,
            expected=(anti_short,),
            validity=Validity.VALID,
            provenance="authored targeted stress case for the short-outcome guard",
        ),
        AuditCase(
            id="padded-label-restatement",
            obligation="layer4-length-independent-restatement",
            baseline=clean,
            variant=_with_variant(
                clean,
                label="Promoción aceptada",
                outcome_body=("Promoción aceptada. " * 10),
            ),
            relation=Relation.VIOLATION,
            expected=(anti_long,),
            validity=Validity.VALID,
            provenance="authored broader-policy challenge; desired length-independent rule exceeds current <90-char guard",
        ),
        AuditCase(
            id="space-edit-control",
            obligation="layer4-anti-bureaucracy",
            baseline=clean,
            variant=_with_variant(clean, body_suffix="  "),
            relation=Relation.PRESERVE,
            validity=Validity.VALID,
            provenance="authored valid control: whitespace-only edit",
        ),
        AuditCase(
            id="empty-effects-stress",
            obligation="layer4-meaningful-effect",
            baseline=clean,
            variant=_with_variant(clean, empty_effects=True),
            relation=Relation.VIOLATION,
            expected=(significance,),
            validity=Validity.VALID,
            provenance="authored targeted stress case for empty effects",
        ),
    )
    obligations = (
        Obligation(
            "layer4-anti-bureaucracy", "Short outcome text must not restate its option label."
        ),
        Obligation(
            "layer4-length-independent-restatement",
            "Outcome text must not merely repeat its option label at any length.",
            scope="challenge",
        ),
        Obligation(
            "layer4-meaningful-effect", "An outcome must include a meaningful domain effect."
        ),
    )
    report = audit_validator(
        invoke, cases, obligations=obligations, validator_id="lifecard.card-validator-pipeline"
    )
    manifest = {}
    for relative in ("src/lifecard/runtime.py", "tests/unit/test_phase4_layer4_challenger.py"):
        data = (root / relative).read_bytes()
        manifest[relative] = hashlib.sha256(data).hexdigest()
    metadata = {
        "validator_id": "lifecard.card-validator-pipeline",
        "lifecard_root": str(root),
        "source_manifest": manifest,
        "attribution": _ATTRIBUTION,
        "scope": "authored targeted stress cases; no independent gold labels",
    }
    return report, manifest, metadata


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lifecard-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.lifecard_root.expanduser().resolve()
    if not (root / "src" / "lifecard").is_dir():
        parser.error(f"not a LifeCard checkout: {root}")
    report, _, metadata = _run(root)
    payload = {"metadata": metadata, "audit": report.to_dict()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(report.to_markdown())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
