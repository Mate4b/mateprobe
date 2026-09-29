# Audit provenance and report schema 2

The external-validator audit uses report schema **2** in this development checkout.
The original state-evaluation and mutation-report formats are unchanged. The
pytest JSON envelope remains schema 1; each nested report has its own schema.

Every external audit includes:

- `validator_id`: caller-supplied implementation/configuration name.
- `library_version`: version of the executing library code, shared with `__version__`.
- `corpus_digest`: digest of the paired samples, targets, validity labels, and rationale.
- `schema_version`: the report format, independent from the package version.
- `provenance`: null unless explicitly supplied, or a Git snapshot labelled by source.

Reports from this unreleased checkout still identify the package version as
`0.1.0a2`; this is not proof that its new APIs are in the published wheel. Use Git
metadata and retain the exact code/configuration for development comparisons.
No package version has been republished under the same number.

## Explicitly observe a repository

```python
from narrative_contracts.provenance import observe_git
from narrative_contracts.validator_audit import audit_validator

git = observe_git("/path/to/validator-repository")
report = audit_validator(
    adapter,
    cases,
    obligations=obligations,
    validator_id="refund-policy/v4",
    provenance=git,
)
```

`observe_git` performs bounded local Git commands. It returns the full HEAD,
whether the worktree is dirty (including untracked files), and `source="observed"`.
It checks HEAD again after status; if HEAD changed, metadata becomes unknown.
Unavailable Git, a non-repository, and timeouts become explicit unknowns with a
reason. Failure to inspect never becomes a falsely clean worktree.

This observes repository metadata. It does **not** prove that the callback was
imported from that repository or that its configuration matches the commit.
Dirty status does not fingerprint uncommitted content, and the observation is not
an atomic filesystem snapshot. Preserve patches/configuration separately when
reproducibility requires them. External dependencies need their own version record.

## Caller-supplied CI metadata

```python
from narrative_contracts.provenance import supplied_git_provenance

git = supplied_git_provenance(commit="0123456789abcdef0123456789abcdef01234567")
# source="supplied", dirty=None (unknown), no Git command executed.
```

Use your real CI checkout SHA. A full 40- or 64-character hexadecimal ID is required;
format validation does not verify the commit's existence. Caller-supplied metadata
is labelled unverified and must not be described as an observed snapshot.

The core `audit_validator` never inspects Git, environment variables, the network,
or the current directory to fill missing metadata. Default calls remain pure apart
from the validator supplied by the caller. The pytest fixture accepts the same
optional `provenance` argument and records it even when thresholds fail.

## Compare two reports honestly

Check both validator identity/configuration and `corpus_digest` before comparing
scores. Matching corpus digests do not prove identical model/API behavior or
dependency versions. Changing an obligation's `scope` only changes its presentation;
it does not remove its cases from the denominator. Retain full reports and cases,
not just summary scores. Evidence and exceptions can contain private application
data, so review artifacts before sharing them publicly.
