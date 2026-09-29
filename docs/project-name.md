# MateProbe and published package names

**MateProbe** is the project name, formerly Narrative Contracts. The paper,
site title and current usage guides use MateProbe. The released a3 artifacts
retain their original installation and API identifiers:

| Surface | Published alpha 0.1.0a3 identifier |
|---|---|
| Project / paper | MateProbe |
| Core distribution | `narrative-contracts` |
| Optional pytest distribution | `pytest-narrative-contracts` |
| Python import | `narrative_contracts` |
| CLI | `narrative-contracts` |
| Pytest fixture / report flag | `narrative` / `--narrative-report` |
| Current repository | [Mate4b/narrative-contracts](https://github.com/Mate4b/narrative-contracts) |

```sh
python -m pip install narrative-contracts==0.1.0a3 pytest-narrative-contracts==0.1.0a3
```

```python
from narrative_contracts.validator_audit import audit_validator
```

The name change does not alter rule semantics or the published artifact bytes.
Historical protocols, captured source files and reports retain the original name
and hashes so they can still be reproduced. A future change to distribution names,
import paths or repository location requires a new compatibility-verified migration;
no `mateprobe` distribution or import is provided by the a3 wheels above.
