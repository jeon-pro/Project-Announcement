const state = {
  items: [],
  activeSources: new Set(),
  query: "",
};

const listEl = document.getElementById("list");
const emptyEl = document.getElementById("empty");
const updatedEl = document.getElementById("updated-at");
const searchEl = document.getElementById("search");
const filtersEl = document.getElementById("source-filters");

async function loadData() {
  try {
    const res = await fetch("data/projects.json", { cache: "no-store" });
    if (!res.ok) throw new Error("data fetch failed: " + res.status);
    const data = await res.json();

    state.items = data.items || [];
    updatedEl.textContent = data.generated_at
      ? `마지막 업데이트: ${new Date(data.generated_at).toLocaleString("ko-KR")} · 총 ${state.items.length}건`
      : `총 ${state.items.length}건`;

    buildFilters();
    render();
  } catch (err) {
    console.error(err);
    updatedEl.textContent = "데이터를 불러오지 못했습니다.";
    emptyEl.classList.remove("hidden");
  }
}

function buildFilters() {
  const sources = [...new Set(state.items.map((i) => i.source))].sort();
  filtersEl.innerHTML = "";
  sources.forEach((src) => {
    const chip = document.createElement("button");
    chip.className = "filter-chip active";
    chip.textContent = src;
    chip.dataset.source = src;
    chip.addEventListener("click", () => toggleSource(src, chip));
    filtersEl.appendChild(chip);
    state.activeSources.add(src);
  });
}

function toggleSource(src, chip) {
  if (state.activeSources.has(src)) {
    state.activeSources.delete(src);
    chip.classList.remove("active");
  } else {
    state.activeSources.add(src);
    chip.classList.add("active");
  }
  render();
}

searchEl.addEventListener("input", (e) => {
  state.query = e.target.value.trim().toLowerCase();
  render();
});

function render() {
  const filtered = state.items.filter((item) => {
    const matchesSource = state.activeSources.has(item.source);
    const matchesQuery =
      !state.query ||
      (item.title || "").toLowerCase().includes(state.query) ||
      (item.tags || []).join(" ").toLowerCase().includes(state.query);
    return matchesSource && matchesQuery;
  });

  listEl.innerHTML = "";
  emptyEl.classList.toggle("hidden", filtered.length > 0);

  filtered
    .sort((a, b) => new Date(b.posted_at || 0) - new Date(a.posted_at || 0))
    .forEach((item) => {
      const card = document.createElement("a");
      card.className = "card";
      card.href = item.url;
      card.target = "_blank";
      card.rel = "noopener noreferrer";
      card.innerHTML = `
        <span class="source">${escapeHtml(item.source)}</span>
        <span class="title">${escapeHtml(item.title)}</span>
        <span class="meta">
          <span>${escapeHtml(item.budget || "")}</span>
          <span>${escapeHtml(item.posted_at ? formatDate(item.posted_at) : "")}</span>
        </span>
      `;
      listEl.appendChild(card);
    });
}

function formatDate(iso) {
  const d = new Date(iso);
  if (isNaN(d)) return iso;
  return d.toLocaleDateString("ko-KR", { month: "2-digit", day: "2-digit" });
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

loadData();
