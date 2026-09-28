"""Minimal original fixture demonstrating the LifeCard adapter without importing its engine."""

from narrative_contracts import Claim, Context, DeclaredClaimsConsistent, StateChanged, evaluate
from narrative_contracts.adapters import lifecard_document

card = {
    "title_template": "Una propuesta",
    "body_template": "La coordinadora te entrega una propuesta.",
    "options": [
        {
            "id": "accept",
            "label_template": "Aceptar",
            "outcomes": [
                {
                    "id": "signed",
                    "title_template": "Acuerdo firmado",
                    "body_template": "Firmás el acuerdo y recibís los recursos pactados para comenzar el trabajo.",
                }
            ],
        }
    ],
}
surface_id = "$.options[0].outcomes[0].body_template"
document = lifecard_document(
    card,
    claims_by_surface={
        surface_id: (Claim("employment.status", "employed"),),
    },
)
# In an application, obtain these snapshots from the trusted engine's execution.
context = Context(
    {
        "current": {"employment.status": "unemployed", "resources": 0},
        "accept/signed": {"employment.status": "employed", "resources": 10},
    }
)
report = evaluate(
    document,
    context,
    (
        DeclaredClaimsConsistent("branch-truth", (surface_id,)),
        StateChanged(
            "domain-advance", "current", "accept/signed", ("employment.status", "resources")
        ),
    ),
)
report.assert_accepted()
print("Accepted: declared claim and branch transition satisfy their contracts.")
