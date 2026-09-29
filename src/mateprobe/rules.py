from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar

from .engine import Rule
from .model import Check, Context, Document, Kind, Scalar, Status, same, scalar
from .text import normalize, tokens

PASS, FAIL, UNKNOWN = Status.SATISFIED, Status.VIOLATED, Status.UNDETERMINED


@dataclass(frozen=True)
class RequiredFact(Rule):
    key: str
    expected: Scalar
    state_ref: str = "current"

    def __post_init__(self) -> None:
        scalar(self.expected)

    def evaluate(self, document: Document, context: Context) -> tuple[Check, ...]:
        facts = context.states.get(self.state_ref)
        scope = f"state:{self.state_ref}:{self.key}"
        if facts is None or self.key not in facts:
            return (self.result(UNKNOWN, "FACT_UNAVAILABLE", scope, "Required fact is missing"),)
        actual = facts[self.key]
        return (
            self.result(
                PASS if same(actual, self.expected) else FAIL,
                "REQUIRED_FACT",
                scope,
                f"Expected {self.expected!r}; observed {actual!r}",
            ),
        )


@dataclass(frozen=True)
class DeclaredClaimsConsistent(Rule):
    """Checks declarations against their OWN branch. Does not parse arbitrary prose."""

    surface_ids: tuple[str, ...] = ()
    require_claims: bool = True

    def evaluate(self, document: Document, context: Context) -> tuple[Check, ...]:
        ids = self.surface_ids or tuple(s.id for s in document.surfaces)
        checks = []
        for sid in ids:
            surface = document.surface(sid)
            facts = context.states.get(surface.state_ref)
            if not surface.claims:
                checks.append(
                    self.result(
                        UNKNOWN if self.require_claims else PASS,
                        "CLAIMS_ABSENT",
                        sid,
                        "No declared claims; text truthfulness is not verified",
                    )
                )
            for claim in surface.claims:
                if facts is None or claim.key not in facts:
                    checks.append(
                        self.result(
                            UNKNOWN,
                            "CLAIM_UNAVAILABLE",
                            sid,
                            f"{claim.key} absent in {surface.state_ref}",
                        )
                    )
                else:
                    checks.append(
                        self.result(
                            PASS if same(facts[claim.key], claim.value) else FAIL,
                            "CLAIM_STATE_MISMATCH",
                            sid,
                            f"{claim.key} declared {claim.value!r}; "
                            f"{surface.state_ref} has {facts[claim.key]!r}",
                        )
                    )
        return tuple(checks)


@dataclass(frozen=True)
class StateChanged(Rule):
    before: str
    after: str
    keys: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.keys:
            raise ValueError("StateChanged requires an explicit domain projection")

    def evaluate(self, document: Document, context: Context) -> tuple[Check, ...]:
        a, b = context.states.get(self.before), context.states.get(self.after)
        scope = f"transition:{self.before}->{self.after}"
        if a is None or b is None or any(k not in a or k not in b for k in self.keys):
            return (
                self.result(
                    UNKNOWN,
                    "STATE_UNAVAILABLE",
                    scope,
                    "Both snapshots must contain every projected key",
                ),
            )
        changed = [k for k in self.keys if not same(a[k], b[k])]
        return (
            self.result(
                PASS if changed else FAIL,
                "NO_DOMAIN_CHANGE",
                scope,
                f"Changed domain keys: {changed}",
                changed_keys=len(changed),
            ),
        )


@dataclass(frozen=True)
class MinimumTokens(Rule):
    surface_ids: tuple[str, ...]
    minimum: int = 10
    minimum_unique: int = 6
    kind: ClassVar[Kind] = Kind.HEURISTIC

    def __post_init__(self) -> None:
        if not self.surface_ids or self.minimum < 1 or not 1 <= self.minimum_unique <= self.minimum:
            raise ValueError("MinimumTokens needs surfaces and 1 <= minimum_unique <= minimum")

    def evaluate(self, document: Document, context: Context) -> tuple[Check, ...]:
        checks = []
        for sid in self.surface_ids:
            words = tokens(document.surface(sid).text)
            good = len(words) >= self.minimum and len(set(words)) >= self.minimum_unique
            checks.append(
                self.result(
                    PASS if good else FAIL,
                    "LOW_LEXICAL_CONTENT",
                    sid,
                    "Token count and diversity are proxies, not scene quality",
                    tokens=len(words),
                    unique_tokens=len(set(words)),
                )
            )
        return tuple(checks)


