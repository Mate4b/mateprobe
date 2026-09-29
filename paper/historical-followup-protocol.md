# Historical compatibility follow-up protocol

Prepared after the first historical run and before executing this follow-up.
This is explicitly exploratory compatibility recovery, not a preplanned success.
Original ledger, inputs, failures and results remain available unchanged.

The first run reproduced the uppercase FILE-scheme fix, but both jsonschema 3.0.x
versions failed importing pkg_resources, jsonschema 4.17.2 was unavailable from the
package index, and the chosen IDN email was accepted by both Marshmallow versions.

Two changes are fixed in advance of the new run:

1. Add setuptools 70.3.0 (which supplies pkg_resources) to both jsonschema 3.0.x
   environments. Keep all other captured dependencies pinned.
2. Use jsonschema 4.17.1 as the available predecessor to 4.17.3. Issue #1018 describes
   the regression starting in 4.16.0; the pinned changelog associates the fix with
   4.17.3. This is not evidence about the unavailable 4.17.2 package.

All eight paired inputs, labels, policies and adapters remain identical. The IDN
case is rerun unchanged; no search for a different successful reproducer is made.
The same two Marshmallow version comparisons act as checks on repeat execution.

The follow-up driver, base collector, protocol, dependency requirements and parent
capture identity are frozen before new collection. The driver hash is included in
the prepared inputs; requirements hashes are verified before installing. Actual
installation reports retain artifact URLs and hashes, along with pip-freeze locks.
Offline replay and fresh package execution are distinct operations. Both the
initial and follow-up tables must be reported, including failed reproduction.

A successful reproduction requires the issue-triggering outcome to change from
incorrect to correct and the preservation control to pass in both versions.
A fixed example is a historical regression reproduced, not a newly discovered bug,
an external adopter, or evidence of a sensitivity advantage over detailed pytest.
