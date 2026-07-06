const state = {
  items: [],
  activeSources: new Set(),
  activeWorkType: "전체",   // "전체" | "상주" | "원격"
  query: "",
};

const listEl    = document.getElementById("list");
const emptyEl   = document.getElementById("empty");
const updatedEl = document.getElementById("updated-at");
const searchEl  = document.getElementById("search");
const filtersEl = document.getElementById("source-filters");
const workFiltersEl = document.getElementById("work-type-filters");

async function loadData() {
  try {
    const res = await fetch("data/projects.json", { cache: "no-store" });
    if (!res.ok) throw new Error("data fetch failed: " + res.status);
    const data = await res.json();

    state.items = data.items || [];
    updatedEl.textContent = data.generated_at
      ? `마지막 업데이트: ${new Date(data.generated_at).toLocaleString("ko-KR")} · 총 ${state.items.length}건`
      : `총 ${state.items.length}건`;

    buildSourceFilters();
    buildWorkTypeFilters();
    render();
  } catch (err) {
    console.error(err);
    updatedEl.textContent = "데이터를 불러오지 못했습니다.";
    emptyEl.classList.remove("hidden");
  }
}

// ── 사이트 필터 ──────────────────────────────────────────────────
function buildSourceFilters() {
  const sources = [...new Set(state.items.map((i) => i.source))].sort();
  filtersEl.innerHTML = "";
  sources.forEach((src) => {
    const chip = document.createElement("button");
    chip.className = "filter-chip active";
    chip.textContent = src;
    chip.dataset.source = src;
    chip.addEventListener("click", () => {
      const isActive = state.activeSources.has(src);
      if (isActive) {
        state.activeSources.delete(src);
        chip.classList.remove("active");
      } else {
        state.activeSources.add(src);
        chip.classList.add("active");
      }
      render();
    });
    filtersEl.appendChild(chip);
    state.activeSources.add(src);
  });
}

// ── 근무형태 필터 ────────────────────────────────────────────────
function buildWorkTypeFilters() {
  const types = ["전체", "상주", "원격"];
  workFiltersEl.innerHTML = "";
  types.forEach((type) => {
    const chip = document.createElement("button");
    chip.className = "filter-chip work-chip" + (type === "전체" ? " active" : "");
    chip.textContent = type;
    chip.addEventListener("click", () => {
      state.activeWorkType = type;
      workFiltersEl.querySelectorAll(".work-chip").forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      render();
    });
    workFiltersEl.appendChild(chip);
  });
}

// ── 검색 ─────────────────────────────────────────────────────────
searchEl.addEventListener("input", (e) => {
  state.query = e.target.value.trim().toLowerCase();
  render();
});

// ── work_type 판별 ───────────────────────────────────────────────
function getWorkType(item) {
  // 스크래퍼가 work_type 필드를 넣어줬으면 그대로 사용
  if (item.work_type) return item.work_type;

  // 없으면 title·tags에서 추론
  const haystack = [item.title, ...(item.tags || [])].join(" ");
  if (/상주/.test(haystack))  return "상주";
  if (/원격|재택|리모트|remote/i.test(haystack)) return "원격";
  return "기타";
}

// ── 렌더링 ───────────────────────────────────────────────────────
function render() {
  const filtered = state.items.filter((item) => {
    if (!state.activeSources.has(item.source)) return false;

    if (state.activeWorkType !== "전체") {
      if (getWorkType(item) !== state.activeWorkType) return false;
    }

    if (state.query) {
      const hay = [item.title, ...(item.tags || []), item.budget]
        .join(" ").toLowerCase();
      if (!hay.includes(state.query)) return false;
    }

    return true;
  });

  listEl.innerHTML = "";
  emptyEl.classList.toggle("hidden", filtered.length > 0);

  filtered
    .sort((a, b) => new Date(b.posted_at || 0) - new Date(a.posted_at || 0))
    .forEach((item) => {
      const workType = getWorkType(item);
      const card = document.createElement("a");
      card.className = "card";
      card.href = item.url;
      card.target = "_blank";
      card.rel = "noopener noreferrer";

      card.innerHTML = `
        <div class="card-top">
          <span class="source">${escapeHtml(item.source)}</span>
          <span class="work-badge work-badge--${workType === '상주' ? 'onsite' : workType === '원격' ? 'remote' : 'etc'}">
            ${escapeHtml(workType)}
          </span>
        </div>
        <span class="title">${escapeHtml(item.title)}</span>
        <div class="tags">
          ${(item.tags || []).slice(0, 4).map(t =>
            `<span class="tag">${escapeHtml(t)}</span>`
          ).join("")}
        </div>
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
