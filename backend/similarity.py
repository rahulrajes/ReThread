"""
similarity.py — score how well a candidate resale listing matches the original
item, using the STRUCTURED metadata (not raw text). Interpretable, weighted
overlap by attribute importance.

Pure-Python, no dependencies.
"""

from __future__ import annotations
import re

# How much each attribute matters when judging "is this the same kind of item?"
# Type (dress vs jacket) matters most; color/material next; style/pattern are
# tie-breakers. Weights sum to 1.0 so the score lands in [0, 1].
WEIGHTS = {
    "type": 0.40,
    "color": 0.20,
    "material": 0.20,
    "style": 0.10,
    "pattern": 0.10,
}

_WORD = re.compile(r"[a-z0-9\-]+")


def _tokens(text: str) -> set[str]:
    return set(_WORD.findall((text or "").lower()))


def score(meta: dict, candidate_title: str) -> float:
    """
    For each attribute category, if ANY of the original item's values for that
    category appears in the candidate's title, award that category's weight.
    Sum -> a 0..1 relevance score.
    """
    cand = _tokens(candidate_title)
    s = 0.0

    # type is a single value; the rest are lists
    if meta.get("type") and set(_WORD.findall(meta["type"])).issubset(cand):
        s += WEIGHTS["type"]

    for cat in ("color", "material", "style", "pattern"):
        values = meta.get(cat + "s", [])  # colors / materials / styles / patterns
        if any(set(_WORD.findall(v)).issubset(cand) for v in values):
            s += WEIGHTS[cat]

    return round(min(s, 1.0), 3)


def rank(meta: dict, candidates: list[dict], min_score: float = 0.2) -> list[dict]:
    """Attach a similarity score to each candidate, filter weak ones, sort desc."""
    scored = []
    for c in candidates:
        c = {**c, "similarity": score(meta, c.get("title", ""))}
        if c["similarity"] >= min_score:
            scored.append(c)
    scored.sort(key=lambda c: c["similarity"], reverse=True)
    return scored


if __name__ == "__main__":
    meta = {"type": "jacket", "colors": ["black"], "materials": ["denim"],
            "styles": ["slim"], "patterns": []}
    cands = [
        {"title": "Vintage Black Denim Jacket", "platform": "eBay"},
        {"title": "Blue Cotton Hoodie", "platform": "eBay"},
        {"title": "Slim Black Denim Trucker Jacket", "platform": "eBay"},
    ]
    for c in rank(meta, cands):
        print(f'{c["similarity"]:.2f}  {c["title"]}')
