# Tell us what happened with your validator

The useful question is whether an audit found a policy failure worth fixing and
keeping as a regression. Getting stuck or finding nothing useful also matters.
An integration report is voluntary; external evaluation is not a release gate.

[Open an integration report](https://github.com/Mate4b/mateprobe/issues/new?template=integration-report.yml).
Use synthetic or sanitized examples; never paste credentials, customer records,
or unreviewed production traces. Evidence and exception messages can contain
application data even when the report stores input digests instead of raw inputs.

## Minimal report

- **Context:** validator/framework, package/Python versions, and one policy obligation.
- **Origin:** your own system, a maintainer-authored demo, or an agent-assisted trial.
  Note assistance received; reproducing our demo is not independent adoption.
- **Integration:** boolean or finding-based adapter; number of fault cases and controls.
- **Result:** a relevant survivor, regression, error, attribution gap, or no useful finding.
- **Follow-through:** did you change code/configuration, keep a regression case, and rerun it?
- **Friction:** what was unclear or blocked you? Time/LOC measurements are optional.

If timing, record setup/installation, adapter work, corpus authoring, and execution
separately, plus interruptions and assistance. Distinguish measured from estimated
values; an unmeasured field is unknown, not zero. Lines of code do not establish time savings.

## What we will learn from reports

Keep one record per trial, including unsuccessful attempts. Separate maintainer-run,
agent-assisted and independent engineer trials. Link the issue to a sanitized
before/after report and regression change where available. Do not merge scores from
different corpora or count repeated runs as new adopters.

The strongest signal is a relevant survivor that led to a code/configuration change
and remains in a regression suite. Useful secondary signals are first-report friction,
questions asked, and later reruns. Stars/downloads alone cannot establish that value.
