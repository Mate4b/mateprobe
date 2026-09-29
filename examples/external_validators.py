"""Offline audits of two existing third-party validator configurations."""

import argparse
import hashlib
import inspect
import json
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
from typing import Annotated, Any

from jsonschema import Draft202012Validator, FormatChecker
from pydantic import BaseModel, HttpUrl, ValidationError
from pydantic.networks import UrlConstraints

from narrative_contracts.mutations import Relation, Validity
from narrative_contracts.provenance import observe_git
from narrative_contracts.validator_audit import AuditCase, Obligation, Verdict, audit_validator


def _path(path: Any) -> str:
    if not path:
        return "$"
    return "/" + "/".join(str(part).replace("~", "~0").replace("/", "~1") for part in path)


def _jsonschema_adapter(validator: Any, sample: dict[str, Any]) -> Verdict:
    errors = tuple(validator.iter_errors(sample))
    ids = tuple(sorted({f"{error.validator}@{_path(error.absolute_path)}" for error in errors}))
    return Verdict(not errors, ids, evidence=tuple(error.message for error in errors))


IPV4_SCHEMA = {
    "type": "object",
    "properties": {"address": {"type": "string", "format": "ipv4"}},
    "required": ["address"],
    "additionalProperties": False,
}


def jsonschema_before(sample: dict[str, Any]) -> Verdict:
    return _jsonschema_adapter(Draft202012Validator(IPV4_SCHEMA), sample)


def jsonschema_after(sample: dict[str, Any]) -> Verdict:
    return _jsonschema_adapter(
        Draft202012Validator(IPV4_SCHEMA, format_checker=FormatChecker()), sample
    )


JSON_OBLIGATIONS = (
    Obligation("ipv4", "The address field must contain a valid IPv4 address."),
    Obligation("schema", "The payload must satisfy the authored object schema."),
)


def jsonschema_cases() -> tuple[AuditCase[dict[str, Any]], ...]:
    baseline = {"address": "192.0.2.10"}
    return (
        AuditCase(
            "ipv4-999-range",
            "ipv4",
            baseline,
            {"address": "999.1.1.1"},
            Relation.VIOLATION,
            ("format@/address",),
            Validity.VALID,
            "Authored: IPv4 octets cannot exceed 255.",
        ),
        AuditCase(
            "ipv4-not-an-ip",
            "ipv4",
            baseline,
            {"address": "not-an-ip"},
            Relation.VIOLATION,
            ("format@/address",),
            Validity.VALID,
            "Authored: arbitrary text is not an IPv4 address.",
        ),
        AuditCase(
            "valid-ipv4-control",
            "ipv4",
            baseline,
            {"address": "192.0.2.11"},
            Relation.PRESERVE,
            validity=Validity.VALID,
            provenance="Authored TEST-NET-1 IPv4 control.",
        ),
        AuditCase(
            "missing-address-schema-error",
            "schema",
            baseline,
            {},
            Relation.VIOLATION,
            ("required@$",),
            Validity.VALID,
            "Authored: required address property is absent.",
        ),
    )


class _DefaultHttpModel(BaseModel):
    url: HttpUrl


_HttpsUrl = Annotated[HttpUrl, UrlConstraints(allowed_schemes=["https"])]


class _HttpsOnlyModel(BaseModel):
    url: _HttpsUrl


def _pydantic_adapter(model: type[BaseModel], sample: dict[str, Any]) -> Verdict:
    try:
        model.model_validate(sample)
    except ValidationError as exc:
        errors = tuple(exc.errors())
        ids = tuple(sorted({f"{error['type']}@{_path(error.get('loc', ()))}" for error in errors}))
        return Verdict(False, ids, evidence=tuple(error["msg"] for error in errors))
    return Verdict(True)


def pydantic_before(sample: dict[str, Any]) -> Verdict:
    return _pydantic_adapter(_DefaultHttpModel, sample)


def pydantic_after(sample: dict[str, Any]) -> Verdict:
    return _pydantic_adapter(_HttpsOnlyModel, sample)


