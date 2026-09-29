# Launch copy — draft, not sent

Material listo para copiar. No publicar desde este archivo: los textos son un
borrador para revisión del mantenedor.

## Post corto en español

Estoy publicando Narrative Contracts, una librería Python y plugin de pytest para
auditar validadores que ya existen con casos emparejados, findings atribuibles y
controles válidos.

La versión publicada `0.1.0a3` permite comparar una variante defectuosa con una
base válida sin esconder los límites del resultado: si una variante inválida
devuelve `True`, queda como `survived`; si la rechaza por la razón equivocada,
queda como `unattributed_rejection`. El corpus y sus etiquetas los aporta quien
integra el auditor.

En la demo inicial, un claim de reembolso “completado” sin recibo confiable y otro
con un request equivocado quedan detectados después del arreglo: 0/3 fallos antes
y 2/3 después, con 1/1 control válido preservado. La contradicción que vive solo
en la prosa queda visible como desafío: el proyecto no afirma detectar
automáticamente invocaciones de API ni certificar que el texto libre sea verdad.

La receta y el informe completo están enlazados en [first-audit](https://mate4b.github.io/narrative-contracts/docs/first-audit/)
y [launch](https://mate4b.github.io/narrative-contracts/docs/launch/). Código: [github.com/Mate4b/narrative-contracts](https://github.com/Mate4b/narrative-contracts).
Para compartir un caso, usa [una issue de feedback](https://github.com/Mate4b/narrative-contracts/issues/new?template=integration-report.yml).

## Short post in English

I’m releasing Narrative Contracts, a Python library and pytest plugin for auditing
existing validators with paired cases, attributable findings, and valid controls.

The published `0.1.0a3` release compares a faulty variant with a valid baseline
without hiding what the result means: when an invalid variant returns `True`, it
is reported as `survived`; when it rejects for the wrong reason, it is reported as
`unattributed_rejection`. The integrating user supplies the corpus and its labels.

In the entry demo, a “completed” refund claim without a trusted receipt and one
with the wrong request are detected after the fix: 0/3 faults before and 2/3
after, with 1/1 valid control preserved. A contradiction that exists only in prose
remains visible as a challenge: this project does not claim automatic API
invocation detection or that unrestricted prose is truthful.

The recipe and full report are linked from [first-audit](https://mate4b.github.io/narrative-contracts/docs/first-audit/) and
[launch](https://mate4b.github.io/narrative-contracts/docs/launch/). Code: [github.com/Mate4b/narrative-contracts](https://github.com/Mate4b/narrative-contracts).
Please share a case through [the feedback issue form](https://github.com/Mate4b/narrative-contracts/issues/new?template=integration-report.yml).

## Brief technical description

Narrative Contracts audits an existing Python validator through a caller-defined
corpus of paired baseline and variant samples. Each case names an obligation, an
expected finding, a relation (`VIOLATION` or `PRESERVE`), a validity label, and
provenance. The harness first requires the baseline to be accepted and complete,
then classifies the variant as `detected`, `survived`,
`unattributed_rejection`, `regressed`, `undetermined`, or `error`. A
rejection without the expected finding is not credited as detection. Reports
retain fault and control evidence separately, including the corpus digest and
explicit gaps.

The published alpha is `narrative-contracts==0.1.0a3` with the optional
`pytest-narrative-contracts==0.1.0a3` plugin. The core remains offline and does
not call a model, an API, or a refund service. Trusted state and receipts must
come from the application. A completed refund claim is supported only by a
matching completed receipt; no receipt, timeout, incomplete acceptance, or stale
receipt is proof that an API call did or did not happen. Free prose is outside the guarantee: checking structured declarations does not
prove that the prose agrees with them. Lexical checks also have explicit limits.

## Demo script — approximately five minutes

Times are orientation only; they are not a measured integration or execution
claim.

### 0:00–0:45 — Frame the question

“This is an audit of an existing validator, not a new refund service. The
application owns the trusted customer, order, amount, request ID, and receipt.
The auditor receives a user-supplied corpus of valid baselines, authored faults,
and preservation controls. It does not invoke an API or infer truth from prose.”

Open the [first-audit recipe](https://mate4b.github.io/narrative-contracts/docs/first-audit/) and its downloadable
`examples/first_audit.py` entry point. Point to [the published a3 API](https://mate4b.github.io/narrative-contracts/docs/api-a3/).
Install the published packages:

```sh
python -m pip install narrative-contracts==0.1.0a3 pytest-narrative-contracts==0.1.0a3
```

### 0:45–2:15 — Run the entry demo

Run the new, self-contained entry demo and its pytest form using the commands in
[first-audit](https://mate4b.github.io/narrative-contracts/docs/first-audit/). It contains exactly three fault cases: a
completed claim with `receipt = None`, a completed claim whose receipt has the
wrong request ID, and one separate prose-only challenge. It also contains one
honest-pending preservation control.

Explain the business boundary: the validator checks trusted execution evidence.
A matching completed receipt supports the claim; a missing or mismatched receipt
does not. This check neither proves that no call happened nor runs a refund.

Show the report: the before validator detects 0/3 faults; the corrected validator
detects 2/3; the honest-pending control is preserved 1/1. Keep the prose challenge
visible in its own result. Its presence does not turn the score into arbitrary
prose accuracy or API-invocation detection.

### 2:15–3:10 — Explain attribution

Show one targeted rejection and say: “A rejection counts only when it contains the
expected finding ID. If an invalid variant returns `True`, the audit labels it
`survived`. If it returns `False` but reports an unrelated or missing finding,
the result is `unattributed_rejection`—wrong reason, not detection.”

Show the honest-pending control: with no receipt, the application declines to
claim completion and the valid control remains accepted. The corpus and its labels
are caller-supplied and need review.

### 3:10–4:20 — Keep the fix as a regression

Run `python -m pytest first_audit.py --narrative-report=pytest-audit.json`.
In `test_refund_policy`, temporarily replace the `after` validator with
`before` and rerun. The test fails; the JSON report is still written.
Restore `after`. Explain that the test explicitly retains the known prose
survivor and will not let another missed fault silently replace it.

The larger `examples/audit_existing_validator.py` can be a follow-up demo:
9 authored faults, 3/9 → 8/9, and two controls. It is a separate corpus; do not
combine its scores with this three-fault entry example.

### 4:20–5:00 — Close with the evidence boundary

“The useful output is a reviewable report: what the validator caught, what it
accepted, what it rejected for the wrong reason, which controls held, and which
obligations still lack evidence. The prose survivor is intentionally visible.
If you have a missed violation, false rejection, or another validator to audit,
send the smallest reproducible corpus through the
[feedback issue form](https://github.com/Mate4b/narrative-contracts/issues/new?template=integration-report.yml).”
