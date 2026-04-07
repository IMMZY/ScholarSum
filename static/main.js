// ── Theme toggle ──────────────────────────────────────
(function initTheme() {
  const saved = localStorage.getItem("ss-theme") || "light";
  document.documentElement.setAttribute("data-theme", saved);
  // icon updates after DOM is ready
  document.addEventListener("DOMContentLoaded", () => {
    const icon = document.getElementById("theme-icon");
    if (icon) icon.textContent = saved === "dark" ? "☀️" : "🌙";
  });
})();

function toggleTheme() {
  const html = document.documentElement;
  const isDark = html.getAttribute("data-theme") === "dark";
  const next = isDark ? "light" : "dark";
  html.setAttribute("data-theme", next);
  localStorage.setItem("ss-theme", next);
  document.getElementById("theme-icon").textContent = next === "dark" ? "☀️" : "🌙";
}

let activeTab = "text";
let apiConnected = false;

(async function checkApiStatus() {
  try {
    const res = await fetch("/api-status");
    const { connected } = await res.json();
    apiConnected = connected;
    const badge = document.getElementById("api-status-badge");
    if (connected) {
      badge.className = "api-status-badge connected";
      badge.innerHTML = '<span class="dot"></span> GPT-4o-mini Connected';
    } else {
      badge.className = "api-status-badge disconnected";
      badge.innerHTML = '<span class="dot"></span> TF-IDF Mode (no API key)';
    }
    updateLangNote();
  } catch {
    // silently ignore if server not reachable yet
  }
})();

function updateLangNote() {
  const note = document.getElementById("lang-note");
  const sel = document.getElementById("language");
  if (!note || !sel) return;
  if (!apiConnected && sel.value !== "English") {
    note.textContent = "⚠ Translation requires GPT API";
    note.style.display = "inline";
  } else {
    note.style.display = "none";
  }
}

document.getElementById("language").addEventListener("change", updateLangNote);
let sourceFilename = "document";
let lastResult = null;

function switchTab(tab) {
  activeTab = tab;
  document.querySelectorAll(".tab-btn").forEach((b, i) => {
    b.classList.toggle(
      "active",
      (i === 0 && tab === "text") || (i === 1 && tab === "pdf"),
    );
  });
  document
    .getElementById("tab-text")
    .classList.toggle("active", tab === "text");
  document.getElementById("tab-pdf").classList.toggle("active", tab === "pdf");
}

function switchView(view) {
  document.querySelectorAll(".view-btn").forEach((b, i) => {
    b.classList.toggle(
      "active",
      (i === 0 && view === "bullets") || (i === 1 && view === "para"),
    );
  });
  document
    .getElementById("bullets-view")
    .classList.toggle("active", view === "bullets");
  document
    .getElementById("para-view")
    .classList.toggle("active", view === "para");
}

function updateSlider(val) {
  document.getElementById("slider-display").textContent = val + "%";
  // Highlight matching preset button if value matches
  const presetMap = { 15: 0, 25: 1, 45: 2 };
  document.querySelectorAll(".preset-btn").forEach((btn, i) => {
    btn.classList.toggle("active", presetMap[parseInt(val)] === i);
  });
}

function setLength(val) {
  const slider = document.getElementById("summary_length");
  slider.value = val;
  updateSlider(val);
}

function handleFileSelect(input) {
  const file = input.files[0];
  const name = file?.name || "";
  sourceFilename = name || "document";
  document.getElementById("file-name").textContent = name ? "✔ " + name : "";
}

const zone = document.getElementById("upload-zone");
zone.addEventListener("dragover", (e) => {
  e.preventDefault();
  zone.classList.add("dragover");
});
zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));
zone.addEventListener("drop", (e) => {
  e.preventDefault();
  zone.classList.remove("dragover");
});

