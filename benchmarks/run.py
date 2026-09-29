"""Reproducible synthetic feasibility benchmark. Not a natural-output LLM study."""

from __future__ import annotations

import argparse
import json
import platform
import random
import re
import statistics
import sys
import unicodedata
from dataclasses import replace
from pathlib import Path
from time import perf_counter_ns

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
    evaluate,
)
from mateprobe.model import plain
from mateprobe.mutations import (
    MutationCase,
    Relation,
    Sample,
    Target,
    Validity,
    audit,
    replace_text,
)

RULES = (
    RequiredFact("fact", "status", "pending"),
    DeclaredClaimsConsistent("claims", ("outcome",)),
    StateChanged("advance", "current", "take", ("credits",)),
    MinimumTokens("thin", ("body", "outcome"), 8, 5),
    LexicalRestatement("restatement", "label", "outcome"),
    ForbiddenPattern(
        "formula", (r"\bla reunion salio bien\b", r"\bthe meeting went well\b"), ("body", "outcome")
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


def dataset(seed=1729, variants=8):
    rng = random.Random(seed)
    cases = []
    for domain in ("employment", "customer_support", "interactive_fiction"):
        for language in ("es", "en"):
            for i in range(variants):
                credits = rng.randint(20, 200)
                group = f"{domain}/{language}/{i}"
                es = language == "es"
                subject = {
                    "employment": ("equipo", "team"),
                    "customer_support": ("cliente", "customer"),
                    "interactive_fiction": ("viajero", "traveler"),
                }[domain][not es]
                body = (
                    f"La coordinadora escucha al {subject} antes de revisar las notas "
                    "y presentar los próximos pasos para resolver la situación pendiente."
                    if es
                    else f"The coordinator listens to the {subject} before reviewing "
                    "the notes and presenting the next steps to resolve the pending situation."
                )
                label = "Aceptar la propuesta formal" if es else "Accept the formal proposal"
                outcome = (
                    "Firmás el acuerdo y recibís recursos adicionales para contratar "
                    "dos especialistas que empezarán a trabajar con vos mañana."
                    if es
                    else "You sign an agreement and receive additional resources "
                    "to hire two specialists who will start working with you tomorrow."
                )
                previous = (
                    "El guardia abre una puerta lateral mientras otra persona observa "
                    "los documentos que quedaron sobre la mesa durante toda la noche."
                    if es
                    else "The guard opens a side door while another person studies "
                    "the documents that remained on the table throughout the night."
                )
                base = Sample(
                    Document(
                        (
                            Surface("body", body),
                            Surface("label", label),
                            Surface("outcome", outcome, "take", (Claim("decision", "accepted"),)),
                        )
                    ),
                    Context(
                        {
                            "current": {"status": "pending", "credits": credits},
                            "take": {"decision": "accepted", "credits": credits + 10},
                            "leave": {"decision": "declined", "credits": credits},
                        },
                        ("offer",),
                        (previous,),
                    ),
                )

                def add(family, variant, target=None, challenge=False):
                    cases.append(
                        MutationCase(
                            f"{group}/{family}",
                            family,
                            Relation.VIOLATION if target else Relation.PRESERVE,
                            base,
                            variant,
                            (target,) if target else (),
                            Validity.VALID,
                            (
                                "Author-labelled scope challenge; not independently human-adjudicated. "
                                if challenge
                                else "Synthetic construction with known transformation. "
                            )
                            + family,
                            group,
                        )
                    )

                add(
                    "token_spam",
                    replace_text(base, "body", "a" * 70),
                    Target("thin", "LOW_LEXICAL_CONTENT", "body"),
                )
                add(
                    "padding_restatement",
                    replace_text(base, "outcome", label + ". " + "x" * 130),
                    Target("restatement", "LEXICAL_RESTATEMENT", "outcome"),
                )
                states = plain(base.context.states)
                states["take"]["credits"] = credits
                add(
                    "zero_domain_delta",
                    replace(base, context=replace(base.context, states=states)),
                    Target("advance", "NO_DOMAIN_CHANGE", "transition:current->take"),
                )
                surfaces = base.document.surfaces
                swapped = replace(surfaces[-1], claims=(Claim("decision", "declined"),))
                add(
                    "cross_branch_claim",
                    replace(base, document=Document((*surfaces[:-1], swapped))),
                    Target("claims", "CLAIM_STATE_MISMATCH", "outcome"),
                )
                phrase = (
                    "La reunion salio bien. " if es else "Ｔｈｅ ｍｅｅｔｉｎｇ ｗｅｎｔ ｗｅｌｌ. "
                )
                add(
                    "unicode_formula",
                    replace_text(base, "outcome", phrase + outcome),
                    Target("formula", "FORBIDDEN_PATTERN", "outcome"),
                )
                offer = (
                    "Te ofrecen otra vez el mismo contrato. "
                    if es
                    else "They offer you the same contract again. "
                )
                add(
                    "closed_premise",
                    replace_text(base, "body", offer + body),
                    Target("premise", "SETTLED_PREMISE_REOFFER", "body"),
                )
                add(
                    "repeated_scene",
                    replace_text(base, "body", previous),
                    Target("repeat", "REUSED_TEXT", "body"),
                )
                states = plain(base.context.states)
                states["current"]["status"] = "cancelled"
                add(
                    "required_fact",
                    replace(base, context=replace(base.context, states=states)),
                    Target("fact", "REQUIRED_FACT", "state:current:status"),
                )
                paraphrase = (
                    "Decidiste dar el sí a aquella oferta que estaba pendiente "
                    "desde antes de esta conversación y confirmaste tu respuesta afirmativa."
                    if es
                    else "You chose to say yes to that offer which had been "
                    "waiting since before this conversation and confirmed your affirmative answer."
                )
                add(
                    "challenge_semantic_restatement",
                    replace_text(base, "outcome", paraphrase),
                    Target("restatement", "LEXICAL_RESTATEMENT", "outcome"),
                    True,
                )
                contradiction = (
                    "Rechazaste definitivamente la propuesta y no aceptaste ningún "
                    "acuerdo durante esta conversación con las personas responsables del proyecto."
                    if es
                    else "You definitively rejected that proposal and did not "
                    "accept any agreement during this conversation with those responsible for it."
                )
                add(
                    "challenge_undeclared_contradiction",
                    replace_text(base, "outcome", contradiction),
                    Target("claims", "CLAIM_STATE_MISMATCH", "outcome"),
                    True,
                )
                add("whitespace", replace_text(base, "body", "  " + body + "\n"))
                add(
                    "unicode_nfd",
                    replace_text(base, "body", unicodedata.normalize("NFD", body) + " "),
                )
                add("case_change", replace_text(base, "body", body.upper()))
                expanded = outcome + (
                    " Los detalles quedan registrados."
                    if es
                    else " The details are recorded for future reference."
                )
                add("valid_expansion", replace_text(base, "outcome", expanded))
                negation = (
                    "Nadie dijo que la reunión salió bien: hubo desacuerdos concretos. "
                    if es
                    else "Nobody said the meeting went well: there were clear disagreements. "
                )
                add(
                    "challenge_negated_formula",
                    replace_text(base, "body", negation + body),
                    challenge=True,
                )
    return tuple(cases)


def excerpt_baseline(sample):
    """Adapted lexical/state predicates, NOT the complete LifeCard pipeline."""
    d = sample.document
    body, outcome, label = (d.surface(s).text for s in ("body", "outcome", "label"))
    if sample.context.states["current"]["status"] != "pending":
        return False
    if len(body.strip()) < 70 or len(outcome.strip()) < 60:
        return False
    source = set(re.findall(r"\w+", label.lower()))
    target = set(re.findall(r"\w+", outcome.lower()))
    if len(outcome.strip()) < 90 and len(source & target) / len(source) > 0.7:
        return False
    if re.search(r"la reunión salió bien|the meeting went well", body + " " + outcome, re.I):
        return False
    if re.search(
        r"te ofrecen otra vez el mismo contrato|they offer you the same contract again", body, re.I
    ):
        return False
    return True


def binary_metrics(cases, accept):
    tp = fn = fp = tn = errors = 0
    baseline_rejections = 0
    for case in cases:
        try:
            baseline_rejections += not accept(case.baseline)
            rejected = not accept(case.variant)
        except Exception:
            errors += 1
            continue
        if case.relation == Relation.VIOLATION:
            tp += rejected
            fn += not rejected
        else:
            fp += rejected
            tn += not rejected
    return {
        "tp": tp,
        "fn": fn,
        "fp": fp,
        "tn": tn,
        "errors": errors,
        "baseline_rejections": baseline_rejections,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "valid_variant_acceptance": tn / (tn + fp) if tn + fp else None,
    }


def render_table(metrics):
    rows = [
        "| Validator | TP | FN | FP | TN | Precision | Recall | Valid acceptance |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    def percentage(value):
        return "n/a" if value is None else f"{100 * value:.1f}%"

    for name, m in metrics.items():
        rows.append(
            f"| {name} | {m['tp']} | {m['fn']} | {m['fp']} | {m['tn']} | "
            f"{percentage(m['precision'])} | {percentage(m['recall'])} | "
            f"{percentage(m['valid_variant_acceptance'])} |"
        )
    return "\n".join(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("benchmarks/results"))
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--variants", type=int, default=8)
    args = parser.parse_args()
    if args.variants < 1:
        parser.error("--variants must be positive")
    args.output.mkdir(parents=True, exist_ok=True)
    cases = dataset(args.seed, args.variants)
    campaign = audit(cases, RULES)
    predicates = {
        "contracts_strict": lambda s: evaluate(s.document, s.context, RULES).accepted,
        "excerpt_baseline": excerpt_baseline,
        "always_accept": lambda s: True,
        "always_reject": lambda s: False,
    }
    metrics = {name: binary_metrics(cases, pred) for name, pred in predicates.items()}
    timings = []
    # Timing is separated from deterministic report content and is not a cost comparison to LLMs.
    for case in cases[:100]:
        start = perf_counter_ns()
        evaluate(case.variant.document, case.variant.context, RULES)
        timings.append((perf_counter_ns() - start) / 1_000_000)
    summary = {
        "dataset": "synthetic-feasibility-v1",
        "seed": args.seed,
        "scenario_groups": len({c.group for c in cases}),
        "cases": len(cases),
        "corpus_digest": campaign.corpus_digest,
        "contract_digest": campaign.cases[0].baseline.contracts_digest,
        "targeted_audit": campaign.summary(),
        "binary_comparisons": metrics,
        "limitations": [
            "Synthetic authored cases; no natural model outputs or independent raters",
            "Domain templates are lexical variations, not domain generalization evidence",
            "No train/test tuning study and no LLM-as-judge baseline",
            "Pairs share scenarios; rows are not independent observations",
            "Challenge labels extend beyond some rule guarantees",
        ],
    }
    for name, data in (
        ("summary.json", summary),
        ("campaign.json", campaign.to_dict()),
        ("corpus.json", plain(cases)),
    ):
        (args.output / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    latency = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "samples": len(timings),
        "median_ms": statistics.median(timings),
        "p95_ms": sorted(timings)[int(0.95 * (len(timings) - 1))],
        "note": "Local warm-process observations; hash/report construction included",
    }
    (args.output / "latency.json").write_text(json.dumps(latency, indent=2) + "\n")
    table = render_table(metrics)
    (args.output / "summary.md").write_text(
        "# Synthetic feasibility results\n\n"
        + table
        + "\n\n"
        + f"{len(cases)} cases, {summary['scenario_groups']} shared scenario groups, seed {args.seed}.\n\n"
        + "These are construction checks and scope challenges, not evidence of real-world LLM accuracy.\n\n"
        + "Corpus SHA-256: `"
        + campaign.corpus_digest
        + "`\n"
    )
    print(table)
    print(json.dumps({"targeted_audit": campaign.summary(), "latency": latency}, indent=2))


if __name__ == "__main__":
    main()
