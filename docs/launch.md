# What does your validator actually catch?

An assertion like `assert not validate(sample)` can pass for the wrong reason:
you expected `customer_mismatch`, but the validator rejected `malformed_input`.
MateProbe by Mate4B audits paired cases and reports that as an **unattributed
rejection**, rather than a successful targeted detection.

Bring your existing Python validator. Define the failures you care about and
valid variations it must preserve. The audit reports which faults survive, which
findings match, where evidence is incomplete, and which obligations have no tests.

## Try it with one file

[Run your first audit](first-audit.md): install the published alpha, download one
script, and see a refund validator accept an unsupported completion claim. Add
the receipt check and keep the same corpus as a pytest regression suite.

The authored demo goes from 0/3 to 2/3 targeted detections, preserving its valid
control. The remaining prose-only contradiction stays visible and in the score.
That is an explicit limit, not a solved hallucination problem.

## What you bring; what the library does

You provide the validator, domain obligations, paired samples and justified labels.
Your application supplies trustworthy state and execution evidence. The library
handles execution, finding attribution, controls, accounting and JSON/Markdown
reports. It does not decide which policies your business should enforce.

Start with a boolean adapter; add stable finding IDs when you need targeted
attribution. No model calls or Document/Claim migration are required for this audit.
The corpus can then track regressions across validator, prompt or model changes
when you supply the corresponding samples and evidence.

## Help test its usefulness

Try one obligation from your own system. [Report what happened](integration-feedback.md):
where you got stuck, a relevant survivor, whether you changed code/configuration,
and whether the case became a permanent test. Reports with no useful findings are
welcome. Remove private data before sharing.

These are alpha tools with authored examples. We have not established independent
adoption, reduced engineering time, or general semantic accuracy.

[Source and issues](https://github.com/Mate4b/mateprobe) ·
[Published API](api-a4.md) · [Scope and limits](development-scope.md)
