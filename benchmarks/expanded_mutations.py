"""Expanded, authored mutation campaign for the alpha contract rules.

This is an output-mutation audit.  The labels below are operator-intent labels,
not annotations inferred from the evaluator and not claims about natural prose.
Semantic challenges are deliberately retained as survivors or false positives
when the configured rule cannot justify a stronger conclusion.
"""

from __future__ import annotations

import argparse
import json
import unicodedata
from dataclasses import replace
from pathlib import Path
from typing import Any

from mateprobe import (
    Claim,
    Context,
    DeclaredClaimsConsistent,
    Document,
    ForbiddenPattern,
    LexicalRestatement,
    MinimumTokens,
    NoRepeatedText,
    RequiredFact,
    SettledPremise,
    StateChanged,
    Surface,
)
from mateprobe.model import plain
from mateprobe.mutations import (
    CampaignReport,
    MutationCase,
    Relation,
    Sample,
    Target,
    Validity,
    audit,
    replace_text,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "benchmarks" / "expanded-results"
SEED = 20260929

INVARIANT_RULES = (
    RequiredFact("required-status", "status", "pending"),
    DeclaredClaimsConsistent("branch-claims", ("outcome",)),
    StateChanged("advance", "current", "take", ("credits",)),
)

HEURISTIC_RULES = (
    MinimumTokens("lexical-floor", ("body", "outcome"), minimum=10, minimum_unique=6),
    LexicalRestatement("restatement", "label", "outcome"),
    ForbiddenPattern(
        "formula",
        (r"\bla reunion salio bien\b", r"\bthe meeting went well\b"),
        ("body", "outcome"),
    ),
    SettledPremise(
        "premise",
        (
            ("offer", r"te ofrecen otra vez el mismo contrato"),
            ("offer", r"they offer you the same contract again"),
        ),
        ("body",),
    ),
    NoRepeatedText("repeat", ("body",)),
)

RULES = INVARIANT_RULES + HEURISTIC_RULES

TARGET = {
    "required": Target("required-status", "REQUIRED_FACT", "state:current:status"),
    "missing_fact": Target("required-status", "FACT_UNAVAILABLE", "state:current:status"),
    "claim": Target("branch-claims", "CLAIM_STATE_MISMATCH", "outcome"),
    "state": Target("advance", "NO_DOMAIN_CHANGE", "transition:current->take"),
    "state_missing": Target("advance", "STATE_UNAVAILABLE", "transition:current->take"),
    "tokens": Target("lexical-floor", "LOW_LEXICAL_CONTENT", "body"),
    "restatement": Target("restatement", "LEXICAL_RESTATEMENT", "outcome"),
    "formula": Target("formula", "FORBIDDEN_PATTERN", "body"),
    "premise": Target("premise", "SETTLED_PREMISE_REOFFER", "body"),
    "repeat": Target("repeat", "REUSED_TEXT", "body"),
}

FAMILY_KIND = {
    "required_fact_type": "invariant",
    "required_fact_missing": "invariant",
    "branch_claim_mismatch": "invariant",
    "branch_claim_cross_scope": "invariant",
    "state_delta_removed": "invariant",
    "state_snapshot_missing": "invariant",
    "undeclared_contradiction": "invariant",
    "irrelevant_branch_fact": "invariant",
    "unicode_nfd": "heuristic",
    "accent_case_spacing_punctuation": "heuristic",
    "long_novel_expansion": "heuristic",
    "long_lexical_restatement": "heuristic",
    "literal_formula": "heuristic",
    "negated_formula_control": "heuristic",
    "formula_paraphrase": "heuristic",
    "literal_settled_premise": "heuristic",
    "premise_paraphrase": "heuristic",
    "exact_repeat": "heuristic",
    "paraphrase_repeat": "heuristic",
    "semantic_restatement": "heuristic",
    "equivalent_unicode_normalization": "heuristic",
    "not_applicable_semantics": "heuristic",
}


def _sample() -> Sample:
    body = (
        "La coordinadora escucha al cliente antes de revisar las notas y presentar "
        "los próximos pasos para resolver la situación pendiente con el equipo."
    )
    label = "Aceptar la propuesta formal"
    outcome = (
        "Firmás el acuerdo y recibís recursos adicionales para contratar dos especialistas "
        "que empezarán a trabajar con vos mañana."
    )
    previous = (
        "El guardia abre una puerta lateral mientras otra persona estudia los documentos "
        "que quedaron sobre la mesa durante toda la noche."
    )
    return Sample(
        Document(
            (
                Surface("body", body),
                Surface("label", label),
                Surface("outcome", outcome, "take", (Claim("decision", "accepted"),)),
            )
        ),
        Context(
            {
                "current": {"status": "pending", "credits": 50},
                "take": {"decision": "accepted", "credits": 60},
                "leave": {"decision": "declined", "credits": 50},
            },
            closed_premises=("offer",),
            history=(previous,),
        ),
    )


BASE = _sample()


def _case(
    family: str,
    variant: Sample,
    *,
    relation: Relation = Relation.PRESERVE,
    expected: tuple[Target, ...] = (),
    validity: Validity = Validity.VALID,
    provenance: str | None = None,
) -> MutationCase:
    if provenance is None:
        provenance = "Authored operator-intent label for the expanded synthetic campaign."
    return MutationCase(
        id=f"expanded/{family}",
        family=family,
        relation=relation,
        baseline=BASE,
        variant=variant,
        expected=expected,
        validity=validity,
        provenance=provenance,
        group="expanded-alpha",
    )


def _fault(family: str, variant: Sample, target: Target, provenance: str) -> MutationCase:
    return _case(
        family,
        variant,
        relation=Relation.VIOLATION,
        expected=(target,),
        provenance=provenance,
    )


def cases() -> tuple[MutationCase, ...]:
    """Return the fixed campaign corpus in stable order.

    Labels are intentionally written beside each mutation.  In particular,
    paraphrases and undeclared contradictions test documented guarantee
    boundaries and are expected to survive the current lexical/claim rules.
    """

    current = BASE.context.states["current"]
    take = BASE.context.states["take"]
    cases_: list[MutationCase] = []

    cases_.append(
        _fault(
            "required_fact_type",
            replace(
                BASE,
                context=replace(
                    BASE.context,
                    states={**BASE.context.states, "current": {**current, "status": True}},
                ),
            ),
            TARGET["required"],
            "The required status changes from string pending to boolean true; JSON scalar equality is type-sensitive.",
        )
    )
    # Keep the claim mutation explicit rather than relying on text parsing.
    surfaces = BASE.document.surfaces
    wrong_claim = replace(surfaces[-1], claims=(Claim("decision", "declined"),))
    cases_.append(
        _fault(
            "branch_claim_mismatch",
            replace(BASE, document=Document((*surfaces[:-1], wrong_claim))),
            TARGET["claim"],
            "The take branch explicitly declares declined while authoritative take facts say accepted.",
        )
    )
    cross_scope = replace(surfaces[-1], state_ref="leave")
    cases_.append(
        _fault(
            "branch_claim_cross_scope",
            replace(BASE, document=Document((*surfaces[:-1], cross_scope))),
            TARGET["claim"],
            "The accepted claim is evaluated against leave facts; branch scope must remain exact.",
        )
    )
    unchanged_take = {**take, "credits": 50}
    cases_.append(
        _fault(
            "state_delta_removed",
            replace(
                BASE,
                context=replace(
                    BASE.context, states={**BASE.context.states, "take": unchanged_take}
                ),
            ),
            TARGET["state"],
            "The projected credits key no longer changes from current to take.",
        )
    )
    missing_take = {"decision": "accepted"}
    cases_.append(
        _case(
            "state_snapshot_missing",
            replace(
                BASE,
                context=replace(BASE.context, states={**BASE.context.states, "take": missing_take}),
            ),
            relation=Relation.VIOLATION,
            expected=(TARGET["state_missing"],),
            validity=Validity.UNREVIEWED,
            provenance="Not applicable to detection scoring: the rule reports an undetermined missing snapshot, not a violated check.",
        )
    )
    cases_.append(
        _case(
            "irrelevant_branch_fact",
            replace(
                BASE,
                context=replace(
                    BASE.context,
                    states={
                        **BASE.context.states,
                        "leave": {"decision": "withdrawn", "credits": 51},
                    },
                ),
            ),
            provenance="Changing an unused leave-branch fact must not affect the current/take invariants or take claim.",
        )
    )
    undeclared = (
        "Rechazaste definitivamente la propuesta y no aceptaste ningún acuerdo durante "
        "esta conversación con las personas responsables del proyecto."
    )
    cases_.append(
        _fault(
            "undeclared_contradiction",
            replace_text(BASE, "outcome", undeclared),
            TARGET["claim"],
            "Operator intent says the prose contradicts the accepted outcome, but no claim changed; this is an explicit guarantee-boundary challenge.",
        )
    )

    body = BASE.document.surface("body").text
    outcome = BASE.document.surface("outcome").text
    cases_.extend(
        (
            _case(
                "unicode_nfd",
                replace_text(BASE, "body", unicodedata.normalize("NFD", body) + "  \n"),
                provenance="NFD accents, trailing spaces and a newline preserve the authored words.",
            ),
            _case(
                "accent_case_spacing_punctuation",
                replace_text(BASE, "body", "  " + body.upper().replace(".", "!..") + "  "),
                provenance="Case, accent-bearing letters, punctuation and surrounding whitespace are formatting changes.",
            ),
            _case(
                "long_novel_expansion",
                replace_text(
                    BASE,
                    "outcome",
                    outcome
                    + " Además, el equipo documenta cada decisión, coordina una revisión "
                    + "semanal y conserva los detalles para la próxima etapa del proyecto.",
                ),
                provenance="A long outcome adds several novel tokens and remains compatible with the accepted claim.",
            ),
            _fault(
                "long_lexical_restatement",
                replace_text(
                    BASE,
                    "outcome",
                    ("Aceptar la propuesta formal " * 35) + "mañana.",
                ),
                TARGET["restatement"],
                "A long target repeats the label vocabulary with one extra token; the lexical rule has no character-length escape.",
            ),
            _fault(
                "literal_formula",
                replace_text(BASE, "body", "La reunión salió bien. " + body),
                TARGET["formula"],
                "The configured forbidden phrase appears literally after Unicode accent folding.",
            ),
            _case(
                "negated_formula_control",
                replace_text(
                    BASE,
                    "body",
                    "Nadie dijo que la reunión salió bien: hubo desacuerdos concretos. " + body,
                ),
                provenance="Operator intent treats a negated/quoted formula as semantically safe; the phrase-only heuristic is expected to false-positive.",
            ),
            _fault(
                "formula_paraphrase",
                replace_text(
                    BASE,
                    "body",
                    "La conversación terminó de manera positiva, aunque esta frase evita la fórmula exacta. "
                    + body,
                ),
                TARGET["formula"],
                "Operator intent treats a paraphrase of the forbidden formula as a fault; this is a known phrase-recognizer blind spot.",
            ),
            _fault(
                "literal_settled_premise",
                replace_text(BASE, "body", "Te ofrecen otra vez el mismo contrato. " + body),
                TARGET["premise"],
                "The closed offer premise is reintroduced with the configured literal phrase.",
            ),
            _fault(
                "premise_paraphrase",
                replace_text(
                    BASE,
                    "body",
                    "La misma propuesta contractual vuelve a aparecer después de haber sido cerrada. "
                    + body,
                ),
                TARGET["premise"],
                "Operator intent treats a paraphrased re-offer as a fault; the configured premise recognizer is intentionally lexical.",
            ),
            _fault(
                "exact_repeat",
                replace_text(BASE, "body", BASE.context.history[0]),
                TARGET["repeat"],
                "The body is exactly the normalized token sequence supplied in history.",
            ),
            _fault(
                "paraphrase_repeat",
                replace_text(
                    BASE,
                    "body",
                    "Una persona vigila la entrada mientras alguien más examina papeles "
                    "dejados sobre la mesa durante la noche.",
                ),
                TARGET["repeat"],
                "Operator intent treats a semantic restatement of history as reuse; token-sequence matching is expected to miss it.",
            ),
            _fault(
                "semantic_restatement",
                replace_text(
                    BASE,
                    "outcome",
                    "Decidiste aceptar la oferta pendiente y confirmaste de forma afirmativa "
                    "la respuesta para esta conversación.",
                ),
                TARGET["restatement"],
                "Operator intent treats this paraphrase of the label/outcome repetition as a restatement; set overlap is expected to miss it.",
            ),
            _case(
                "equivalent_unicode_normalization",
                replace_text(BASE, "body", unicodedata.normalize("NFD", body) + "  "),
                validity=Validity.EQUIVALENT,
                provenance="Equivalent label: NFD spelling and spacing are outside the token-level semantic distinction used here.",
            ),
            _case(
                "not_applicable_semantics",
                replace_text(
                    BASE,
                    "body",
                    "El texto comunica una intención distinta y no tiene una etiqueta contractual.",
                ),
                validity=Validity.UNREVIEWED,
                provenance="Not applicable: arbitrary prose meaning is outside this synthetic contract corpus.",
            ),
        )
    )
    return tuple(cases_)


def _kind_report(report: CampaignReport, kind: str) -> dict[str, Any]:
    selected = tuple(c for c in report.cases if FAMILY_KIND[c.family] == kind)
    selected_report = CampaignReport(selected, report.corpus_digest)
    result = selected_report.summary()
    result["kind"] = kind
    result["scope"] = "invariant rules" if kind == "invariant" else "text heuristics"
    return result


def _summary(report: CampaignReport, corpus: tuple[MutationCase, ...]) -> dict[str, Any]:
    controls = [
        c for c in report.cases if c.relation == Relation.PRESERVE and c.outcome != "excluded"
    ]
    accepted_controls = sum(c.outcome == "preserved" for c in controls)
    return {
        "dataset": "expanded-synthetic-mutation-campaign-v1",
        "seed": SEED,
        "cases": len(corpus),
        "corpus_digest": report.corpus_digest,
        "combined": report.summary(),
        "by_kind": {
            "invariant": _kind_report(report, "invariant"),
            "heuristic": _kind_report(report, "heuristic"),
        },
        "controls": {
            "valid_controls": len(controls),
            "preserved_controls": accepted_controls,
            "preservation_rate": accepted_controls / len(controls) if controls else None,
            "always_reject_valid_variant_acceptance": 0.0,
            "note": "A reject-all validator cannot pass the nonempty valid-control gate.",
        },
        "label_policy": {
            "valid": "Transparent authored operator intent with provenance.",
            "equivalent": "Explicitly excluded because semantic equivalence is not inferred by audit().",
            "unreviewed": "Explicitly excluded as not applicable or ambiguous.",
            "semantic_challenges": "Paraphrase and undeclared-contradiction labels are synthetic scope challenges, not natural semantic accuracy claims.",
        },
    }


def write_campaign(output: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    corpus = cases()
    report = audit(corpus, RULES)
    output.mkdir(parents=True, exist_ok=True)
    summary = _summary(report, corpus)
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    (output / "campaign.json").write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n"
    )
    (output / "corpus.json").write_text(
        json.dumps({"seed": SEED, "cases": plain(corpus)}, ensure_ascii=False, indent=2) + "\n"
    )
    lines = [
        "# Expanded synthetic mutation campaign",
        "",
        "This authored campaign separates state invariants from text heuristics.",
        "It is not a natural-output semantic-accuracy study.",
        "",
        f"Corpus SHA-256: `{report.corpus_digest}`",
        "",
        "| Scope | Cases | Faults | Detected | Detection | Controls | Preserved | Preservation |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for kind in ("invariant", "heuristic"):
        data = summary["by_kind"][kind]
        lines.append(
            f"| {kind} | {data['total']} | {data['valid_faults']} | {data['detected_faults']} | "
            f"{data['detection_score']!s} | {data['valid_controls']} | {data['preserved_controls']} | "
            f"{data['preservation_rate']!s} |"
        )
    lines.extend(
        [
            "",
            "Survivors and false positives are retained as evidence about the configured guarantees.",
            "Equivalent and not-applicable/unreviewed labels are excluded from denominators.",
        ]
    )
    (output / "summary.md").write_text("\n".join(lines) + "\n")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(write_campaign(args.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
