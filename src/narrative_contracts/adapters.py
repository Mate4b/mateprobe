"""Application boundary adapters. Never execute generated effects here."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .model import Claim, Document, Surface


def lifecard_document(
    card: Mapping[str, Any], *, claims_by_surface: Mapping[str, tuple[Claim, ...]] | None = None
) -> Document:
    """Convert a LifeCard-shaped payload into branch-scoped text surfaces.

    Supply authoritative snapshots separately in Context.states under `current`
    and `<option-id>/<outcome-id>`. This adapter does not derive truth from LLM
    effects. Claims are optional declarations, NOT trusted textual extraction.
    """
    claims = claims_by_surface or {}
    surfaces = []

    def add(path: str, text: str, state_ref: str = "current") -> None:
        surfaces.append(Surface(path, text, state_ref, tuple(claims.get(path, ()))))

    add("$.title_template", card["title_template"])
    add("$.body_template", card["body_template"])
    branches: set[str] = set()
    for i, option in enumerate(card["options"]):
        add(f"$.options[{i}].label_template", option["label_template"])
        for j, outcome in enumerate(option["outcomes"]):
            branch = f"{option['id']}/{outcome['id']}"
            if branch in branches:
                raise ValueError(f"Duplicate branch reference: {branch}")
            branches.add(branch)
            prefix = f"$.options[{i}].outcomes[{j}]"
            add(f"{prefix}.title_template", outcome["title_template"], branch)
            add(f"{prefix}.body_template", outcome["body_template"], branch)
    unknown = claims.keys() - {s.id for s in surfaces}
    if unknown:
        raise ValueError(f"Claim annotations refer to unknown surfaces: {sorted(unknown)}")
    return Document(tuple(surfaces))
