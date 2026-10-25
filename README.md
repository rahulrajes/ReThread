# ReThread ♻️ — Sustainable Shopping Chrome Extension

While you browse a fast-fashion product page (H&M, Zara, Shein…), ReThread finds
**second-hand and sustainable alternatives** for that item in real time, using
computer vision + keyword matching to understand the product and a resale-market
search to surface cheaper, greener options.

> This is the **rebuilt, functional version** (v2). The original hackathon build
> tried to run computer vision and marketplace search *inside the browser*, which
> doesn't work (API-key exposure + CORS). v2 fixes that with a proper backend.

## Architecture

```
  Chrome Extension (MV3)                  Backend (FastAPI / Python)          External APIs
 ───────────────────────                 ────────────────────────────        ──────────────
  content.js                              POST /analyze
   └ scrape {title, image} ───┐            1. Google Cloud Vision ──────────▶ Vision API
  popup.js                     │              (label/object/web detection)    (LABEL/OBJECT/WEB)
   └ show ranked results       │            2. CV labels + title
  background.js (service worker)│              → structured metadata
   └ POST to backend ──────────┴──────▶       (type/color/material/style)
                                             3. build search query
                                             4. eBay Browse search ─────────▶ eBay Browse API
                                                (real USED listings)          (OAuth app token)
                                             5. similarity-rank candidates
                                             6. + deep-links (Poshmark/…)
   render alternatives  ◀───────────────── JSON { metadata, alternatives, deep_links }
```

**Why a backend?** The API keys stay server-side (never shipped in the extension),
and the server isn't subject to the browser's CORS wall — so it can actually call
Google Vision and eBay. This is also what makes ReThread genuinely *full-stack*.

## How it maps to the résumé bullet
- *"computer vision ... to identify fashion products"* → **Google Cloud Vision** (`vision.py`): label/object/web detection on the product image.
- *"keyword matching ... map features to structured metadata"* → `metadata.py`: CV labels + title matched against a fashion **taxonomy** → `{type, colors, materials, styles, patterns}`.
- *"surface sustainable resale alternatives in real time ... (Poshmark)"* → `marketplace.py`: **eBay Browse API** for live used listings + **deep-link searches** to Poshmark/Depop/ThredUp/Vinted.
- *"third-party APIs"* → Google Vision + eBay.

## Project structure
```
ReThread/
├── backend/
│   ├── app.py          # FastAPI app — POST /analyze orchestrates everything
│   ├── vision.py       # Google Cloud Vision integration (+ offline mock)
│   ├── metadata.py     # CV labels + title → structured metadata (taxonomy)
│   ├── similarity.py   # weighted attribute-overlap relevance scoring
│   ├── marketplace.py  # eBay Browse API + marketplace deep-links (+ mock)
│   ├── demo.py         # run the whole pipeline in mock mode, no server/keys
│   ├── requirements.txt
│   └── .env.example    # copy to .env to go live
└── extension/
    ├── manifest.json   # MV3
    ├── content.js      # scrape product title + image off the page
    ├── background.js   # service worker — calls the backend
    ├── popup.html/js/css
```

## Run it

### 1. Backend
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```
Runs in **mock mode** by default (no keys needed) — returns realistic sample data
so you can demo the full flow. Quick check: open <http://localhost:8000/health>.
Try the pure-logic pipeline with no server at all: `python3 demo.py`.

### 2. Extension
1. `chrome://extensions` → enable **Developer mode** → **Load unpacked** → pick the `extension/` folder.
2. Visit a product page on H&M / Zara / Shein, click the ReThread icon.
3. See the detected attributes + ranked second-hand alternatives.

### 3. Go live (optional)
Copy `backend/.env.example` → `backend/.env`, set `MOCK_MODE=false`, and add:
- `GOOGLE_VISION_API_KEY` — Google Cloud → enable Vision API → create API key.
- `EBAY_CLIENT_ID` / `EBAY_CLIENT_SECRET` — developer.ebay.com → create an app.

## Notes / honest limitations
- Mock mode fabricates listings so the UX runs offline; live mode hits the real APIs.
- Poshmark/Depop/ThredUp/Vinted expose no open API → we deep-link into their search.
- Site scrapers rely on Open Graph tags (robust) with a largest-image fallback.
