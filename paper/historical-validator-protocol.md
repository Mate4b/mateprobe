# Historical validator study protocol

Status: frozen 2026-09-29 (America/Argentina/Buenos_Aires).

This is a retrospective reproduction study, not an independent preregistration.
The unit is a documented validator defect with a public primary issue, pull
request, advisory, or release note naming the fix. A candidate is eligible only
when the upstream record describes an observable validation or validation-adjacent
behavior change and identifies both a before and after release (or commits).
Configuration omissions, documented defaults, feature requests, type-checking
only changes, and regressions without a later fix are excluded.

Before any reproduction, the candidate ledger, minimal inputs, expected behavior,
adapter source, and this protocol are hashed. Reproductions use fresh virtual
environments below `work/`; no package is installed into the study checkout or
global interpreter. Network access is explicit (`collect --network`). The offline
replay consumes only the captured normalized verdicts and validates their hashes.

Each included candidate has one valid baseline control and one invalid or newly
accepted variant. The control must remain accepted in both versions. The expected
finding is authored from the primary record and kept separate from adapter logic.
`audit_validator` outcomes are reported verbatim; errors, unsupported cases, and
failed baselines remain in the ledger and do not count as fixes. This protocol
does not tune library rules and makes no claim that the harness outperforms pytest.

The frozen target is 8--12 candidates, with at least three reproduced fixes when
the available Python/runtime/package constraints permit. Fewer successful cases
are reported honestly. For every candidate we retain package/version/runtime,
source URL and ID, rationale, input digest, adapter hash, raw before/after output,
normalized audit report, and environment `pip freeze` hash.

Primary sources are upstream GitHub issues, pull requests, release notes, or
security advisories. Minimal reproducers are authored for this study and do not
copy upstream test files.
