# MateProbe API: 0.1.0a4

```sh
python -m pip install mateprobe==0.1.0a4 pytest-mateprobe==0.1.0a4
```

Python 3.11+; the pytest plugin is optional. Core runtime has zero third-party
dependencies. You do not need to change your validator to start auditing it.

## Audit an existing validator

Import `AuditCase`, `Obligation`, `Verdict`, `ValidatorAuditReport`, and
`audit_validator` from `mateprobe.validator_audit`. Import `Relation`
and `Validity` from `mateprobe.mutations`.

- [Runnable audit and result semantics](validator-audit.md).
- [Progressive adoption](adoption-levels.md), beginning with a boolean adapter.
- [Keep a survivor as a regression test](policy-regression.md), including the
  `mateprobe.audit_validator(...)` pytest fixture and retained JSON artifacts.
- [Independent evidence flags and provenance](audit-provenance.md).
- [JSON Schema and Pydantic integration trials](external-validator-integrations.md).

The adapter receives only the sample, not its expected findings. A rejection with
no matching finding IDs is unattributed, not targeted detection. Errors and
unknown variants remain in the denominator. The caller defines and justifies
obligations, fault cases, and valid controls; the library does not infer labels.

## State-conditioned checks

`check_fields`, `CompareFields`, and `AllowedTransition` are available from
`mateprobe`. See [field bindings and bounded relations](state-bindings.md).

The Document/Claim constructors, contracts, evaluation states, CLI and original
mutation API retain the [a2 reference signatures](api-a2.md). Install a4 when
combining those APIs with the new helpers. The historical reference's a2 install
commands are retained for reproducibility.

## Report compatibility

External-validator reports use schema 2, including independent obligation flags;
`assessment` remains a display summary. The pytest envelope stays at schema 1 and
each nested report carries its own format. Package/report `library_version` is
`0.1.0a4`. Package versions and report schema versions describe different things.

No result certifies arbitrary prose as truthful or establishes general policy
coverage. Review [scope and limits](development-scope.md) before using a score.
