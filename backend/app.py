"""
app.py — the ReThread backend (FastAPI).

ONE endpoint, POST /analyze, runs the whole pipeline:
  image+title  ->  Vision labels  ->  structured metadata  ->  search query
  ->  eBay resale listings  ->  similarity-ranked  ->  + marketplace deep-links

Runs in MOCK mode automatically when API keys are absent, so you can demo it
with zero setup; add keys in .env to go live.
"""

from __future__ import annotations
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import vision
import marketplace
from metadata import extract_metadata, build_query
from similarity import rank

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

VISION_KEY = os.getenv("GOOGLE_VISION_API_KEY", "")
EBAY_ID = os.getenv("EBAY_CLIENT_ID", "")
EBAY_SECRET = os.getenv("EBAY_CLIENT_SECRET", "")
# Mock unless explicitly disabled OR keys are missing.
MOCK = os.getenv("MOCK_MODE", "").lower() != "false" or not (VISION_KEY and EBAY_ID)

app = FastAPI(title="ReThread API", version="2.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    title: str
    image_url: str | None = None
    max_results: int = 5


@app.get("/health")
def health():
    return {"status": "ok", "mock_mode": MOCK}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    # 1) COMPUTER VISION ------------------------------------------------------
    if MOCK or not (VISION_KEY and req.image_url):
        cv = vision.analyze_image_mock(req.title)
    else:
        try:
            cv = vision.analyze_image(req.image_url, VISION_KEY)
        except Exception:
            cv = vision.analyze_image_mock(req.title)  # graceful fallback

    # 2) CV + KEYWORDS -> STRUCTURED METADATA --------------------------------
    meta = extract_metadata(req.title, cv["all"])
    query = build_query(meta)

    # 3) MARKETPLACE SEARCH ---------------------------------------------------
    if MOCK or not (EBAY_ID and EBAY_SECRET):
        listings = marketplace.search_mock(query, limit=8)
    else:
        try:
            listings = marketplace.search_ebay(query, EBAY_ID, EBAY_SECRET, limit=8)
        except Exception:
            listings = marketplace.search_mock(query, limit=8)

    # 4) SIMILARITY RANK ------------------------------------------------------
    ranked = rank(meta, listings, min_score=0.2)[: req.max_results]
    if not ranked:  # never show an empty popup in a demo
        ranked = [{**l, "similarity": 0.0} for l in listings[: req.max_results]]

    return {
        "mock_mode": MOCK,
        "cv_labels": cv["all"][:10],
        "metadata": meta,
        "query": query,
        "alternatives": ranked,
        "deep_links": marketplace.deep_links(query),
    }
