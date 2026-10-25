"""
metadata.py — turn CV labels + the product title into STRUCTURED metadata.

This is the "computer vision + keyword matching -> structured metadata" core of
ReThread. Google Cloud Vision gives us free-text labels ("Denim", "Sleeve",
"Jacket"...); the product page gives us a title. We match BOTH against a
controlled fashion taxonomy to extract a clean, structured description we can
search with.

Pure-Python, no external dependencies (so it's trivially testable).
"""

from __future__ import annotations
import re

# --- the controlled fashion vocabulary (a "taxonomy") ------------------------
TAXONOMY = {
    "type": [
        "dress", "shirt", "t-shirt", "tee", "blouse", "top", "tank top", "crop top",
        "pants", "jeans", "trousers", "leggings", "shorts", "skirt",
        "jacket", "coat", "blazer", "cardigan", "hoodie", "sweatshirt", "sweater",
        "jumpsuit", "romper", "vest", "bodysuit", "sneakers", "boots", "bag",
    ],
    "color": [
        "black", "white", "red", "blue", "navy", "green", "olive", "yellow",
        "purple", "lavender", "pink", "brown", "tan", "beige", "cream", "gray",
        "grey", "charcoal", "orange", "burgundy", "maroon", "teal", "khaki",
        "gold", "silver",
    ],
    "material": [
        "cotton", "organic cotton", "recycled cotton", "wool", "silk", "denim",
        "leather", "faux leather", "polyester", "recycled polyester", "linen",
        "cashmere", "velvet", "suede", "knit", "fleece", "corduroy", "nylon",
        "bamboo", "modal", "lyocell", "tencel",
    ],
    "style": [
        "casual", "formal", "business", "streetwear", "athletic", "bohemian",
        "vintage", "minimalist", "preppy", "y2k", "classic", "oversized",
        "slim", "cropped", "relaxed", "fitted",
    ],
    "pattern": [
        "solid", "striped", "floral", "plaid", "polka dot", "checkered",
        "animal print", "leopard", "camouflage", "geometric", "tie dye",
        "houndstooth", "herringbone", "paisley",
    ],
}

# Longer phrases first so "t-shirt" beats "shirt", "organic cotton" beats "cotton".
for _cat in TAXONOMY:
    TAXONOMY[_cat] = sorted(set(TAXONOMY[_cat]), key=len, reverse=True)

_WORD = re.compile(r"[a-z0-9\-]+")


def _normalize(text: str) -> str:
    return " " + " ".join(_WORD.findall((text or "").lower())) + " "


def extract_metadata(title: str, cv_labels: list[str] | None = None) -> dict:
    """
    Combine the product TITLE and the CV LABELS into one text blob, then pull
    out each taxonomy category by phrase matching. Returns structured metadata.
    """
    cv_labels = cv_labels or []
    blob = _normalize(title + " " + " ".join(cv_labels))

    found: dict[str, list[str]] = {cat: [] for cat in TAXONOMY}
    for category, terms in TAXONOMY.items():
        for term in terms:
            # pad the term so we match whole words/phrases, not substrings
            if f" {term} " in blob and term not in found[category]:
                found[category].append(term)

    return {
        "type": found["type"][0] if found["type"] else None,  # primary garment
        "colors": found["color"],
        "materials": found["material"],
        "styles": found["style"],
        "patterns": found["pattern"],
    }


def build_query(meta: dict) -> str:
    """
    Turn structured metadata into a marketplace search string, most-specific
    attributes first: "<color> <material> <type>", e.g. "black denim jacket".
    Falls back gracefully when fields are missing.
    """
    parts: list[str] = []
    if meta.get("colors"):
        parts.append(meta["colors"][0])
    if meta.get("materials"):
        parts.append(meta["materials"][0])
    # if we have no color/material, fall back to a pattern or style descriptor
    if not parts:
        if meta.get("patterns"):
            parts.append(meta["patterns"][0])
        elif meta.get("styles"):
            parts.append(meta["styles"][0])
    parts.append(meta.get("type") or "clothing")
    return " ".join(parts)


if __name__ == "__main__":
    demo = extract_metadata(
        "Slim Fit Black Denim Jacket - Men",
        cv_labels=["Jacket", "Denim", "Sleeve", "Outerwear", "Textile"],
    )
    print("metadata:", demo)
    print("query:   ", build_query(demo))
