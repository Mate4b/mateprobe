# Problem-driven discovery and a3 integration trials

Two separate fresh-context `gpt-5.6-luna` agents performed one task each. These
are maintainer-run usability observations, not independent validation or estimates
of recommendation frequency. The protocol and reviewer checks were saved and hashed
before reading the respective submissions. Access restrictions were instructions,
not an operating-system sandbox.

## Discovery observation

The discovery agent received an existing-validator testing problem without the
target package name or URL. It recommended **pytest-gremlins**, with Hypothesis and
mutmut as other candidates. This records the agent's choice, not an endorsement
or a controlled comparison of those products with Narrative Contracts.

The agent performed four search calls with three unique query formulations. It
seeded the first two queries with familiar tool names and favored source mutation
testing. The task's distinction between mutating validator code and supplying
faulty input variants was not experimentally controlled. Candidate anchoring and
task interpretation may therefore have affected the result.

The original first search response was not saved. A later repeat response was
stored under `01-query.json`; it must not be treated as the original response.
No target URL appears in the three retained search responses, and the final
recommendation does not name the target. Presence in **all** responses is unknown.
See `discovery/capture-notes.md.txt` and `discovery-result.json`.

A separate maintainer diagnostic searched using the target name and a site filter.
It also returned no target result in the captured combined tool response. This is
not part of the blinded agent trial and does not prove absence from an index.
Direct HTTP checks returned 200 for the site, `llms.txt`, sitemap and PyPI JSON;
the homepage had a matching canonical URL and no observed `noindex` directive.
The root `robots.txt` returned 404. Accessibility is distinct from search discovery.

The public archive contains queries, titles, URLs, hashes and observed choices.
Third-party article/page bodies from the search tool remain outside the repository.
Search results are time-dependent; replaying this archive does not rerun a search.

## Integration observation

The other agent started from public `llms.txt`, installed the two published a3
packages and implemented a new inventory-allocation audit. It downloaded 19
documentation files with verified hashes and the actual site's build metadata.
The docs revision was `27ab960c6c3b3d3931221e6b335526d3f3b21947`, later than the
repository revision recorded when the protocol was frozen. The captured bytes
are the actual inputs. Public documentation linked the earlier a2 trial, which
the agent also downloaded; this was not a documentation-naive trial.

The agent's four tests passed. Twenty prewritten maintainer checks passed against
its unchanged implementation. Before the authored zone check was added, the
wrong-zone case survived; after the fix it was detected.

| Campaign | Before targeted detections | After targeted detections | Controls preserved |
|---|---|---|---|
| Full eight-case diagnostic corpus | 1/5 | 2/5 | 2/2 |
| Named four-case policy subset | 1/2 | 2/2 | 2/2 |

The full corpus still contains one unattributed schema rejection, one unknown,
one execution error and one identical-pair exclusion. Full-corpus thresholds fail
both before and after. The smaller policy regression passes only after the zone
fix. A declared `idempotency` obligation remains untested; the consumer described
it as validation stability, not evidence about backend operation idempotency.

The three diagnostic target assignments deliberately exercise accounting. They
are not independently established stock-policy violations. Labels and the buggy
validator were supplied in the task; this is not a previously unknown production
bug discovery. No result establishes prose truthfulness or general policy coverage.

## Files and replay

- `protocol.json`, `freeze.json`: pre-trial criteria and their timestamp/hash.
- `reviewer-freeze.json`: hash of checks authored before reading the submission.
- `discovery/`: normalized agent trace, prompt, capture notes and named diagnostic.
- `integration/submission/`: original consumer/test code as `.py.txt`, logs and reports.
- `integration/docs/`: byte-preserved public docs, with Markdown stored as `.md.txt`.
- `integration/doc-captures.json`: URL-to-file hash mapping.
- `integration/reviewer_checks.py.txt`: additional maintainer checks.
- `summary.json`, `manifest.json`: outcomes, limitations, redactions and artifact hashes.

One machine-specific workspace prefix in the submitted command log was redacted;
code and document bytes were not changed. Original private logs remain outside
the public repository. No consumer implementation repair was made by the maintainer.

Create a separate Python 3.11+ environment and install:

```sh
python -m pip install narrative-contracts==0.1.0a3 pytest-narrative-contracts==0.1.0a3
```

From the repository, using that environment's interpreter:

```sh
python benchmarks/replay_agent_readiness.py --output /tmp/a3-agent-readiness
```

The output directory must be new. Replay verifies artifact hashes and runs the
four submitted tests plus twenty reviewer checks using the installed packages.
It makes no generation-model calls and does not rerun the discovery agent. Keep
the historical a2 trial and its separately pinned replay unchanged.
