/* Spec Data Lake — live dashboard */

const STAGES = ["received", "extracting", "classifying", "structuring", "validating", "integrated"];
const STAGE_LABELS = {
  received: "Ingest", extracting: "Extract", classifying: "Classify",
  structuring: "Structure", validating: "Validate", integrated: "Integrate",
};
const CAT_ORDER = ["signals", "states", "requirements", "dtcs", "parameters", "relationships"];
const CAT_NAMES = {
  signals: "Signals", states: "States", requirements: "Requirements",
  dtcs: "DTCs", parameters: "Parameters", relationships: "Relationships",
};

/* ---- SVG icons (stroke line icons) ---- */
const ICONS = {
  upload: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>',
  cloud: '<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M20 16.2A4.5 4.5 0 0 0 17.5 8h-1.8A7 7 0 1 0 4 14.9"/><polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/></svg>',
  docs: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="13" y2="17"/></svg>',
  flow: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="6" height="6" rx="1"/><rect x="15" y="15" width="6" height="6" rx="1"/><path d="M9 6h6a3 3 0 0 1 3 3v6"/></svg>',
  history: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v5h5"/><path d="M3.05 13A9 9 0 1 0 6 5.3L3 8"/><path d="M12 7v5l4 2"/></svg>',
  lake: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/><path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3"/></svg>',
  check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
  chevron: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>',
  empty: '<svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="8" y1="15" x2="16" y2="15"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>',
};
const CAT_ICONS = {
  signals: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12h4l3 8 4-16 3 8h6"/></svg>',
  states: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 2v6h-6"/><path d="M3 12a9 9 0 0 1 15-6.7L21 8"/><path d="M3 22v-6h6"/><path d="M21 12a9 9 0 0 1-15 6.7L3 16"/></svg>',
  requirements: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>',
  dtcs: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
  parameters: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/></svg>',
  relationships: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.5 1.5"/><path d="M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.5-1.5"/></svg>',
};

const esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const openCats = new Set();

/* ---------- Renderers ---------- */
function stepper(currentStage) {
  const idx = STAGES.indexOf(currentStage);
  let html = '<div class="stepper">';
  STAGES.forEach((st, i) => {
    const done = idx >= 0 && i < idx || currentStage === "integrated" && i <= idx;
    const active = i === idx && currentStage !== "integrated";
    const cls = done ? "done" : active ? "active" : "";
    html += `<div class="step ${cls}"><div class="step-dot">${ICONS.check}</div><div class="step-label">${STAGE_LABELS[st]}</div></div>`;
    if (i < STAGES.length - 1) html += `<div class="step-conn ${i < idx ? "done" : ""}"></div>`;
  });
  return html + "</div>";
}

function renderActive(state) {
  const el = document.getElementById("activePipeline");
  const jobs = Object.values(state.active_jobs || {});
  if (!jobs.length) {
    el.innerHTML = `<div class="empty">${ICONS.empty}<p>No documents processing. Upload a file to watch it flow through the pipeline.</p></div>`;
    return;
  }
  el.innerHTML = jobs.map((job) => {
    const ev = (job.events || []).slice(-3).map((e) =>
      `<div class="event"><span class="event-time">${esc((e.timestamp || "").slice(11, 19))}</span><span class="event-msg">${esc(e.message)}</span></div>`).join("");
    return `<div class="pipeline-card">
      <div class="pipeline-header">
        <span class="pipeline-file">${esc(job.filename)}</span>
        <span class="pipeline-id">${esc(job.job_id)}</span>
        <span class="badge ${job.current_stage}">${esc(job.current_stage)}</span>
      </div>
      ${stepper(job.current_stage)}
      ${ev ? `<div class="pipeline-events">${ev}</div>` : ""}
    </div>`;
  }).join("");
}

function renderHistory(state) {
  const el = document.getElementById("history");
  const jobs = (state.completed_jobs || []).slice().reverse();
  if (!jobs.length) {
    el.innerHTML = `<div class="empty">${ICONS.empty}<p>No documents processed yet.</p></div>`;
    return;
  }
  el.innerHTML = '<div class="timeline">' + jobs.map((job) => {
    const entities = job.extracted_entities ? Object.values(job.extracted_entities).reduce((a, b) => a + b, 0) : null;
    return `<div class="tl-item">
      <span class="tl-dot"></span>
      <div class="tl-head">
        <span class="tl-file">${esc(job.filename)}</span>
        <span class="badge ${job.current_stage}">${esc(job.current_stage)}</span>
      </div>
      <div class="tl-meta">
        <span>Categories: <b>${esc((job.categories || []).map((c) => CAT_NAMES[c] || c).join(", ") || "\u2014")}</b></span>
        ${entities != null ? `<span>Entities: <b>${entities}</b></span>` : ""}
        <span>Files: <b>${(job.data_lake_paths || []).length}</b></span>
      </div>
    </div>`;
  }).join("") + "</div>";
}

