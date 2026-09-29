# Historical validator study protocol

Status: version 2 prepared 2026-09-29 (America/Argentina/Buenos_Aires), before execution.

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

## Preflight corrections and selection limitations

Version 1 is retained under `preflight-v1/` and in Git commit `5035606`.
No package reproduction was executed with that preparation. Before collection,
review of the original upstream reports found: uppercase file schemes and IDN
email addresses are valid variations, not faults; the file example needs explicit
`schemes={"file"}`; the boolean-ref issue requires a cached boolean schema in a
RefResolver store rather than a plain local reference; and the IDN case should
exercise a Unicode TLD. Those inputs/adapters and relations are corrected in v2.
Unsupported release guesses for excluded candidates are replaced with null.
The original serialization description for Pydantic #12348 was also corrected
after reading its actual ModuleType reproducer. These are pre-execution corrections,
not findings about the third-party libraries. Original flawed inputs are not evidence.

Every included issue now links to its upstream report and a commit-pinned changelog
establishing the fixed version. The ten candidates were a purposive, bounded
screening sample, not an exhaustive or randomly sampled review of issues.
Exclusion means outside this experiment or insufficient documented evidence; it
does not mean an upstream report is invalid. No population discovery rate follows.

Each included issue has two actual changed pairs: the issue-triggering variant
and a valid preservation control. The enum issue is a violation; the other three
are preservation issues, including a valid input triggering an exception.
Replay compares the full recorded normalized results against the same a3 audit;
exceptions remain errors rather than validation rejections. Baseline verdicts
and child failures are retained. The summary calls a fix reproduced only when
the before-version misbehaves on the trigger, the after-version satisfies it,
and the control is preserved in both versions.

Freeze writes the prepared ledger and source/protocol hashes once. Setup never
rewrites it. Collection verifies prepared hashes, uses isolated version-specific
environments, and records exact installed dependency versions plus downloaded
artifact hashes from pip's installation report. Re-collection installs those
recorded dependency versions when supplied via `--lock-from`. Offline replay
does not reinstall packages and is distinguished from fresh package execution.
Hashes detect accidental changes; mutable manifests are not tamper-proof evidence.
