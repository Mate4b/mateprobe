---
title: How to test AI output validators in Python
description: Audit an existing Python validator with invalid output samples and valid controls. Track missed faults, wrong-reason rejections, missing evidence and errors in pytest.
---

# How to test AI output validators in Python

You already validate structured responses from an LLM or agent. How do you know
the validator catches the policy violations you care about, while accepting valid
changes? **MateProbe by Mate4B runs your validator against paired samples and
reports what it detects, misses, or rejects for an unrelated reason.**

The independent `audit_validator` API is available in published `0.1.0a4` for
Python 3.11+. It works with an adapter around your existing function; adopting the
library's built-in state contracts or `Document`/`Claim` representation is optional.

## Start with a specific failure

Suppose an agent returns `refund_completed=True`. Your schema accepts the boolean,
but application policy also requires a completed backend receipt for the same
request. Test those obligations separately:

| Sample | Expected behavior |
| --- | --- |
| Completion claim with a matching completed receipt | Accept the baseline |
| Completion claim without supporting receipt evidence | Reject under the declared completion policy |
| Completion claim with another request's receipt | Reject for the receipt mismatch |
| Honest pending declaration when completion is unconfirmed | Preserve the valid control |

Your application supplies the authoritative receipts and justifies the labels.
A missing receipt does not prove an operation never happened. The audit checks
the specified evidence policy on these samples.

[Run the one-file refund audit](first-audit.md) from PyPI without cloning this repo.
It includes a prose-only contradiction that still passes, so the known limit
remains visible. No API key or model is needed for that example.

## Why isn't any rejection enough?

If a case expects `customer_mismatch` but gets `malformed_input`, a generic
`assert not validate(sample)` passes. The audit records an **unattributed
rejection** because the intended finding was not observed. A crash is an execution
error; missing evidence can be reported as an incomplete verdict. Neither is
credited as a targeted detection.

A valid control checks the other direction: a wording change or another permitted
value must stay accepted. Rejecting every input cannot establish useful coverage.

## Input audits, source mutation testing, and pytest

| Approach | What changes | Question it answers |
| --- | --- | --- |
| This validator audit | Caller-supplied input samples, with justified fault/control labels | Does the validator detect these faults and preserve these valid cases? |
| Source mutation testing | Program source, with tests run against altered implementations | Do the tests detect these changes to the implementation? |
| Ordinary pytest assertions | Whatever fixtures and assertions you write | Does the code satisfy these explicit test expectations? |

These approaches can be used together. MateProbe by Mate4B adds paired execution,
finding attribution, obligation inventories, and JSON/Markdown reports to a supplied
corpus. It does not edit validator source or automatically invent and label mutations.
Every individual expectation can also be expressed directly in pytest.

## Connect your validator and keep a regression

1. Wrap its actual result in `Verdict`; preserve its finding IDs and completeness.
   A boolean-only adapter is supported, but a rejection alone cannot identify the cause.
2. Define an `Obligation` and `AuditCase` pairs: an accepted baseline, justified
   invalid variants, and valid controls. Expected findings belong to cases, never
   inside the adapter's output.
3. Call `audit_validator`, inspect individual outcomes, and retain survivors and errors.
4. Use the optional `mateprobe.audit_validator` pytest fixture to set thresholds and
   write `--mateprobe-report=contract-results.json`. Assert important case outcomes
   so a new miss cannot silently replace an acknowledged gap.

See [the adapter API](validator-audit.md), [real Pydantic and JSON Schema adapters](external-validator-integrations.md),
and [the regression walkthrough](policy-regression.md) for executable integrations.

## Can this replace an LLM judge?

It can audit checks whose behavior is explicitly defined by your policy and cases,
without introducing a judge. The built-in checks run offline; an arbitrary wrapped
validator retains its own dependencies and behavior. Reproducible results require
a deterministic validator and fixed inputs/configuration.

It cannot certify unrestricted prose as true or helpful. A mutation score measures
the supplied corpus, not production accuracy or total policy coverage. Use
[the evaluation selection guide](choosing-an-evaluator.md) to choose checks for the
properties you actually need. The [a3 integration observation](agent-readiness.md)
shows one agent implementing a fresh inventory audit, with its limits documented.
