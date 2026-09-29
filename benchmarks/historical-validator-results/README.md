# Historical evidence: read the final and initial results together

The final compatibility run is `compatibility-followup-v2/evaluation/summary.json`:
three reproduced historical fixes across two packages and one non-reproduction.
There are four issue comparisons, eight changed pairs, and two versions per issue.
These are independently originated reports reproduced by this project's authors,
not independent users of Narrative Contracts or newly discovered defects.

- `preflight-v1/`: flawed initial preparation preserved for transparency; not results.
- `prepared-v2-bootstrap/`: preparation before the macOS venv bootstrap correction.
- `prepared/`: original executed inputs, adapter and protocol snapshots.
- `captured/` and `evaluation/`: original run, with one reproduced fix, unavailable
  jsonschema 4.17.2, missing pkg_resources in old versions and the unchanged IDN case.
- `compatibility-followup/`: first compatibility run; a conflicting setuptools pin
  prevented two environments from installing. Other results and the driver are retained.
- `compatibility-followup-v2/`: corrected, pinned dependency environments, raw
  outcomes, artifact hashes, locks, and final replay results. Case labels and inputs
  were never changed to improve results after the original package execution.

The initial screening ledger is purposive, with ten candidates and six exclusions.
Null versions on excluded entries mean a validation-fix pair was not established.
Preflight-v1 guesses must not be used as established release information.

See [the study](../../docs/validator-study.md), [screening protocol](../../paper/historical-validator-protocol.md)
and [follow-up deviations](../../paper/historical-followup-protocol.md). Reproduction
commands distinguish offline replay from package downloads and fresh execution.
No package installations or inference calls are needed for CI replay. The original
and final runs are checked byte-for-byte by the test suite; the intermediate
compatibility run is an archived failed setup attempt, not the recommended entrypoint.
