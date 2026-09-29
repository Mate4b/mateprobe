# Pydantic reply boundary

This offline recipe uses Pydantic v2 to validate a structured reply before it
becomes a `narrative-contracts` document. Install the published packages in a
fresh Python 3.11+ environment:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install narrative-contracts==0.1.0a2 'pydantic>=2,<3'
```

Run it from the repository root:

```sh
.venv/bin/python examples/pydantic_reply.py
```

Without a checkout, download the [executable recipe](../examples/pydantic_reply.py),
then run `python pydantic_reply.py` in the environment above. The published docs
serve this file directly; downloading requires network access, evaluation does not.

The schema uses `extra="forbid"` and strict mode, so a numeric `1` is rejected
where a boolean is required. `claims_from_reply` uses an explicit allowlist with
`model_dump(include=...)`; only those fields become `Claim` values. The branch
and authoritative state come from trusted application inputs, independently of
the reply text.

The example demonstrates three boundaries:

- A valid structured reply is accepted.
- A schema-valid reply whose declarations disagree with the selected state is
  rejected by `DeclaredClaimsConsistent`.
- Contradictory arbitrary prose can still pass when its explicit declarations
  match state. The released package checks declarations against state; it does
  not infer truth from free prose.

The recipe targets the published `narrative-contracts==0.1.0a2` API and does not
use unreleased field-checking, relation, or audit APIs. Pydantic is an example
dependency only; it is not added to the package runtime dependencies.

See Pydantic's [strict mode documentation](https://docs.pydantic.dev/latest/concepts/strict_mode/)
for its coercion rules. The CI recipe is exercised with Pydantic 2.13.5; other v2
versions are allowed by the example installation command but are not all tested here.
