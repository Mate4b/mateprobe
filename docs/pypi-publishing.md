# PyPI publication and recovery

## Current release: 0.1.0a3

Both packages are published on PyPI at **0.1.0a3**:

```sh
python -m pip install narrative-contracts==0.1.0a3 pytest-narrative-contracts==0.1.0a3
```

[GitHub release](https://github.com/Mate4b/narrative-contracts/releases/tag/v0.1.0a3) ·
[Successful Trusted Publishing run](https://github.com/Mate4b/narrative-contracts/actions/runs/36627528644).

All four PyPI wheel/sdist hashes match the release manifest. Both built artifact
formats passed clean-install checks; a separate environment installed the published
packages directly from PyPI and exercised a3 audits, pytest, examples and CLI.
See [a3 verification](pypi-a3-verification.json) and the
[pinned artifact manifest](../scripts/release-a3.json).

The release artifacts come from commit `980c78f25771cfd408f7b2e2eece548396d063e6`.
Later documentation and publishing metadata do not rebuild those versioned bytes.
The workflow supports `version=0.1.0a3` (default) or the historical `0.1.0a2`.
Use `publish=false` to verify without uploading. `package=core|plugin|both` supports
recovery; existing files are never replaced.

```sh
gh workflow run publish-pypi.yml --repo Mate4b/narrative-contracts --ref main -f publish=false -f version=0.1.0a3
```

## Historical release: 0.1.0a2

The original a2 packages remain available:

- [narrative-contracts](https://pypi.org/project/narrative-contracts/0.1.0a2/)
- [pytest-narrative-contracts](https://pypi.org/project/pytest-narrative-contracts/0.1.0a2/)

```sh
python -m pip install narrative-contracts==0.1.0a2 pytest-narrative-contracts==0.1.0a2
```

Downloaded wheel and sdist bytes match all four original GitHub release SHA-256 hashes.
A fresh Python 3.12 environment installed both packages solely from PyPI, auto-discovered
the pytest plugin, passed its fixture/report smoke test, and ran the offline demo and CLI.
See [machine-readable verification](pypi-verification.json).

## Publication evidence

- [Successful core publication](https://github.com/Mate4b/narrative-contracts/actions/runs/36615827807).
- [Successful plugin publication](https://github.com/Mate4b/narrative-contracts/actions/runs/36616326251).
- [Original partial attempt and retry](https://github.com/Mate4b/narrative-contracts/actions/runs/36615296267):
  the core wheel uploaded, then PyPI rejected creation of the plugin because its pending
  publisher had not been configured. The owner supplied the account page confirming that
  absence. Core completion was isolated, the plugin publisher was added, and its upload succeeded.

The workflow publishes exactly the four original a2 files from
[GitHub Releases](https://github.com/Mate4b/narrative-contracts/releases/tag/v0.1.0a2), verified
against pinned hashes, rather than rebuilding different bytes under the same version.
Their original metadata retains pre-transfer repository URLs, which redirect to `Mate4b`.
Current benchmark/documentation additions live in the repository; the original source
archive retains the original release snapshot. Future metadata changes require a new release.

## Active publisher bindings

These are existing project publishers now, not pending publishers. Manage them in each
project's PyPI publishing settings if the repository or workflow identity changes:

| Field | Core | Plugin |
| --- | --- | --- |
| PyPI project | `narrative-contracts` | `pytest-narrative-contracts` |
| GitHub owner | `Mate4b` | `Mate4b` |
| Repository | `narrative-contracts` | `narrative-contracts` |
| Workflow filename | `publish-pypi.yml` | `publish-pypi.yml` |
| Environment name | `pypi` | `pypi` |

GitHub organization ownership and PyPI project ownership are separate. The binding authorizes
this workflow to upload; it does not itself establish a PyPI organization account. No API
token is stored in GitHub. See [PyPI Trusted Publishing documentation](https://docs.pypi.org/trusted-publishers/).

## Re-running the existing a2 publication

From `main`, run **publish-verified-alpha-to-pypi** with `version=0.1.0a2` and `publish=false` for a dry run.
It checks original hashes and metadata, installs wheels and runs the demo. Uploads use the
`pypi` environment and short-lived OIDC credentials. Each package is handled separately;
`skip-existing` supports recovery without replacing existing files. The package selector
accepts `both`, `core`, or `plugin`.

```sh
gh workflow run publish-pypi.yml --repo Mate4b/narrative-contracts --ref main -f publish=false -f version=0.1.0a2
# Only if recovering a missing plugin upload:
gh workflow run publish-pypi.yml --repo Mate4b/narrative-contracts --ref main -f publish=true -f version=0.1.0a2 -f package=plugin
```

All a2 files are already published. The a2 path stays pinned to its original hashes;
the a3 path uses its separate committed manifest. Future releases need new versioned
artifacts and hashes. Do not overwrite or rebuild a published version in place.
