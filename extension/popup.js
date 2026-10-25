// popup.js — orchestrates the popup UI.
// 1) ask the content script for the product on the page
// 2) ask the service worker to analyze it (which calls the backend)
// 3) render the sustainable alternatives

const statusEl = document.getElementById("status");
const detectedEl = document.getElementById("detected");
const metaTextEl = document.getElementById("metaText");
const resultsEl = document.getElementById("results");
const deeplinksEl = document.getElementById("deeplinks");
const deeplinkRowEl = document.getElementById("deeplinkRow");
const footerEl = document.getElementById("footer");

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

// Ask content.js for the product; if it isn't there yet, inject it and retry.
async function getProduct(tabId) {
  try {
    return await chrome.tabs.sendMessage(tabId, { action: "getProduct" });
  } catch {
    await chrome.scripting.executeScript({ target: { tabId }, files: ["content.js"] });
    return await chrome.tabs.sendMessage(tabId, { action: "getProduct" });
  }
}

function describeMeta(meta) {
  const bits = [
    ...(meta.colors || []),
    ...(meta.materials || []),
    ...(meta.patterns || []),
    meta.type,
  ].filter(Boolean);
  return bits.length ? bits.join(" · ") : "a clothing item";
}

function renderAlternatives(alts) {
  resultsEl.innerHTML = "";
  for (const a of alts) {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <div class="card-body">
        <div class="card-title">${a.title}</div>
        <div class="card-meta">
          <span class="price">${a.price || ""}</span>
          <span class="platform">${a.platform}</span>
          <span class="match">${Math.round((a.similarity || 0) * 100)}% match</span>
        </div>
      </div>`;
    card.addEventListener("click", () => chrome.tabs.create({ url: a.url }));
    resultsEl.appendChild(card);
  }
}

function renderDeepLinks(links) {
  deeplinkRowEl.innerHTML = "";
  for (const d of links) {
    const btn = document.createElement("button");
    btn.className = "chip";
    btn.textContent = d.platform;
    btn.addEventListener("click", () => chrome.tabs.create({ url: d.url }));
    deeplinkRowEl.appendChild(btn);
  }
  deeplinksEl.hidden = false;
}

async function run() {
  try {
    const tab = await getActiveTab();
    const product = await getProduct(tab.id);

    if (!product || !product.title) {
      statusEl.textContent = "Open a product page to find second-hand alternatives.";
      return;
    }

    statusEl.textContent = "Finding sustainable alternatives…";
    const res = await chrome.runtime.sendMessage({ action: "analyze", product });

    if (!res || !res.ok) {
      statusEl.textContent =
        "Couldn't reach the ReThread server. Is the backend running on :8000?";
      return;
    }

    const { metadata, alternatives, deep_links, mock_mode } = res.data;
    statusEl.textContent = `Found ${alternatives.length} second-hand options`;
    metaTextEl.textContent = describeMeta(metadata);
    detectedEl.hidden = false;
    renderAlternatives(alternatives);
    renderDeepLinks(deep_links);
    if (mock_mode) {
      footerEl.hidden = false;
      footerEl.textContent = "demo mode — add API keys in backend/.env to go live";
    }
  } catch (err) {
    statusEl.textContent = `Error: ${err.message}`;
  }
}

document.addEventListener("DOMContentLoaded", run);
