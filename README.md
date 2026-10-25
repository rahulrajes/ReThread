# ReThread 

Shop sustainable by recycling and reusing!

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

### 2. Extension
1. `chrome://extensions` → enable **Developer mode** → **Load unpacked** → pick the `extension/` folder.
2. Visit a product page on H&M / Zara / Shein, click the ReThread icon.
3. See the detected attributes + ranked second-hand alternatives.
