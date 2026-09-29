# Customer-support workflow example

`examples/support_workflow.py` is a second-domain example independent of
LifeCard. It models a small refund-support policy entirely in deterministic
Python. `OrderSnapshot` is trusted input, and `trusted_refund_transition`
chooses `refund_eligible` or `refund_ineligible` from that input. The function
does not inspect reply text and makes no external calls.

`build_support_scenario` then creates a `Context` containing the current
snapshot and both branch snapshots, a `Surface` containing the candidate
reply, and contracts for that case. The exact contracts are:

- `RequiredFact` checks that the request is a refund request.
- `BranchSelection` checks that the reply points at the branch selected by the
  trusted transition.
- `StateChanged` checks that at least one key in the explicit refund projection
  (decision, eligibility or action) changes from pending to the selected
  result. The trusted workflow supplies all three changed keys here; the core
  contract intentionally guarantees only a nonempty projected difference.
- `DeclaredClaimsConsistent` checks each declared claim against the surface's
  own `state_ref`.

The reply-length and unsupported-certainty checks are explicit heuristics. They
are lexical proxies and do not establish that prose is true or that it entails
its declarations. For example, the `arbitrary_prose` case uses an unrelated
but sufficiently long sentence with correct declarations. Its report is
accepted by design: the declarations are consistent with trusted state, while
the arbitrary sentence itself has not been verified. This is the library's
structured-claim boundary, not a claim that the sentence describes a refund.

The `wrong_branch_claim` case keeps the correct branch selected but copies the
opposite branch's `refund.eligible` and `refund.action` declarations; the
declaration invariant rejects it even though both branch snapshots are present.
The `cross_branch_state` case copies claims from the opposite snapshot and
points the surface at that snapshot. Those declarations can pass their own
branch check, but `BranchSelection` rejects the case because the trusted
transition selected the other branch. This makes accidental cross-branch
masking visible.

Run the standalone corpus with:

```sh
.venv/bin/python examples/support_workflow.py
```

The JSON fixture contains the valid eligible case and can be checked with the
CLI. It intentionally uses only built-in contracts, because the CLI cannot
load the example-local `BranchSelection` rule; use the Python API for the full
trusted-branch guarantee:

```sh
.venv/bin/mateprobe examples/support_workflow.json
```

For a small deterministic benchmark corpus, import
`generate_support_cases()`. Each `SupportScenario` exposes `document`,
`context`, `contracts`, `expected_branch`, `variant` and `expected_accept`, and
its `evaluate()` method returns the normal `Report`. No model, network, legal
claim or real customer data is involved.
