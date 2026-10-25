"""
marketplace.py — find real resale listings (the "third-party API" piece).

- LIVE listings come from the **eBay Browse API** (a real, free API; eBay is a
  huge second-hand clothing marketplace). We filter to USED condition.
- Poshmark / Depop / ThredUp / Vinted have no open API, so we generate
  **deep-link searches** the user can click straight into.

eBay needs an OAuth *application* token (client-credentials grant). We fetch it
from your client id/secret and cache it until it expires.

`requests` is imported lazily so the mock path has no dependencies.
"""

from __future__ import annotations
import base64
import time
from urllib.parse import quote_plus

OAUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
BROWSE_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"

_token_cache = {"token": None, "expires_at": 0.0}


def _get_ebay_token(client_id: str, client_secret: str) -> str:
    """Client-credentials OAuth. Cached until ~1 min before expiry."""
    import requests
    if _token_cache["token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["token"]

    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    resp = requests.post(
        OAUTH_URL,
        headers={"Authorization": f"Basic {basic}",
                 "Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "client_credentials",
              "scope": "https://api.ebay.com/oauth/api_scope"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = time.time() + int(data.get("expires_in", 7200)) - 60
    return _token_cache["token"]


def search_ebay(query: str, client_id: str, client_secret: str,
                limit: int = 8) -> list[dict]:
    """Query eBay Browse for USED items matching the query."""
    import requests
    token = _get_ebay_token(client_id, client_secret)
    resp = requests.get(
        BROWSE_URL,
        headers={"Authorization": f"Bearer {token}",
                 "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"},
        params={"q": query, "limit": limit, "filter": "conditions:{USED}"},
        timeout=12,
    )
    resp.raise_for_status()
    items = resp.json().get("itemSummaries", []) or []
    out = []
    for it in items:
        price = it.get("price", {})
        out.append({
            "title": it.get("title", ""),
            "price": f'{price.get("value", "?")} {price.get("currency", "")}'.strip(),
            "url": it.get("itemWebUrl", ""),
            "image": (it.get("image") or {}).get("imageUrl", ""),
            "platform": "eBay",
            "condition": it.get("condition", "Pre-owned"),
        })
    return out


def search_mock(query: str, limit: int = 8) -> list[dict]:
    """Deterministic fake listings so the app runs without eBay keys."""
    adjectives = ["Vintage", "Pre-owned", "Gently Used", "Secondhand", "Retro"]
    out = []
    for i in range(min(limit, 5)):
        out.append({
            "title": f"{adjectives[i % len(adjectives)]} {query.title()}",
            "price": f"{18 + i * 7}.99 USD",
            "url": f"https://www.ebay.com/sch/i.html?_nkw={quote_plus(query)}",
            "image": "",
            "platform": "eBay",
            "condition": "Pre-owned",
        })
    return out


def deep_links(query: str) -> list[dict]:
    """Click-through searches for marketplaces without an open API."""
    q = quote_plus(query)
    return [
        {"platform": "Poshmark", "url": f"https://poshmark.com/search?query={q}"},
        {"platform": "Depop",    "url": f"https://www.depop.com/search/?q={q}"},
        {"platform": "ThredUp",  "url": f"https://www.thredup.com/products?search_query={q}"},
        {"platform": "Vinted",   "url": f"https://www.vinted.com/catalog?search_text={q}"},
    ]


if __name__ == "__main__":
    print("mock listings:")
    for x in search_mock("black denim jacket"):
        print(" ", x["title"], x["price"])
    print("deep links:", deep_links("black denim jacket"))
