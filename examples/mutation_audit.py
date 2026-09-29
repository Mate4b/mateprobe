"""A minimal mutation campaign with both faulty and valid variants."""

import json

from mateprobe import Context, Document, MinimumTokens, Surface
from mateprobe.mutations import (
    MutationCase,
    Relation,
    Sample,
    Target,
    Validity,
    audit,
    replace_text,
)

base = Sample(
    Document((Surface("body", "The coordinator hands you a signed agreement for review."),)),
    Context({}),
)
rules = (MinimumTokens("lexical-floor", ("body",), minimum=8, minimum_unique=5),)
cases = (
    MutationCase(
        "truncate",
        "truncation",
        Relation.VIOLATION,
        base,
        replace_text(base, "body", "Done."),
        (Target("lexical-floor", "LOW_LEXICAL_CONTENT", "body"),),
        Validity.VALID,
        "One token cannot satisfy the explicit eight-token minimum",
    ),
    MutationCase(
        "spacing",
        "whitespace",
        Relation.PRESERVE,
        base,
        replace_text(base, "body", "  " + base.document.surface("body").text + "\n"),
        validity=Validity.VALID,
        provenance="Spacing preserves tokens and their order",
    ),
)
report = audit(cases, rules)
report.assert_thresholds()
print(json.dumps(report.summary(), indent=2))
