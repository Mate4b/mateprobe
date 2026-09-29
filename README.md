# Narrative Contracts

**Executable contracts for state-conditioned language generation, with mutation audits of the validators.**

Alpha `0.1.0a2`. Python 3.11+. Core runtime has zero third-party dependencies and makes no model or network calls. The optional pytest plugin adds a fixture and JSON reports.

The library checks structured state invariants and explicitly labelled lexical heuristics. It does **not** certify arbitrary prose as truthful, meaningful, or good writing. A passing declaration check only establishes consistency of the supplied declarations with supplied authoritative state.

## Install from this checkout

```sh
git clone https://github.com/pablomate4b/narrative-contracts.git
cd narrative-contracts
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]' -e ./packages/pytest-narrative-contracts
pytest
```

Both packages use the MIT license. Installable wheels and sdists are published in
[GitHub Releases](https://github.com/pablomate4b/narrative-contracts/releases); PyPI is not required.
To install the pinned alpha without a checkout:

```sh
python -m pip install \
  https://github.com/pablomate4b/narrative-contracts/releases/download/v0.1.0a2/narrative_contracts-0.1.0a2-py3-none-any.whl \
  https://github.com/pablomate4b/narrative-contracts/releases/download/v0.1.0a2/pytest_narrative_contracts-0.1.0a2-py3-none-any.whl
```

The core wheel can also be installed alone. Installation downloads packages; evaluation itself
never calls a model. Model collection is a separate, opt-in benchmark script.

Start with the [five-minute offline demo](docs/quickstart.md): a detected declaration error,
a preserved valid variation, and a prose contradiction that passes.

## State-conditioned checks

```python
from narrative_contracts import (
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
def test_outcome(narrative):
    narrative.check(document, context, contracts)
```

```sh
pytest --narrative-report=contract-results.json
```

`narrative.audit(cases, contracts, detection=0.9, preservation=0.95)` checks a mutation campaign. Both denominators must exist; an empty suite cannot claim perfect performance. See [mutation examples](examples/mutation_audit.py). Distributed pytest report merging is not yet supported; use a serial run with `--narrative-report`.

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
narrative-contracts examples/valid.json --output report.json
```

Exit status: `0` accepted, `1` rejected, `2` invalid input/configuration/I/O. Configuration accepts only built-in contract types and known fields. It never evaluates Python expressions. Library extensions use the `Contract` protocol, not untrusted imports from JSON.

## LifeCard integration

`narrative_contracts.adapters.lifecard_document` maps a card to stable surface paths and an individual state reference for every outcome. Supply post-state snapshots calculated by the trusted engine, not by the generating LLM. The adapter does not modify LifeCard or execute effects. See [example](examples/lifecard_adapter.py) and [migration guide](docs/lifecard.md).

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
[counterexamples](https://github.com/pablomate4b/narrative-contracts/issues/new/choose) with a minimal
bundle and evidence; see [contribution guidance](CONTRIBUTING.md). Publication does not imply
that independent reviewers have validated the method.

## Development

```sh
pytest
ruff check .
ruff format --check .
mypy
python -m build --no-isolation
python -m build --no-isolation packages/pytest-narrative-contracts
python benchmarks/run.py
```

[Roadmap and release gates](docs/roadmap.md) · [Contributing](CONTRIBUTING.md) · [Prior art](paper/references.bib)
