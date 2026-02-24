let activeTab = "text";
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
}

function handleFileSelect(input) {
  const file = input.files[0];
  const name = file?.name || "";
  sourceFilename = name || "document";
  document.getElementById("file-name").textContent = name ? "✔ " + name : "";
}

function toggleKey() {
  const input = document.getElementById("api_key");
  input.type = input.type === "password" ? "text" : "password";
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
    spinner.textContent = document.getElementById("api_key").value
      ? "🤖 Asking GPT-4o-mini…"
      : "📊 Analyzing with TF-IDF…";

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

  document.getElementById("results").style.display = "block";
  switchView("bullets");
  document.getElementById("results").scrollIntoView({ behavior: "smooth" });
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