function renderLake(lake) {
  const el = document.getElementById("dataLake");
  const cats = Object.keys(lake);
  if (!cats.length) {
    el.innerHTML = `<div class="empty">${ICONS.empty}
      <p>The data lake is empty. Upload a document or process the bundled source specs to populate it.</p>
      <button class="btn btn-blue" id="processAllBtn">Process All Source Documents</button></div>`;
    const btn = document.getElementById("processAllBtn");
    if (btn) btn.onclick = processAll;
    return;
  }
  const ordered = cats.sort((a, b) => {
    const ia = CAT_ORDER.indexOf(a), ib = CAT_ORDER.indexOf(b);
    return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
  });
  el.innerHTML = '<div class="lake">' + ordered.map((cat) => {
    const files = lake[cat];
    const count = files.reduce((a, f) => a + (f.entry_count || 0), 0);
    const isOpen = openCats.has(cat);
    const body = files.map((f) => {
      const rows = (f.entries || []).slice(0, 5).map((e) =>
        `<div class="entry"><span class="entry-id">${esc(e.entry_id)}</span><span class="entry-src">${esc(e.source_document || "")}</span></div>`).join("");
      const more = (f.entries || []).length > 5 ? `<div class="entry more">\u2026 and ${f.entries.length - 5} more</div>` : "";
      return `<div class="lake-file">
        <div class="lf-head"><span class="lf-name">${esc(f.source_document || f.filename)}</span><span class="lf-count">${f.entry_count} entries</span></div>
        ${rows}${more}</div>`;
    }).join("");
    return `<div class="cat ${isOpen ? "open" : ""}" data-cat="${esc(cat)}">
      <div class="cat-head">
        <span class="cat-icon">${CAT_ICONS[cat] || CAT_ICONS.relationships}</span>
        <span class="cat-name">${CAT_NAMES[cat] || (cat.charAt(0).toUpperCase() + cat.slice(1))}</span>
        <span class="cat-count">${count}</span>
        <span class="cat-arrow">${ICONS.chevron}</span>
      </div>
      <div class="cat-body">${body}</div>
    </div>`;
  }).join("") + "</div>";
  el.querySelectorAll(".cat-head").forEach((h) => {
    h.onclick = () => {
      const c = h.parentElement.dataset.cat;
      h.parentElement.classList.toggle("open");
      if (openCats.has(c)) openCats.delete(c); else openCats.add(c);
    };
  });
}

/* ---------- Devin sessions ---------- */
function sessionStatusClass(status) {
  const s = (status || "").toLowerCase();
  if (s === "integrated" || s.includes("finish") || s.includes("complete")) return "done";
  if (s.includes("blocked") || s.includes("fail") || s.includes("error") || s.includes("expired")) return "blocked";
  return "running";
}

function renderSessions(sessions) {
  const section = document.getElementById("sessionsSection");
  const el = document.getElementById("sessions");
  if (!sessions || !sessions.length) {
    section.hidden = true;
    el.innerHTML = "";
    return;
  }
  section.hidden = false;
  el.innerHTML = sessions.slice().reverse().map((s) => {
    const cls = sessionStatusClass(s.status);
    const statusLabel = cls === "done" ? "Integrated" : cls === "blocked" ? esc(s.status) : "Devin working\u2026";
    const cats = (s.categories || []).map((c) => CAT_NAMES[c] || c).join(", ");
    const link = s.url
      ? `<a class="sess-link" href="${esc(s.url)}" target="_blank" rel="noopener">Open session ${ICONS.chevron}</a>`
      : "";
    const prLink = s.pr_url
      ? `<a class="sess-link" href="${esc(s.pr_url)}" target="_blank" rel="noopener">View pull request ${ICONS.chevron}</a>`
      : "";
    return `<div class="sess-card">
      <div class="sess-head">
        <span class="sess-spinner ${cls}"></span>
        <span class="sess-file">${esc(s.filename)}</span>
        <span class="badge ${cls === "done" ? "integrated" : cls}">${statusLabel}</span>
      </div>
      <div class="sess-meta">
        <span>Branch: <code>${esc(s.branch)}</code></span>
        ${s.session_id ? `<span>Session: <code>${esc(s.session_id)}</code></span>` : ""}
        ${s.entries_pulled ? `<span>Committed: <b>${s.entry_count}</b> entries${cats ? " \u2014 " + esc(cats) : ""}</span>` : ""}
      </div>
      <div class="sess-links">${link}${prLink}</div>
    </div>`;
  }).join("");
}

