"""
vision.py — Google Cloud Vision integration (the "computer vision" piece).

Runs SERVER-SIDE (not in the browser) for two reasons the old prototype got
wrong: (1) the API key stays secret on the server, (2) no browser CORS wall.

Flow: download the product image -> base64 -> POST to Vision images:annotate
with LABEL_DETECTION, OBJECT_LOCALIZATION, WEB_DETECTION -> return clean labels.

`requests` is imported lazily inside the real path so the mock path (and tests)
run with zero dependencies.
"""

from __future__ import annotations
import base64

VISION_ENDPOINT = "https://vision.googleapis.com/v1/images:annotate"


def analyze_image(image_url: str, api_key: str, max_results: int = 10) -> dict:
    """Call Google Cloud Vision on the product image. Returns normalized labels."""
    import requests  # lazy: only needed on the real path

    img = requests.get(image_url, timeout=10)
    img.raise_for_status()
    content = base64.b64encode(img.content).decode("utf-8")

    body = {
        "requests": [{
            "image": {"content": content},
            "features": [
                {"type": "LABEL_DETECTION", "maxResults": max_results},
                {"type": "OBJECT_LOCALIZATION", "maxResults": max_results},
                {"type": "WEB_DETECTION", "maxResults": max_results},
            ],
        }]
    }
    resp = requests.post(f"{VISION_ENDPOINT}?key={api_key}", json=body, timeout=15)
    resp.raise_for_status()
    r = resp.json()["responses"][0]

    labels = [x["description"] for x in r.get("labelAnnotations", [])]
    objects = [x["name"] for x in r.get("localizedObjectAnnotations", [])]
    web = [e["description"] for e in
           r.get("webDetection", {}).get("webEntities", []) if e.get("description")]

    # de-duplicate, preserve order
    seen, merged = set(), []
    for term in labels + objects + web:
        key = term.lower()
        if key not in seen:
            seen.add(key)
            merged.append(term)
    return {"labels": labels, "objects": objects, "web_entities": web, "all": merged}


def analyze_image_mock(title: str) -> dict:
    """
    Offline stand-in for Vision so the app runs without a key. Simulates the CV
    'recognizing' attributes by echoing taxonomy words found in the title plus a
    few generic clothing labels — enough to exercise the full pipeline.
    """
    from metadata import TAXONOMY, _normalize
    blob = _normalize(title)
    detected = [t.title() for cat in TAXONOMY for t in TAXONOMY[cat]
                if f" {t} " in blob]
    generic = ["Clothing", "Fashion", "Textile", "Sleeve", "Pattern"]
    merged = detected + [g for g in generic if g not in detected]
    return {"labels": merged, "objects": detected[:3],
            "web_entities": detected, "all": merged}


if __name__ == "__main__":
    print(analyze_image_mock("Black Denim Jacket Slim Fit"))