@dataclass(frozen=True)
class LexicalRestatement(Rule):
    source: str
    target: str
    overlap_threshold: float = 0.7
    minimum_novel_tokens: int = 4
    kind: ClassVar[Kind] = Kind.HEURISTIC

    def __post_init__(self) -> None:
        if not 0 <= self.overlap_threshold <= 1 or self.minimum_novel_tokens < 1:
            raise ValueError("Invalid lexical restatement thresholds")

    def evaluate(self, document: Document, context: Context) -> tuple[Check, ...]:
        source = set(tokens(document.surface(self.source).text))
        target = set(tokens(document.surface(self.target).text))
        if not source:
            return (self.result(UNKNOWN, "SOURCE_EMPTY", self.target, "Source has no word tokens"),)
        overlap = len(source & target) / len(source)
        novel = len(target - source)
        reject = overlap > self.overlap_threshold and novel < self.minimum_novel_tokens
        return (
            self.result(
                FAIL if reject else PASS,
                "LEXICAL_RESTATEMENT",
                self.target,
                "High lexical reuse with little lexical novelty; no character cutoff",
                overlap=overlap,
                novel_tokens=novel,
            ),
        )


@dataclass(frozen=True)
class ForbiddenPattern(Rule):
    patterns: tuple[str, ...]
    surface_ids: tuple[str, ...]
    fold_accents: bool = True
    kind: ClassVar[Kind] = Kind.HEURISTIC

    def __post_init__(self) -> None:
        if not self.patterns or not self.surface_ids:
            raise ValueError("Patterns and surfaces are required")
        for pattern in self.patterns:
            if not pattern:
                raise ValueError("Empty patterns are invalid")
            re.compile(pattern, re.IGNORECASE)

    def evaluate(self, document: Document, context: Context) -> tuple[Check, ...]:
        checks = []
        for sid in self.surface_ids:
            text = normalize(document.surface(sid).text, self.fold_accents)
            match = next(
                (m for p in self.patterns if (m := re.search(p, text, re.IGNORECASE))), None
            )
            checks.append(
                self.result(
                    FAIL if match else PASS,
                    "FORBIDDEN_PATTERN",
                    sid,
                    f"Normalized match: {match.group()!r}"
                    if match
                    else "No configured phrase matched; paraphrases may escape",
                )
            )
        return tuple(checks)


@dataclass(frozen=True)
class SettledPremise(Rule):
    patterns: tuple[tuple[str, str], ...]
    surface_ids: tuple[str, ...]
    kind: ClassVar[Kind] = Kind.HEURISTIC

    def __post_init__(self) -> None:
        if not self.surface_ids or any(not key or not pattern for key, pattern in self.patterns):
            raise ValueError("Premise patterns need ids, patterns and surfaces")
        for _, pattern in self.patterns:
            re.compile(pattern, re.IGNORECASE)

    def evaluate(self, document: Document, context: Context) -> tuple[Check, ...]:
        checks = []
        for premise in context.closed_premises:
            patterns = tuple(pattern for key, pattern in self.patterns if key == premise)
            if not patterns:
                checks.append(
                    self.result(
                        UNKNOWN,
                        "PREMISE_UNSUPPORTED",
                        "$",
                        f"No phrase recognizer for closed premise {premise}",
                    )
                )
                continue
            for sid in self.surface_ids:
                text = normalize(document.surface(sid).text, True)
                hit = any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)
                checks.append(
                    self.result(
                        FAIL if hit else PASS,
                        "SETTLED_PREMISE_REOFFER",
                        sid,
                        f"Closed premise {premise}; lexical match={hit}",
                    )
                )
        return tuple(checks) or (
            self.result(PASS, "NO_CLOSED_PREMISES", "$", "No closed premises supplied"),
        )


@dataclass(frozen=True)
class NoRepeatedText(Rule):
    surface_ids: tuple[str, ...]
    kind: ClassVar[Kind] = Kind.HEURISTIC

    def evaluate(self, document: Document, context: Context) -> tuple[Check, ...]:
        previous = {" ".join(tokens(text)) for text in context.history}
        return tuple(
            self.result(
                FAIL if " ".join(tokens(document.surface(sid).text)) in previous else PASS,
                "REUSED_TEXT",
                sid,
                "Compared normalized token sequences to supplied history",
            )
            for sid in self.surface_ids
        )
