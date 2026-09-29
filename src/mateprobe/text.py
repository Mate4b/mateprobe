from __future__ import annotations

import re
import unicodedata


def normalize(text: str, fold_accents: bool = False) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    if fold_accents:
        text = "".join(
            c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
        )
    return unicodedata.normalize("NFC", text)


def tokens(text: str) -> tuple[str, ...]:
    """Unicode word tokens with at least one letter, not an information measure."""
    return tuple(t for t in re.findall(r"\w+", normalize(text)) if any(c.isalpha() for c in t))