document
  .getElementById("summarize-form")
  .addEventListener("submit", async function (e) {
    e.preventDefault();
    const errorBox = document.getElementById("error-box");
    const results = document.getElementById("results");
    const btn = document.getElementById("submit-btn");
    const spinner = document.getElementById("spinner");

    errorBox.style.display = "none";
    results.style.display = "none";
    lastResult = null;

    btn.disabled = true;
    spinner.style.display = "block";
    spinner.textContent = "⏳ Analyzing document…";

    const formData = new FormData(this);
    if (activeTab === "text") formData.delete("pdf_file");
    else formData.delete("text_input");

    try {
      const res = await fetch("/summarize", { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok || data.error) {
        errorBox.textContent = data.error || "Something went wrong.";
        errorBox.style.display = "block";
      } else {
        data.source_filename =
          activeTab === "pdf" ? sourceFilename : "document";
        lastResult = data;
        renderResults(data);
        // Update the badge to reflect what actually ran (OpenAI vs TF-IDF fallback)
        const badge = document.getElementById("api-status-badge");
        if (data.method === "openai") {
          apiConnected = true;
          badge.className = "api-status-badge connected";
          badge.innerHTML = '<span class="dot"></span> GPT-4o-mini Connected';
        } else {
          apiConnected = false;
          badge.className = "api-status-badge disconnected";
          badge.innerHTML = '<span class="dot"></span> TF-IDF Mode (no API key)';
        }
      }
    } catch (err) {
      errorBox.textContent = "Network error. Is the server running?";
      errorBox.style.display = "block";
    } finally {
      btn.disabled = false;
      spinner.style.display = "none";
    }
  });

function renderResults(data) {
  const compression = Math.round(
    (1 - data.summary_word_count / data.original_word_count) * 100,
  );
  document.getElementById("stats-row").innerHTML = `
      <div class="stat"><div class="val">${data.original_word_count.toLocaleString()}</div><div class="lbl">Original words</div></div>
      <div class="stat"><div class="val">${data.summary_word_count.toLocaleString()}</div><div class="lbl">Summary words</div></div>
      <div class="stat"><div class="val">${compression}%</div><div class="lbl">Compression</div></div>
      <div class="stat"><div class="val">${data.sentence_count}</div><div class="lbl">Key points</div></div>
    `;

  const isOpenAI = data.method === "openai";
  document.getElementById("method-badge").innerHTML = `
      <span class="method-badge ${data.method}">
        ${isOpenAI ? "🤖 Summarized by GPT-4o-mini" : "📊 Summarized by TF-IDF (fallback)"}
      </span>`;

  document.getElementById("bullet-list").innerHTML = data.bullet_points
    .map((p) => `<li><div class="bullet-dot"></div><span>${p}</span></li>`)
    .join("");

  document.getElementById("paragraph-box").textContent = data.paragraph;

  document.getElementById("keywords-wrap").innerHTML = data.keywords
    .map(([word]) => `<span class="kw-chip">${word}</span>`)
    .join("");

  // Citations
  const citSection = document.getElementById("citations-section");
  const citList = document.getElementById("citation-list");
  if (data.citations && data.citations.length > 0) {
    citList.innerHTML = data.citations
      .map((c) => `<li class="citation-item">${c}</li>`)
      .join("");
    citSection.style.display = "block";
  } else {
    citSection.style.display = "none";
  }

  document.getElementById("results").style.display = "block";
  switchView("bullets");
  document.getElementById("results").scrollIntoView({ behavior: "smooth" });
}

async function copyToClipboard() {
  const bulletsVisible = document.getElementById("bullets-view").classList.contains("active");
  let text;
  if (bulletsVisible) {
    const items = document.querySelectorAll("#bullet-list li span");
    text = Array.from(items).map((el, i) => `${i + 1}. ${el.textContent}`).join("\n");
  } else {
    text = document.getElementById("paragraph-box").textContent;
  }
  const btn = document.getElementById("copy-btn");
  try {
    await navigator.clipboard.writeText(text);
    btn.textContent = "✔ Copied!";
  } catch {
    btn.textContent = "✖ Failed";
  }
  setTimeout(() => { btn.innerHTML = "📋 Copy"; }, 2000);
}

async function downloadSummary(format) {
  if (!lastResult) return;
  const formatClass = format === "docx" ? "docx" : format;
  const btn = document.querySelector(`.dl-btn.${formatClass}`);
  const originalHTML = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = "⏳ Generating…";

  try {
    const res = await fetch("/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        format,
        source_filename: lastResult.source_filename || "document",
        ...lastResult,
      }),
    });

    if (!res.ok) {
      const err = await res.json();
      alert(err.error || "Download failed.");
      return;
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const base = (lastResult.source_filename || "document").replace(
      /\.[^.]+$/,
      "",
    );
    a.download = `${base}_summarized.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch {
    alert("Download failed. Is the server running?");
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalHTML;
  }
}
