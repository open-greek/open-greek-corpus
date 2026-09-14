const state = {
  payload: null,
  items: [],
  visible: [],
  decisions: new Map(),
  currentId: null,
  zoom: 100,
};

const el = (id) => document.getElementById(id);

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
  })[char]);
}

function label(value) {
  return String(value || "").replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function itemTitle(item) { return item.observed || item.kind || item.item_id; }
function itemLocus(item) { return item.row?.locus || item.page || item.page_a?.locus || ""; }
function itemWork(item) { return item.row?.work || item.work?.slug || item.work || item.file || ""; }

function currentItem() {
  return state.items.find((item) => item.item_id === state.currentId) || state.visible[0];
}

function currentIndex() {
  return state.visible.findIndex((item) => item.item_id === state.currentId);
}

function renderProgress() {
  const done = state.decisions.size;
  const total = state.items.length;
  el("progress-label").textContent = `${done} / ${total}`;
  el("progress-bar").style.width = `${total ? (done / total) * 100 : 0}%`;
}

function renderList() {
  const filter = el("filter").value;
  state.visible = state.items.filter((item) => {
    const decision = state.decisions.get(item.item_id)?.decision;
    if (filter === "open") return !decision;
    if (filter === "decided") return Boolean(decision);
    if (filter === "defer") return decision === "defer";
    return true;
  });
  if (!state.visible.some((item) => item.item_id === state.currentId)) {
    state.currentId = state.visible[0]?.item_id || null;
  }
  el("item-list").innerHTML = state.visible.map((item) => {
    const decision = state.decisions.get(item.item_id)?.decision;
    const status = decision === "defer" ? "deferred" : decision ? "decided" : "";
    const active = item.item_id === state.currentId ? "active" : "";
    const absolute = state.items.findIndex((row) => row.item_id === item.item_id) + 1;
    return `<button class="queue-item ${status} ${active}" data-item="${escapeHtml(item.item_id)}">
      <span class="status-rail"></span>
      <span class="queue-copy"><strong lang="grc">${escapeHtml(itemTitle(item))}</strong><span>${escapeHtml(itemLocus(item))}</span></span>
      <span class="queue-number">${absolute}</span>
    </button>`;
  }).join("");
  document.querySelectorAll("[data-item]").forEach((button) => {
    button.addEventListener("click", () => selectItem(button.dataset.item));
  });
}

function renderContext(item) {
  const parts = String(item.context || "").split("<TARGET>");
  if (parts.length === 2) {
    el("context").innerHTML = `${escapeHtml(parts[0])}<mark>${escapeHtml(item.observed || "target")}</mark>${escapeHtml(parts[1])}`;
  } else {
    el("context").textContent = item.context || item.text || "";
  }
}

function renderCandidates(item) {
  const candidates = item.candidate_readings || [];
  el("candidates").innerHTML = candidates.length ? candidates.map((candidate) => (
    `<button type="button" class="candidate" data-reading="${escapeHtml(candidate.reading)}">
      ${escapeHtml(candidate.reading)} <small>${escapeHtml(candidate.kind)}</small>
    </button>`
  )).join("") : `<span class="empty-state">None</span>`;
  document.querySelectorAll("[data-reading]").forEach((button) => {
    button.addEventListener("click", () => {
      el("reading").value = button.dataset.reading;
      const decision = button.dataset.reading.includes(" ") ? "split" : "replace";
      document.querySelector(`input[name="decision"][value="${decision}"]`)?.click();
    });
  });
}

function renderDecisions(item, saved) {
  el("decision-options").innerHTML = item.allowed_decisions.map((choice) => (
    `<label><input type="radio" name="decision" value="${escapeHtml(choice)}" ${saved?.decision === choice ? "checked" : ""}><span>${escapeHtml(label(choice))}</span></label>`
  )).join("");
  document.querySelectorAll('input[name="decision"]').forEach((input) => {
    input.addEventListener("change", updateReadingVisibility);
  });
  el("reading").value = saved?.reading || "";
  el("evidence-url").value = saved?.evidence_url || item.scan_url || "";
  el("notes").value = saved?.notes || "";
  el("form-error").textContent = "";
  updateReadingVisibility();
}

function updateReadingVisibility() {
  const item = currentItem();
  const choice = document.querySelector('input[name="decision"]:checked')?.value;
  el("reading-field").hidden = !item?.reading_required_for?.includes(choice);
}

function renderScan(item) {
  const image = el("scan-image");
  const empty = el("scan-empty");
  el("scan-link").href = item.scan_url || "#";
  el("scan-link").toggleAttribute("hidden", !item.scan_url);
  if (item.image_url) {
    image.src = item.image_url;
    image.style.display = "block";
    image.style.width = `${state.zoom}%`;
    empty.hidden = true;
  } else {
    image.removeAttribute("src");
    image.style.display = "none";
    empty.hidden = false;
  }
}

function renderItem() {
  const item = currentItem();
  if (!item) return;
  state.currentId = item.item_id;
  const index = currentIndex();
  const saved = state.decisions.get(item.item_id);
  el("work-name").textContent = itemWork(item);
  el("locus").textContent = itemLocus(item);
  el("position").textContent = `${index + 1} of ${state.visible.length}`;
  el("observed").textContent = item.observed || "";
  el("previous").disabled = index <= 0;
  el("next").disabled = index < 0 || index >= state.visible.length - 1;
  renderContext(item);
  renderCandidates(item);
  renderDecisions(item, saved);
  renderScan(item);
  renderList();
  window.lucide?.createIcons();
}

function selectItem(itemId) {
  state.currentId = itemId;
  renderItem();
}

function move(offset) {
  const next = currentIndex() + offset;
  if (next >= 0 && next < state.visible.length) selectItem(state.visible[next].item_id);
}

async function saveDecision(event) {
  event.preventDefault();
  const item = currentItem();
  const absoluteIndex = state.items.findIndex((row) => row.item_id === item.item_id);
  const candidate = {
    item_id: item.item_id,
    decision: document.querySelector('input[name="decision"]:checked')?.value || "",
    reading: el("reading").value.trim(),
    evidence_url: el("evidence-url").value.trim(),
    reviewer: el("reviewer").value.trim(),
    reviewed_at: new Date().toISOString().slice(0, 10),
    notes: el("notes").value.trim(),
  };
  const submit = document.querySelector(".save-button");
  submit.disabled = true;
  el("form-error").textContent = "";
  try {
    const response = await fetch("/api/decision", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(candidate),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || "Decision was not saved");
    state.decisions.set(item.item_id, body.decision);
    renderProgress();
    renderList();
    const next = state.visible.find((row) => state.items.indexOf(row) > absoluteIndex)
      || state.visible[state.visible.length - 1];
    state.currentId = next?.item_id || null;
    renderItem();
  } catch (error) {
    el("form-error").textContent = error.message;
  } finally {
    submit.disabled = false;
  }
}

function setZoom(value) {
  state.zoom = Math.max(50, Math.min(240, value));
  el("zoom").value = state.zoom;
  const image = el("scan-image");
  if (image.src) image.style.width = `${state.zoom}%`;
}

async function init() {
  const response = await fetch("/api/review");
  state.payload = await response.json();
  state.items = state.payload.items;
  state.visible = state.items;
  state.decisions = new Map(Object.entries(state.payload.decisions));
  state.currentId = state.items[0]?.item_id || null;
  el("queue-name").textContent = state.payload.queue;
  el("reviewer").value = localStorage.getItem("ogc-reviewer") || "";
  el("reviewer").addEventListener("change", () => {
    localStorage.setItem("ogc-reviewer", el("reviewer").value.trim());
  });
  el("filter").addEventListener("change", () => { renderList(); renderItem(); });
  el("previous").addEventListener("click", () => move(-1));
  el("next").addEventListener("click", () => move(1));
  el("zoom-out").addEventListener("click", () => setZoom(state.zoom - 10));
  el("zoom-in").addEventListener("click", () => setZoom(state.zoom + 10));
  el("zoom").addEventListener("input", (event) => setZoom(Number(event.target.value)));
  el("decision-form").addEventListener("submit", saveDecision);
  document.addEventListener("keydown", (event) => {
    const editing = ["INPUT", "TEXTAREA", "SELECT"].includes(event.target.tagName);
    if (!editing && event.key === "ArrowLeft") move(-1);
    if (!editing && event.key === "ArrowRight") move(1);
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") el("decision-form").requestSubmit();
  });
  renderProgress();
  renderList();
  renderItem();
}

init().catch((error) => {
  document.body.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
});