/* ---------- Polling ---------- */
async function refresh() {
  try {
    const [state, lake, sessions] = await Promise.all([
      fetch("/api/state").then((r) => r.json()),
      fetch("/api/data-lake").then((r) => r.json()),
      fetch("/api/sessions").then((r) => r.json()).catch(() => ({ sessions: [] })),
    ]);
    const entries = Object.values(lake).reduce((a, files) => a + files.reduce((x, f) => x + (f.entry_count || 0), 0), 0);
    const docs = new Set();
    Object.values(lake).forEach((files) => files.forEach((f) => { if (f.source_document) docs.add(f.source_document); }));
    document.getElementById("m-docs").textContent = docs.size;
    document.getElementById("m-entries").textContent = entries;
    document.getElementById("m-cats").textContent = Object.keys(lake).length;
    renderActive(state);
    renderHistory(state);
    renderSessions(sessions.sessions || []);
    renderLake(lake);
  } catch (e) { /* keep last good render */ }
}

/* ---------- Upload ---------- */
const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const uploadStatus = document.getElementById("uploadStatus");

["dragover"].forEach((ev) => dropZone.addEventListener(ev, (e) => { e.preventDefault(); dropZone.classList.add("drag-over"); }));
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
dropZone.addEventListener("drop", (e) => {
  e.preventDefault(); dropZone.classList.remove("drag-over");
  if (e.dataTransfer.files.length) uploadFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener("change", () => { if (fileInput.files.length) uploadFile(fileInput.files[0]); });

let uploadTick = null;

function setStatus(cls, msg) {
  uploadStatus.className = "upload-toast visible " + cls;
  uploadStatus.textContent = msg;
}

async function uploadFile(file) {
  setStatus("uploading", `Ingesting ${file.name}\u2026`);
  const el = document.getElementById("activePipeline");
  if (uploadTick) clearInterval(uploadTick);
  let step = 0;
  uploadTick = setInterval(() => {
    el.innerHTML = `<div class="pipeline-card">
      <div class="pipeline-header"><span class="pipeline-file">${esc(file.name)}</span>
      <span class="badge ${STAGES[step]}">${STAGES[step]}</span></div>${stepper(STAGES[step])}</div>`;
    step = Math.min(step + 1, STAGES.length - 1);
  }, 280);

  const fd = new FormData();
  fd.append("file", file);
  try {
    const resp = await fetch("/upload", { method: "POST", body: fd });
    const data = await resp.json();
    clearInterval(uploadTick);
    uploadTick = null;
    if (data.status === "session") {
      document.getElementById("activePipeline").innerHTML = "";
      setStatus("success", `${file.name} \u2014 Devin session launched to ingest it`);
    } else if (data.status === "success") {
      const cats = (data.job.categories || []).join(", ") || "no new categories";
      const hint = data.fallback_error
        ? `Devin session failed (${data.fallback_error}) \u2014 processed locally instead.`
        : "Set the Devin + GitHub tokens to spawn a real session.";
      setStatus(
        "success",
        `${file.name} processed locally (no Devin session) \u2014 ${cats}. ${hint}`,
      );
    } else {
      setStatus("error", `Error: ${data.error || "processing failed"}`);
    }
  } catch (err) {
    clearInterval(uploadTick);
    uploadTick = null;
    setStatus("error", `Upload failed: ${err.message}`);
  }
  await refresh();
}

async function processAll() {
  setStatus("uploading", "Processing all bundled source documents\u2026");
  try {
    const resp = await fetch("/api/process-all", { method: "POST" });
    const data = await resp.json();
    if (data.status === "success") setStatus("success", `Processed ${data.processed} source documents into the data lake.`);
    else setStatus("error", "Processing failed.");
  } catch (err) { setStatus("error", `Processing failed: ${err.message}`); }
  await refresh();
}

/* ---------- Icon injection ---------- */
function injectIcons(root) {
  (root || document).querySelectorAll("[data-ic]").forEach((n) => {
    const k = n.getAttribute("data-ic");
    if (ICONS[k]) { n.innerHTML = ICONS[k]; n.removeAttribute("data-ic"); }
  });
}

/* ---------- Sticky nav shadow on scroll ---------- */
const nav = document.getElementById("nav");
window.addEventListener("scroll", () => {
  nav.classList.toggle("scrolled", window.scrollY > 4);
}, { passive: true });

/* ---------- Ingestion mode badge ---------- */
async function renderMode() {
  const el = document.getElementById("modeBadge");
  if (!el) return;
  try {
    const cfg = await fetch("/api/config").then((r) => r.json());
    if (cfg.authentic_mode) {
      el.className = "nav-mode mode-authentic";
      el.textContent = "Authentic \u00b7 Devin sessions";
      el.title = "Dropped files spawn a real Devin session.";
    } else {
      el.className = "nav-mode mode-local";
      el.textContent = "Local fallback";
      el.title =
        "Dropped files are processed in-process (no Devin session). Missing: " +
        (cfg.missing_env || []).join(", ");
    }
    el.hidden = false;
  } catch (e) {
    el.hidden = true;
  }
}

/* ---------- Init ---------- */
injectIcons(document);
renderMode();
refresh();
setInterval(refresh, 3000);
