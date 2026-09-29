# MateProbe by Mate4B

**Test whether your Python validator catches invalid AI outputs and preserves valid ones.**

MateProbe audits your existing validator with paired input variants:
known faults and valid controls. It reports missed faults, rejections for the wrong
reason, incomplete evidence, and execution errors. You supply the cases and policy;
the audit runs without an LLM judge.

Here, mutations are changes to the **samples passed to the validator**. The audit
does not rewrite its Python source. See [how to test AI output validators](docs/testing-ai-output-validators.md)
for the workflow and how it fits with ordinary pytest and source mutation testing.

Alpha `0.1.0a4`. Python 3.11+. Core runtime has zero third-party dependencies and makes no model or network calls. The optional pytest plugin adds a fixture and JSON reports.

The library checks structured state invariants and explicitly labelled lexical heuristics. It does **not** certify arbitrary prose as truthful, meaningful, or good writing. A passing declaration check only establishes consistency of the supplied declarations with supplied authoritative state.

[Documentation](https://mate4b.github.io/mateprobe/) ·
[Agent integration guide](docs/agent-guide.md) · [Published API](docs/api-a4.md) ·
[Pydantic recipe](docs/pydantic.md) · [Documentation index for agents](llms.txt)

[Try the one-file audit](docs/first-audit.md): a refund claim without a matching receipt,
a retained prose survivor, and a pytest regression.

Previously **Narrative Contracts**. Existing users: see the [migration guide](docs/migration-mateprobe.md).

## Audit an existing validator

You do not need to change your validator to start. Wrap its existing result and
supply the failures and valid variations you care about. The APIs below are available in **0.1.0a4**; older `0.1.0a2` wheels do not include them.

Pytest can express every individual assertion. This library supplies paired
baseline/variant execution, targeted finding attribution, valid controls, honest
error accounting, obligation inventories, and CI reports. You still define the
domain obligations and justify the cases.

For example, a test expects `customer_mismatch`, but the validator rejects with
`malformed_input`. A generic `assert not validate(sample)` passes; the audit
reports **unattributed rejection**, not successful detection of the customer error.

- [Audit an existing validator](docs/validator-audit.md) without adopting `Context`,
  `Surface`, or claims. Wrap its verdict, supply paired cases and obligations, and
  inspect detections, survivors, false rejections, and failures.
- [Bind output fields to state](docs/state-bindings.md) with `check_fields`, or use
  the new bounded equality, numeric-limit, and transition contracts.
- Run the [before/after refund demo](examples/audit_existing_validator.py) or the
  opt-in [existing LifeCard validator integration](docs/lifecard-validator-audit.md).

```sh
python examples/audit_existing_validator.py --output /tmp/refund-audit
```

The refund demo detects 3 of 9 authored faults before the fix and 8 of 9 afterward,
preserving both valid controls. The prose-only contradiction still passes and an
untested idempotency obligation stays visible. The prose challenge remains **inside
the nine-fault denominator**. This is an illustrative audit of
validators, not measured production accuracy. See [scope and limits](docs/development-scope.md).

Start with the [adoption levels](docs/adoption-levels.md): a boolean validator can
expose accepted bad cases and rejected valid controls; finding IDs enable targeted
detection, scopes refine attribution, and completeness/evidence explain unknowns.
The [external-validator trials](docs/external-validator-integrations.md) adapt
JSON Schema and Pydantic without adding runtime dependencies to the core.

Reports lead with known gaps, incomplete evidence, and untested obligations.
[Opt-in provenance](docs/audit-provenance.md) records the library version, corpus
digest, and observed or caller-supplied Git metadata. These are audit results for
supplied cases, not a percentage of total agent coverage.

The corpus becomes a regression suite for your validation policy. Follow the
[survivor-to-regression guide](docs/policy-regression.md) to keep a discovered gap
as a permanent pytest check and share a sanitized integration report.

## When to use this

- Your application owns authoritative state and needs to check explicit output declarations
  against it: refund status, account balances, workflow outcomes, or narrative branches.
- You need repeatable pytest failures and reports for specified constraints, without an
  inference call during evaluation.
- You want to audit a validator using faulty variants **and** valid controls, retaining
  missed faults and false rejections as evidence.

Start with the [published alpha quickstart](docs/quickstart.md). Schema validation and
state checks solve different problems; the [Pydantic recipe](docs/pydantic.md) shows both.

## When this is insufficient

- Checking whether unrestricted prose is truthful or entails the supplied declarations.
- Discovering authoritative facts, executing state transitions, or enforcing runtime permissions.
- Measuring writing quality, broad semantic equivalence, or production accuracy from a
  mutation score alone.

An LLM judge may evaluate open-ended properties outside these predicates. The two approaches
can coexist; this library does not claim to replace every judge or guardrail system.
See [choosing an evaluation method](docs/choosing-an-evaluator.md).

## Install the current alpha

Install the pinned alpha from PyPI with:

```sh
python -m pip install mateprobe==0.1.0a4 pytest-mateprobe==0.1.0a4
```

Install only `mateprobe==0.1.0a4` if you do not need the pytest integration.

## Install from this checkout

```sh
git clone https://github.com/Mate4b/mateprobe.git
cd mateprobe
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]' -e ./packages/pytest-mateprobe
pytest
```

Both packages use the MIT license. Versioned wheels and sdists are distributed through
[GitHub Releases](https://github.com/Mate4b/mateprobe/releases).
To install the pinned alpha without a checkout:

```sh
python -m pip install \
  https://github.com/Mate4b/mateprobe/releases/download/v0.1.0a4/mateprobe-0.1.0a4-py3-none-any.whl \
  https://github.com/Mate4b/mateprobe/releases/download/v0.1.0a4/pytest_mateprobe-0.1.0a4-py3-none-any.whl
```

The core wheel can also be installed alone. Installation downloads packages; evaluation itself
never calls a model. Model collection is a separate, opt-in benchmark script.

Start with the [five-minute offline demo](docs/quickstart.md): a detected declaration error,
a preserved valid variation, and a prose contradiction that passes.

## State-conditioned checks

```python
from mateprobe import (
    Claim,
    Context,
    DeclaredClaimsConsistent,
    Document,
    MinimumTokens,
    RequiredFact,
    Surface,
    evaluate,
)

context = Context(
    {
        "current": {"offer.status": "pending"},
        "accept": {"offer.status": "accepted"},
        "reject": {"offer.status": "rejected"},
    }
)
document = Document(
    (
        Surface(
            "outcome",
            "You sign the agreement and arrange a meeting with your new team.",
            state_ref="accept",
            claims=(Claim("offer.status", "accepted"),),
        ),
    )
)
contracts = (
    RequiredFact("offer-was-pending", "offer.status", "pending"),
    DeclaredClaimsConsistent("outcome-facts", ("outcome",)),
    MinimumTokens("lexical-floor", ("outcome",), minimum=8, minimum_unique=5),
)
report = evaluate(document, context, contracts)
report.assert_accepted()
print(report.to_dict())
```

A claim under `reject` cannot use facts from `accept`. Missing snapshots or facts produce `undetermined`, not success. Rule exceptions produce `error`. Strict policy blocks both; heuristic violations can be configured as advisory with `Policy(block_heuristics=False)`.

## Pytest

Install the second package for automatic `pytest11` discovery:

```python
def test_outcome(mateprobe):
    mateprobe.check(document, context, contracts)
```

```sh
pytest --mateprobe-report=contract-results.json
```

`mateprobe.audit(cases, contracts, detection=0.9, preservation=0.95)` checks a mutation campaign. Both denominators must exist; an empty suite cannot claim perfect performance. See [mutation examples](examples/mutation_audit.py). Distributed pytest report merging is not yet supported; use a serial run with `--mateprobe-report`.

## What is included

| Contract | Kind | Actual guarantee / limitation |
|---|---|---|
| `RequiredFact` | Invariant | Type-sensitive equality of a declared required fact in a named snapshot; does not inspect prose. |
| `DeclaredClaimsConsistent` | Invariant | Declared claims match their own branch snapshot; undeclared assertions remain unchecked. |
| `StateChanged` | Invariant | At least one key in an explicit state projection changes; excludes unrelated bookkeeping. |
| `MinimumTokens` | Heuristic | Minimum word-token count and lexical diversity; not information content. |
| `LexicalRestatement` | Heuristic | High source-token overlap with too few novel tokens; no character-length exemption. |
| `ForbiddenPattern` | Heuristic | Matches configured regex on Unicode-normalized text; no negation or quotation reasoning. |
| `SettledPremise` | Heuristic | Configured phrase recognizers conditioned on closed premise IDs; unsupported IDs are explicit. |
| `NoRepeatedText` | Heuristic | Repeated normalized token sequence in supplied history; no semantic paraphrase detection. |

All reports carry input/configuration digests, rule versions, evidence, scope and result status. No timestamps contaminate deterministic reports. See [architecture](docs/architecture.md) and [contract semantics](docs/contracts.md).

## Audit the evaluator

The mutation runner records baseline acceptance, attributable detections, survivors, valid-variant regressions and exclusions. A hit must match **rule ID + finding code + scope**; an unrelated rejection or exception does not count as a detection. Semantic validity of a mutation is caller-supplied and requires provenance. No-op, equivalent and unreviewed cases are reported as exclusions.

```sh
python examples/mutation_audit.py
python benchmarks/run.py
```

The included benchmark has author-constructed state/text variations and deliberate scope challenges. It is a feasibility artifact, **not** evidence of accuracy on natural LLM outputs. [Original synthetic results](benchmarks/results/summary.md),
[expanded mutation campaign](docs/mutation-campaign.md), and
[real-model pilot](docs/natural-benchmark.md) are separate evidence streams.
The follow-up [384-case mutation audit of captured Gemma/Qwen outputs](docs/real-output-mutations.md)
separates declaration, lexical, schema, control and out-of-scope prose evidence.
All 64 deliberately inserted prose-only contradictions pass; no semantic accuracy is claimed.
Read the [technical report](paper/draft.md) and [frozen release protocol](paper/release-protocol.md).
No human labels are required to use or reproduce the alpha; without them, natural-output
acceptance must not be called semantic accuracy.

## JSON and CLI

```sh
mateprobe examples/valid.json --output report.json
```

Exit status: `0` accepted, `1` rejected, `2` invalid input/configuration/I/O. Configuration accepts only built-in contract types and known fields. It never evaluates Python expressions. Library extensions use the `Contract` protocol, not untrusted imports from JSON.

## LifeCard integration

`mateprobe.adapters.lifecard_document` maps a card to stable surface paths and an individual state reference for every outcome. Supply post-state snapshots calculated by the trusted engine, not by the generating LLM. The adapter does not modify LifeCard or execute effects. See [example](examples/lifecard_adapter.py) and [migration guide](docs/lifecard.md).

## Independent support workflow

The [customer-support example](docs/support-workflow.md) computes refund eligibility with
trusted Python state transitions, checks branch selection and declarations, and demonstrates
valid paraphrases and failures that remain outside the prose guarantee. It is independent of
LifeCard; this is an executable second integration, not evidence of broad domain generalization.

## Reproduce or challenge the results

```sh
python benchmarks/expanded_mutations.py --output /tmp/expanded-campaign
python benchmarks/natural.py replay --input benchmarks/natural-results --output /tmp/natural-replay
```

Replay requires no model, network or API key. Output directories must be new. Submit
[counterexamples](https://github.com/Mate4b/mateprobe/issues/new/choose) with a minimal
bundle and evidence; see [contribution guidance](CONTRIBUTING.md). Publication does not imply
that independent reviewers have validated the method.

## Development

```sh
pytest
ruff check .
ruff format --check .
mypy
python -m build --no-isolation
python -m build --no-isolation packages/pytest-mateprobe
python benchmarks/run.py
```

[Roadmap and release gates](docs/roadmap.md) · [Contributing](CONTRIBUTING.md) · [Prior art](paper/references.bib)
