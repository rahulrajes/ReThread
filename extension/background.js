// background.js — the extension's service worker (MV3).
// It owns the network call to our backend, so all API logic lives in one place
// (and off the page, away from the site's CSP). Popup -> SW -> backend -> popup.

const BACKEND_URL = "http://localhost:8000/analyze";

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.action === "analyze") {
    fetch(BACKEND_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: msg.product.title,
        image_url: msg.product.imageUrl,
        max_results: 5,
      }),
    })
      .then((r) => {
        if (!r.ok) throw new Error(`Backend ${r.status}`);
        return r.json();
      })
      .then((data) => sendResponse({ ok: true, data }))
      .catch((err) => sendResponse({ ok: false, error: err.message }));
    return true; // keep the message channel open for the async response
  }
});
