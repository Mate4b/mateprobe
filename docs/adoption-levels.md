# Adopt the audit progressively

These APIs require the development checkout; they are not in published `0.1.0a2`.
Start with one existing validator, one declared obligation, a known-valid baseline,
one intentionally invalid variant, and one valid variation. See the
[runnable audit example](validator-audit.md#minimal-runnable-example) for case setup.

| Level | What your validator provides | Evidence the audit can report |
|---|---|---|
| 0 | Boolean acceptance | Accepted invalid variants, rejected valid controls, unattributed rejections |
| 1 | Stable blocking finding IDs | Detections attributable to the expected obligation |
| 2 | Finding IDs with scope | Whether the right error occurred at the intended field/branch |
| 3 | Completeness and evidence | Unknown outcomes distinguished from violations, plus diagnostic evidence |

These are adoption options, not a requirement to implement all four before use.
Every level still needs justified fault and preservation cases. No level infers
truth labels or extracts arbitrary assertions from prose.

## Level 0: an existing boolean function

```python
from narrative_contracts.validator_audit import Verdict


def adapt(sample):
    return Verdict(accepted=my_existing_boolean_validator(sample))
```

This wraps your actual function; it must return a real bool. A deliberately invalid
variant that is accepted is `survived`. A valid control that is rejected is
`regressed`. An invalid variant that is rejected is `unattributed_rejection`,
because there is no evidence of *why* it was rejected.

Fault cases still name the intended failure in `expected`, for example
`expected=("customer_mismatch",)`. This expresses the test's obligation; it does
not invent a finding from the validator. Do not fill `violations` with that
expected value just because the boolean result was false. The adapter must not
receive case labels or expectations.

At this level a targeted detection score of zero means **attribution is unavailable**;
it does not mean the validator accepted every invalid input. Read the case outcomes.
Do not use the default 100% targeted-detection CI gate until findings exist. You can
inspect reports and assert specific survivor/regression counts with ordinary pytest.

## Level 1: stable finding IDs

For a validator that already reports structured errors:

```python
def adapt(sample):
    result = my_existing_validator(sample)
    return Verdict(
        accepted=result.accepted,
        violations=tuple(sorted({error.code for error in result.blocking_errors})),
        evidence=tuple(warning.message for warning in result.warnings),
    )
```

This is adapter pseudocode: map your validator's real fields and acceptance policy.
Warnings are evidence, not blocking violations. A rejection with different codes
remains unattributed. An exception remains an error; do not disguise it as a
violation to earn a detection. Stable IDs are a real maintenance cost. Do not
derive IDs from translated error messages if your framework supplies machine codes.

## Level 2: scoped findings

An error in one branch must not masquerade as a detection in another:

```python
violations = tuple(sorted({f"{error.code}:{error.path}" for error in result.blocking_errors}))
# A fault case can now require "customer_mismatch:$.refund.customer_id".
```

Use the same documented path convention in the adapter and authored cases. Do not
flatten away array indexes or branch identity when those distinguish obligations.
The external JSON Schema and Pydantic trials show real adapters with scoped IDs.

## Level 3: incomplete evidence

```python
return Verdict(
    accepted=False,
    complete=False,
    evidence=("The backend outcome could not be confirmed.",),
)
```

An incomplete variant is `undetermined`; it stays in the denominator and earns no
targeted detection. This is different from a known violation such as *claiming
completion without the required receipt*. A timeout does not prove that the
operation failed, but it cannot support an affirmative completion claim.

## Read the report before optimizing a score

- **Known gaps:** accepted invalid variants, valid controls rejected, and wrong-reason rejections.
- **Incomplete evidence and execution failures:** unknowns, crashes, and failed baselines.
- **Untested or unevaluated obligations:** no cases, or only excluded cases.
- **Evidence by obligation:** flags controls-only, faults-only, and partial evidence.

"No failures observed" only refers to these cases. A declared `scope="challenge"`
labels a deliberate broader-policy challenge; it does not exclude it from scores.
In the refund demo the prose contradiction is still one of the nine faults.
