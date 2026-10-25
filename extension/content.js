// content.js — runs ON the fast-fashion product page.
// Its only job: scrape the current product's TITLE and primary IMAGE, then hand
// them to the popup when asked. (All the heavy lifting happens in the backend.)

function pickTitle() {
  // Open Graph title is the most reliable across sites; fall back to h1/title.
  const og = document.querySelector('meta[property="og:title"]')?.content;
  const h1 = document.querySelector("h1")?.textContent?.trim();
  return (og || h1 || document.title || "").trim();
}

function pickImage() {
  // og:image is set by nearly every product page and points at the hero shot.
  const og = document.querySelector('meta[property="og:image"]')?.content;
  if (og) return og;
  // Fallback: the largest <img> on the page (usually the product photo).
  let best = null, bestArea = 0;
  for (const img of document.images) {
    const area = (img.naturalWidth || img.width) * (img.naturalHeight || img.height);
    if (area > bestArea && img.src) { best = img.src; bestArea = area; }
  }
  return best || "";
}

function scrapeProduct() {
  return {
    title: pickTitle(),
    imageUrl: pickImage(),
    site: location.hostname.replace(/^www\./, ""),
  };
}

// Answer the popup's request for the current product.
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.action === "getProduct") {
    sendResponse(scrapeProduct());
  }
  return true;
});
