# External validator integrations

**Development checkout only; these APIs are not in published `0.1.0a2`.**

These opt-in, offline examples audit authored domain obligations against two existing
third-party validator configurations. They do not add either library to core
`narrative-contracts`, and make no claim about production coverage or adoption.

The jsonschema example authors an IPv4 obligation. JSON Schema's `format` keyword is
an annotation by default, so `Draft202012Validator(schema)` accepts `999.1.1.1` and
`not-an-ip`. The corrected configuration supplies `FormatChecker()`. Adapter IDs use
the actual validator error code and absolute path, such as `format@/address`; schema
failures such as `required@$` remain distinct.

The Pydantic example authors an HTTPS-only policy. A default `HttpUrl` accepts an
`http://` URL. The corrected model uses `Annotated[HttpUrl,
UrlConstraints(allowed_schemes=["https"])]`. IDs use each structured error's `type`
and `loc`, for example `url_scheme@/url` and `url_parsing@/url`. The weaker before
result exposes a missing policy setting, not a library bug.

Run in the isolated integration environment with:

```sh
python -m pip install -r requirements-integrations.txt
python -m pytest tests/test_external_validators.py
python examples/external_validators.py --output reports/external-validators
```

The CLI writes before/after JSON and Markdown reports plus one measurement manifest
per integration. Manifests record authored case and obligation counts, physical source
lines for the path helper, normalization adapter, entrypoint wrappers, and corpus
factory, manually mapped fields, installed library versions, and optional observed
Git metadata and the integration script's SHA-256 digest. Repository metadata does
not prove where the callable came from. These measurements exclude total integration LOC and human
effort. With the pinned environment, the current measured values are:

| Integration | Normalization | Path helper | Wrappers | Corpus factory | Cases | Obligations |
|---|---:|---:|---:|---:|---:|---:|
| jsonschema-ipv4 | 4 | 4 | 6 | 43 | 4 | 2 |
| pydantic-https | 8 | 4 | 4 | 33 | 3 | 2 |

These values are source measurements and can change with formatting edits. No external
service is called.

Observed targeted detections are **1/3 → 3/3** for the three JSON Schema faults,
and **1/2 → 2/2** for the two Pydantic faults. Each trial preserves its one authored
valid control before and after the configuration correction. These tiny corpora
demonstrate the adapters and policy gaps; neither provides an accuracy estimate.

Official descriptions of the behavior:
[jsonschema format validation](https://python-jsonschema.readthedocs.io/en/stable/validate/#validating-formats)
and [Pydantic HttpUrl](https://docs.pydantic.dev/latest/api/networks/#pydantic.networks.HttpUrl).
The defaults are intentional. The correction changes the application's configuration,
not either third-party library.

Together with the [LifeCard adapter](lifecard-validator-audit.md), this gives three
existing engines exercised by our code. It is **not** three independent teams
integrating the tool. We have not measured independent onboarding time or retention.