PYDANTIC_OBLIGATIONS = (
    Obligation("https", "The endpoint URL must use HTTPS under the authored policy."),
    Obligation("url-parse", "The endpoint must be a parseable HTTP URL."),
)


def pydantic_cases() -> tuple[AuditCase[dict[str, Any]], ...]:
    baseline = {"url": "https://api.example.test/v1"}
    return (
        AuditCase(
            "http-disallowed-by-policy",
            "https",
            baseline,
            {"url": "http://api.example.test/v1"},
            Relation.VIOLATION,
            ("url_scheme@/url",),
            Validity.VALID,
            "Authored HTTPS-only policy.",
        ),
        AuditCase(
            "malformed-url",
            "url-parse",
            baseline,
            {"url": "not a url"},
            Relation.VIOLATION,
            ("url_parsing@/url",),
            Validity.VALID,
            "Authored malformed URL challenge.",
        ),
        AuditCase(
            "valid-https-control",
            "https",
            baseline,
            {"url": "https://api.example.test/v2"},
            Relation.PRESERVE,
            validity=Validity.VALID,
            provenance="Authored HTTPS control.",
        ),
    )


def _source_lines(function: Any) -> int:
    return len(inspect.getsourcelines(function)[0])


def _measurement_manifest(
    name: str,
    before: Any,
    after: Any,
    cases: Any,
    obligations: Any,
    helpers: tuple[Any, ...],
    provenance: Any,
) -> dict[str, Any]:
    helper_lines = [_source_lines(helper) for helper in helpers]
    return {
        "integration": name,
        "component_loc": {
            "normalization_adapter": sum(helper_lines),
            "path_helper": _source_lines(_path),
            "entrypoint_wrappers": _source_lines(before) + _source_lines(after),
            "corpus_factory": _source_lines(cases),
        },
        "measurement_definition": "Physical source lines from inspect.getsourcelines, including blanks; excludes total integration LOC and human effort.",
        "authored_corpus": {"cases": len(cases()), "obligations": len(obligations)},
        "manual_mapped_fields": [
            "accepted/rejected",
            "error code/type",
            "error path/loc",
            "error message",
        ],
        "library_versions": {"jsonschema": version("jsonschema"), "pydantic": version("pydantic")},
        "provenance": asdict(provenance) if provenance is not None else None,
        "integration_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }


def _run(
    name: str,
    before: Any,
    after: Any,
    cases: Any,
    obligations: Any,
    helpers: tuple[Any, ...],
    output: Path | None,
    provenance: Any = None,
) -> None:
    reports = {}
    for label, validator in (("before", before), ("after", after)):
        report = audit_validator(
            validator,
            cases(),
            obligations=obligations,
            validator_id=f"{name}/{label}/1",
            provenance=provenance,
        )
        reports[label] = report
        print(report.to_markdown())
        if output:
            output.mkdir(parents=True, exist_ok=True)
            (output / f"{name}-{label}.json").write_text(
                json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8"
            )
            (output / f"{name}-{label}.md").write_text(report.to_markdown(), encoding="utf-8")
    if output:
        manifest = _measurement_manifest(
            name, before, after, cases, obligations, helpers, provenance
        )
        manifest["summary_before"] = reports["before"].summary()
        manifest["summary_after"] = reports["after"].summary()
        (output / f"{name}-manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    provenance = observe_git(Path(__file__).resolve().parents[1]) if args.output else None
    _run(
        "jsonschema-ipv4",
        jsonschema_before,
        jsonschema_after,
        jsonschema_cases,
        JSON_OBLIGATIONS,
        (_jsonschema_adapter,),
        args.output,
        provenance,
    )
    _run(
        "pydantic-https",
        pydantic_before,
        pydantic_after,
        pydantic_cases,
        PYDANTIC_OBLIGATIONS,
        (_pydantic_adapter,),
        args.output,
        provenance,
    )


if __name__ == "__main__":
    main()
