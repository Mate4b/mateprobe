# Discovery and integration observations

> Historical evidence/reference from Narrative Contracts. The current project is
> **MateProbe by Mate4B**; see the [migration guide](migration-mateprobe.md).
> Original package names, versions and recorded results below identify that earlier work.

We ran two separate tasks with fresh-context `gpt-5.6-luna` agents: finding a tool
from a testing problem without a supplied package name, and integrating published
`0.1.0a3` from its public documentation. The criteria were recorded beforehand.
These are two maintainer-run observations, not a general agent success rate.

## Discovery: target not recommended

The search agent received a Python validator-auditing problem and a budget of
six queries and three candidate projects. It recommended `pytest-gremlins` and
also considered Hypothesis and mutmut. This records its choice; we did not run a
comparative evaluation of those libraries.

It performed four search calls with three unique formulations. The agent itself
included familiar product names in its queries and interpreted defect injection
largely as source mutation testing. The original first response was not saved;
a later repeat was captured instead. The three retained search responses do not
contain our URL, and the final recommendation does not name the library.

This is a negative recommendation observation with incomplete retrieval evidence.
It does not establish that the library is absent from a search index or that all
agents would miss it. A separate named/site-filter diagnostic also returned no
target result, while direct requests successfully retrieved the site, `llms.txt`,
sitemap and PyPI metadata. Direct accessibility and search discovery are different
properties. No task was silently rerun until a positive recommendation appeared.

## Integration: published a3 worked for the authored task

The second agent used `audit_validator` to wrap an inventory-allocation validator
without adopting `Document` or `Claim`. The supplied validator checked stock but
omitted a zone constraint. Its adapter preserved the actual finding IDs and
incomplete results, allowing exceptions to remain execution errors.

- Four agent-authored pytest tests passed.
- Twenty prewritten maintainer checks passed against unchanged consumer code.
- The zone fault survived before the fix and was detected afterward.
- Both the exact-stock and wording controls were preserved.
- Unrelated schema rejection, unknown state and exceptions remained distinct.
- Failed threshold checks still produced pytest JSON audit reports.

The full diagnostic corpus went from **1/5 to 2/5 targeted detections**, with
**2/2 controls preserved** and one identical-pair exclusion. It continues to fail
the full threshold. A separately named policy-only regression went from **1/2 to
2/2**, preserving both controls. The full corpus was not removed to make the
smaller regression appear universally successful.

The diagnostic cases deliberately assign targets to exercise accounting; their
labels are not independent evidence that missing or invalid stock constitutes a
specific stock-policy violation. The validator and missing rule were supplied
in the task. This is integration evidence, not discovery of an unknown real-world
bug, natural semantic accuracy, or independent developer adoption.

## Evidence and limits

The agent captured 19 public documentation files, their hashes and the site's
actual build revision. Those docs included the publicly linked historical trial;
the new conversation did not inherit its implementation context. Access restrictions
were instructions, not an OS sandbox. We retained the search capture failure and
all diagnostic gaps rather than treating the task as a clean end-to-end success.

[Frozen prompts, code, observations and replay](../benchmarks/agent-readiness/v2/README.md)
allow inspection of both tasks and offline repetition of the a3 integration checks.
CI replays the code; it does not regenerate an agent response or repeat web searches.
The [historical a2 integration](agent-adoption.md) remains a separate experiment.
