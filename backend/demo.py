"""
demo.py — run the FULL pipeline in mock mode, no server, no API keys, no deps.
Proves the core logic end-to-end. Run:  python3 demo.py
"""
import vision, marketplace
from metadata import extract_metadata, build_query
from similarity import rank

SAMPLE_PRODUCTS = [
    "Slim Fit Black Denim Jacket - Men",
    "Floral Print Midi Dress",
    "Organic Cotton White T-Shirt",
]

for title in SAMPLE_PRODUCTS:
    cv = vision.analyze_image_mock(title)               # 1) computer vision (mock)
    meta = extract_metadata(title, cv["all"])           # 2) -> structured metadata
    query = build_query(meta)                           # 3) -> search query
    listings = marketplace.search_mock(query, limit=8)  # 4) marketplace (mock)
    ranked = rank(meta, listings, min_score=0.2)[:5]    # 5) similarity rank

    print("\n" + "=" * 70)
    print("PRODUCT :", title)
    print("CV LABELS:", ", ".join(cv["all"][:8]))
    print("METADATA :", {k: v for k, v in meta.items() if v})
    print("QUERY    :", query)
    print("TOP RESALE ALTERNATIVES (eBay):")
    for a in ranked:
        print(f'   {a["similarity"]:.2f}  {a["title"]:<40} {a["price"]}')
    print("ALSO SEARCH:", ", ".join(f'{d["platform"]}' for d in marketplace.deep_links(query)))
