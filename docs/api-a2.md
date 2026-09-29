# Published API: 0.1.0a2

This reference covers the installed PyPI alpha, not every symbol on `main`.
Use Python 3.11+ and pin `narrative-contracts==0.1.0a2`. See the
[complete runnable example](agent-guide.md#a-complete-pytest-example).

## Data model and evaluation

Import these names from `narrative_contracts`:

```text
Claim(key, value)
Surface(id, text, state_ref="current", claims=())
Document(surfaces)
Context(states, closed_premises=(), history=())
Policy(block_heuristics=True, block_undetermined=True)
evaluate(document, context, contracts, policy=None) -> Report
```

- `value` is a finite JSON scalar: string, integer, float, boolean or null.
  Equality is type-sensitive: `True`, `1`, `1.0`, and `"1"` differ.
- `surfaces` and `claims` are tuples. Document surface IDs must be unique.
- `states` maps trusted snapshot IDs to flat dictionaries of fact keys and scalars.
  Select each surface's snapshot in application code, not from model output.
- Required output fields and their mapping into claims belong to the application
  schema. Omitting a claim does not prove its corresponding prose assertion is absent.
- `Report.accepted` applies policy; `Report.complete` means no `undetermined` or
  `error` checks. `Report.assert_accepted()` raises `AssertionError` on rejection.
- `Report.to_dict()` returns a JSON-compatible record with checks, digests and versions.
- `Report.checks` exposes `rule_id`, `code`, `scope`, `status`, `kind`, and evidence.
  Check `status` as well as `code`: a code names the predicate, not necessarily failure.

## Built-in rules

All names below are exported by `narrative_contracts`. Rule IDs are chosen by the
caller and identify findings and mutation targets.

```text
RequiredFact(rule_id, key, expected, state_ref="current")
DeclaredClaimsConsistent(rule_id, surface_ids=(), require_claims=True)
StateChanged(rule_id, before, after, keys)
MinimumTokens(rule_id, surface_ids, minimum=10, minimum_unique=6)
LexicalRestatement(rule_id, source, target, overlap_threshold=0.7, minimum_novel_tokens=4)
ForbiddenPattern(rule_id, patterns, surface_ids, fold_accents=True)
SettledPremise(rule_id, patterns, surface_ids)
NoRepeatedText(rule_id, surface_ids)
```

The first three are state/declaration invariants. The other five are lexical
heuristics. `StateChanged` requires at least one projected key to change, not all
keys. `RequiredFact` does not inspect text. `DeclaredClaimsConsistent` with no
surface IDs applies to every surface; with `require_claims=True`, an empty set of
claims is unknown, but a partial nonempty set is not a completeness guarantee.
`SettledPremise.patterns` contains `(premise_id, regex)` pairs.
See [semantics and limitations](contracts.md) before interpreting acceptance.

## Mutation audit

Import from **`narrative_contracts.mutations`** (plural):

```text
Sample(document, context)
Target(rule_id, code, scope)
MutationCase(id, family, relation, baseline, variant, expected=(), validity=Validity.UNREVIEWED, provenance="", group="")
Relation.VIOLATION / Relation.PRESERVE
Validity.VALID / Validity.EQUIVALENT / Validity.UNREVIEWED
replace_text(sample, surface_id, text) -> Sample
audit(cases, contracts, policy=None) -> CampaignReport
```

Supply `validity` explicitly and provide nonempty provenance for `VALID` labels.
A fault needs attributable targets. `CampaignReport.summary()` and `to_dict()`
expose results; `assert_thresholds(detection=1.0, preservation=1.0)` checks both
rates and rejects undefined denominators. Labels are caller-supplied; the library
does not determine semantic equivalence. See [executable example](../examples/mutation_audit.py).

## Pytest and CLI

Install `pytest-narrative-contracts==0.1.0a2` for automatic fixture discovery:

```text
narrative.check(document, context, contracts, policy=None) -> Report
narrative.audit(cases, contracts, detection=1.0, preservation=1.0, policy=None)
```

`check` records a report and asserts acceptance. To inspect an expected rejection,
use core `evaluate`; to record it with the fixture, wrap `narrative.check` in
`pytest.raises(AssertionError)`. There is no `accepted=False` argument.

```sh
python -m pytest --narrative-report=contract-results.json
narrative-contracts input.json --output report.json
```

The CLI accepts the documented JSON bundle, not plain prose. Exit codes are
0 accepted, 1 rejected, 2 invalid input/configuration/I/O. The
[JSON example](../examples/valid.json) provides the complete format.

## Not in a2

`check_fields`, `FieldRef`, `CompareFields`, `AllowedTransition`, and
`narrative_contracts.validator_audit` are absent from a2. They are available in
[published alpha a3](api-a3.md); upgrade explicitly to use them.
