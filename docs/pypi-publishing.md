# Packages and verification

## MateProbe 0.1.0a4

The project is now **MateProbe by Mate4B**. The renamed distributions are
`mateprobe` and `pytest-mateprobe`, version `0.1.0a4`. See the
[migration guide](migration-mateprobe.md) and [current API](api-a4.md).
The historical verification records below apply to their original distributions.


## Historical release: Narrative Contracts 0.1.0a3

```sh
python -m pip install narrative-contracts==0.1.0a3 pytest-narrative-contracts==0.1.0a3
```

Python 3.11+ is required; the pytest plugin is optional. The independent validator
audit and state-field bindings are available in a3. See [the historical API index](api-a3.md)
and [first audit recipe](first-audit.md).

[PyPI core](https://pypi.org/project/narrative-contracts/0.1.0a3/) ·
[PyPI plugin](https://pypi.org/project/pytest-narrative-contracts/0.1.0a3/) ·
[GitHub release](https://github.com/Mate4b/narrative-contracts/releases/tag/v0.1.0a3).

All four PyPI wheel/sdist hashes match the release manifest. Both built artifact
formats passed clean-install checks; a separate environment installed the published
packages directly from PyPI and exercised a3 audits, pytest, examples and CLI.
See [machine-readable verification](pypi-a3-verification.json), the
[pinned artifact manifest](../scripts/release-a3.json), and the
[publication run](https://github.com/Mate4b/narrative-contracts/actions/runs/36627528644).

The release artifacts come from commit `980c78f25771cfd408f7b2e2eece548396d063e6`.
Later repository documentation does not change those versioned bytes. Retain the
package version, corpus, validator configuration and dependency versions when
reproducing a report. Repository metadata alone does not prove which code ran.

## Historical release: 0.1.0a2

The original a2 packages remain available for reproducing earlier experiments.
They do not contain the independent audit or state-binding APIs introduced in a3.

Downloaded wheel/sdist bytes matched all four original GitHub release hashes.
A clean Python 3.12 environment installed both packages from PyPI, discovered the
pytest plugin and ran the fixture/report smoke test, offline demo and CLI.

[Historical verification](pypi-verification.json) ·
[Original release](https://github.com/Mate4b/narrative-contracts/releases/tag/v0.1.0a2) ·
[Core publication](https://github.com/Mate4b/narrative-contracts/actions/runs/36615827807) ·
[Plugin publication](https://github.com/Mate4b/narrative-contracts/actions/runs/36616326251).

Historical artifacts are preserved rather than rebuilt under an existing version.
Their original repository URLs may redirect to the current organization.
