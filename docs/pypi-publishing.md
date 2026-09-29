# First PyPI publication

The alpha remains installable from [GitHub Releases](https://github.com/Mate4b/narrative-contracts/releases/tag/v0.1.0a2).
The new workflow publishes exactly the four original a2 wheel/sdist files, verified against
pinned SHA-256 hashes, rather than rebuilding different bytes under the same version.
Current benchmark and documentation additions live in the repository; the original a2
source archive retains the original release snapshot. Core/plugin code is unchanged.

At setup time both PyPI JSON endpoints returned 404. This is not a reservation or proof
that PyPI will permit either name. No project has been published by this workflow yet.

## One-time owner setup

Sign in to the intended owner account on [PyPI publishing settings](https://pypi.org/manage/account/publishing/).
Configure two **pending GitHub publishers**, one per package:

| Field | First publisher | Second publisher |
| --- | --- | --- |
| PyPI project name | `narrative-contracts` | `pytest-narrative-contracts` |
| Owner | `Mate4b` | `Mate4b` |
| Repository | `narrative-contracts` | `narrative-contracts` |
| Workflow filename | `publish-pypi.yml` | `publish-pypi.yml` |
| Environment name | `pypi` | `pypi` |

The account must meet PyPI's current verification/authentication requirements. No API token
needs to be shared or stored in GitHub. A pending publisher does not reserve the name and
only creates the project when publishing succeeds. See [PyPI's official setup guide](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/).

## Execution

From `main`, first run the **publish-existing-alpha-to-pypi** workflow with `publish=false`.
It downloads the existing release, checks pinned hashes and package metadata, installs the
wheels and runs the offline demonstration. It does not request PyPI publishing credentials.

Once both pending publishers exist, run it with `publish=true`. The publishing job uses the
`pypi` GitHub environment and short-lived OIDC credentials. `skip-existing` permits recovery
if one package uploads and the other fails; never change the pinned a2 bytes.

```sh
gh workflow run publish-pypi.yml --ref main -f publish=false
# After owner setup and the successful dry run:
gh workflow run publish-pypi.yml --ref main -f publish=true
```

After success, verify both PyPI project versions and file hashes, then install
`narrative-contracts==0.1.0a2` and `pytest-narrative-contracts==0.1.0a2` in a clean environment.
Only then change the README to advertise installation from PyPI. Packaging guidance:
[PyPA workflow guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/).
