const PREFECTURES = [
  ["北海道", "北海道", 9, 0],
  ["青森県", "東北", 8, 3], ["岩手県", "東北", 9, 4], ["宮城県", "東北", 9, 5],
  ["秋田県", "東北", 8, 4], ["山形県", "東北", 8, 5], ["福島県", "東北", 9, 6],
  ["茨城県", "関東", 10, 7], ["栃木県", "関東", 9, 7], ["群馬県", "関東", 8, 7],
  ["埼玉県", "関東", 9, 8], ["千葉県", "関東", 10, 9], ["東京都", "関東", 9, 9], ["神奈川県", "関東", 9, 10],
  ["新潟県", "中部", 7, 6], ["富山県", "中部", 6, 7], ["石川県", "中部", 5, 7], ["福井県", "中部", 5, 8],
  ["山梨県", "中部", 8, 9], ["長野県", "中部", 7, 8], ["岐阜県", "中部", 6, 9], ["静岡県", "中部", 8, 10], ["愛知県", "中部", 7, 10],
  ["三重県", "近畿", 7, 11], ["滋賀県", "近畿", 6, 10], ["京都府", "近畿", 5, 10], ["大阪府", "近畿", 5, 11],
  ["兵庫県", "近畿", 4, 10], ["奈良県", "近畿", 6, 11], ["和歌山県", "近畿", 6, 12],
  ["鳥取県", "中国", 3, 9], ["島根県", "中国", 2, 9], ["岡山県", "中国", 3, 10], ["広島県", "中国", 2, 10], ["山口県", "中国", 1, 10],
  ["徳島県", "四国", 4, 12], ["香川県", "四国", 4, 11], ["愛媛県", "四国", 3, 12], ["高知県", "四国", 3, 13],
  ["福岡県", "九州・沖縄", 1, 12], ["佐賀県", "九州・沖縄", 0, 13], ["長崎県", "九州・沖縄", 0, 14],
  ["熊本県", "九州・沖縄", 1, 13], ["大分県", "九州・沖縄", 2, 13], ["宮崎県", "九州・沖縄", 2, 14],
  ["鹿児島県", "九州・沖縄", 1, 15], ["沖縄県", "九州・沖縄", 0, 17],
].map(([pref, region, x, y]) => ({
  pref,
  label: pref === "北海道" ? pref : pref.replace(/[都府県]$/, ""),
  region,
  x,
  y,
}));

const REGION_ORDER = ["北海道", "東北", "関東", "中部", "近畿", "中国", "四国", "九州・沖縄"];
const PREFECTURE_META = new Map(PREFECTURES.map((item) => [item.pref, item]));

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    if (quoted) {
      if (char === '"' && text[i + 1] === '"') {
        field += '"';
        i += 1;
      } else if (char === '"') {
        quoted = false;
      } else {
        field += char;
      }
    } else if (char === '"') {
      quoted = true;
    } else if (char === ",") {
      row.push(field);
      field = "";
    } else if (char === "\n") {
      row.push(field.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      field = "";
    } else {
      field += char;
    }
  }
  if (field || row.length) {
    row.push(field.replace(/\r$/, ""));
    rows.push(row);
  }
  return rows;
}

function numberOrNull(value) {
  return value === "" ? null : Number(value);
}

async function loadObservations() {
  const response = await fetch("/cedar-pollen-bi/api/v1/observations.csv", { cache: "no-cache" });
  if (!response.ok) throw new Error(`Failed to load observations: HTTP ${response.status}`);
  const csvRows = parseCsv(await response.text());
  const header = csvRows.shift();
  const index = Object.fromEntries(header.map((name, i) => [name, i]));
  return csvRows.filter((row) => row.length > 1).map((row) => {
    const pref = row[index.prefecture_name_ja];
    return {
      pref,
      region: PREFECTURE_META.get(pref)?.region ?? "",
      observation: numberOrNull(row[index.observation_count_per_m2]),
      baseline: numberOrNull(row[index.baseline_average_count_per_m2]),
      ratio: numberOrNull(row[index.official_comparison_percent]),
      baselineNote: row[index.baseline_note] ?? "",
      sourceUrl: row[index.source_url] ?? "",
    };
  });
}

const observations = await loadObservations();
const comparable = observations.filter((item) => Number.isFinite(item.ratio));
const observationByPrefecture = new Map(observations.map((item) => [item.pref, item]));

const search = document.querySelector("#search");
const band = document.querySelector("#band");
const sort = document.querySelector("#sort");
const reset = document.querySelector("#reset");
const barChart = document.querySelector("#barChart");
const rows = document.querySelector("#rows");
const countLabel = document.querySelector("#countLabel");
const japanMap = document.querySelector("#japanMap");
const tooltip = document.querySelector("#tooltip");
let selected = "";

function category(item) {
  return item.ratio >= 200 ? "high" : item.ratio <= 50 ? "low" : "mid";
}

function categoryLabel(value) {
  return value === "high" ? "200%以上" : value === "low" ? "50%以下" : "50%超から200%未満";
}

function comparisonReason(item) {
  if (Number.isFinite(item?.ratio)) return "";
  if (item?.baselineNote.includes("new observation") && item.baseline == null) {
    return "新規観測のため過去平均なし";
  }
  if (item?.baseline == null) return "過去平均なし";
  return "比較不能";
}

function matchesQuery(item, query) {
  return !query || item.pref.includes(query) || item.region.includes(query);
}

function filteredRows() {
  const query = search.value.trim();
  return observations
    .filter((item) => matchesQuery(item, query))
    .filter((item) => band.value === "all" || Number.isFinite(item.ratio) && category(item) === band.value)
    .sort((a, b) => {
      const aComparable = Number.isFinite(a.ratio);
      const bComparable = Number.isFinite(b.ratio);
      if (aComparable !== bComparable) return aComparable ? -1 : 1;
      if (!aComparable) return a.pref.localeCompare(b.pref, "ja");
      if (sort.value === "asc") return a.ratio - b.ratio;
      if (sort.value === "region") return REGION_ORDER.indexOf(a.region) - REGION_ORDER.indexOf(b.region) || b.ratio - a.ratio;
      return b.ratio - a.ratio;
    });
}

function showTooltip(item, x, y) {
  if (!item || item.ratio == null) {
    const observationText = Number.isFinite(item?.observation) ? `${item.observation}個/m²` : "観測値なし";
    tooltip.innerHTML = `<strong>${item?.pref ?? ""}</strong><span>${observationText} / ${comparisonReason(item)}</span>`;
  } else {
    tooltip.innerHTML = `<strong>${item.pref}</strong><span>${item.ratio}% / ${categoryLabel(category(item))}</span><span>観測 ${item.observation}個/m² / 基準 ${item.baseline}個/m²</span>`;
  }
  tooltip.style.left = `${Math.min(x + 14, window.innerWidth - 250)}px`;
  tooltip.style.top = `${Math.max(y - 22, 12)}px`;
  tooltip.style.display = "block";
}

function hideTooltip() {
  tooltip.style.display = "none";
}

function selectPrefecture(prefecture) {
  selected = selected === prefecture ? "" : prefecture;
  render();
}

function renderBars(items) {
  barChart.innerHTML = "";
  for (const item of items.filter((row) => Number.isFinite(row.ratio))) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `bar-row ${selected === item.pref ? "active" : ""}`;
    button.style.border = "0";
    button.style.background = selected === item.pref ? "rgb(23 107 77 / 0.08)" : "transparent";
    button.style.width = "100%";
    button.style.padding = "3px";
    button.setAttribute("aria-label", `${item.pref} ${item.ratio}%`);
    button.innerHTML = `<span class="pref">${item.pref}</span><span class="track"><span class="bar ${category(item)}" style="--value:${item.ratio}"></span></span><span class="value">${item.ratio}%</span>`;
    button.addEventListener("click", () => selectPrefecture(item.pref));
    button.addEventListener("pointermove", (event) => showTooltip(item, event.clientX, event.clientY));
    button.addEventListener("pointerleave", hideTooltip);
    barChart.append(button);
  }
}

function renderTable(items) {
  rows.innerHTML = "";
  for (const item of items) {
    const tr = document.createElement("tr");
    if (selected === item.pref) tr.style.background = "rgb(23 107 77 / 0.08)";
    if (Number.isFinite(item.ratio)) {
      const itemCategory = category(item);
      tr.innerHTML = `<td>${item.pref}</td><td>${item.region}</td><td>${item.ratio}%</td><td>${item.ratio - 100 > 0 ? "+" : ""}${item.ratio - 100}pt</td><td><span class="badge ${itemCategory}">${categoryLabel(itemCategory)}</span></td><td><a href="${item.sourceUrl}">環境省 資料1</a></td>`;
      tr.addEventListener("click", () => selectPrefecture(item.pref));
    } else {
      tr.innerHTML = `<td>${item.pref}</td><td>${item.region}</td><td>—</td><td>—</td><td>${comparisonReason(item)}</td><td><a href="${item.sourceUrl}">環境省 資料1</a></td>`;
    }
    rows.append(tr);
  }
}

function renderMap(items) {
  const visible = new Set(items.filter((item) => Number.isFinite(item.ratio)).map((item) => item.pref));
  const tile = 34;
  const gap = 6;
  const origin = { x: 38, y: 18 };
  japanMap.innerHTML = "";
  for (const meta of PREFECTURES) {
    const observation = observationByPrefecture.get(meta.pref);
    const hasRatio = Number.isFinite(observation?.ratio);
    const isVisible = hasRatio && visible.has(meta.pref);
    const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
    group.setAttribute("class", ["pref-tile", hasRatio ? "has-data" : "no-data", hasRatio ? category(observation) : "", hasRatio && !isVisible ? "hidden" : "", selected === meta.pref ? "selected" : ""].filter(Boolean).join(" "));
    group.setAttribute("transform", `translate(${origin.x + meta.x * (tile + gap)}, ${origin.y + meta.y * (tile + gap)})`);
    group.setAttribute("aria-label", hasRatio ? `${meta.pref} ${observation.ratio}%` : `${meta.pref} ${comparisonReason(observation)}`);
    group.setAttribute("tabindex", "0");
    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("width", tile);
    rect.setAttribute("height", tile);
    rect.setAttribute("rx", "7");
    rect.setAttribute("ry", "7");
    group.append(rect);
    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("x", tile / 2);
    text.setAttribute("y", tile / 2 + 4);
    text.textContent = meta.label;
    group.append(text);
    group.addEventListener("pointermove", (event) => showTooltip(observation ?? { pref: meta.pref, ratio: null }, event.clientX, event.clientY));
    group.addEventListener("pointerleave", hideTooltip);
    if (hasRatio) {
      group.addEventListener("click", () => selectPrefecture(meta.pref));
    }
    group.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        showTooltip(observation ?? { pref: meta.pref, ratio: null }, window.innerWidth / 2, 80);
        if (hasRatio) selectPrefecture(meta.pref);
      }
    });
    japanMap.append(group);
  }
}

function renderMetrics() {
  const ratios = comparable.map((item) => item.ratio);
  document.querySelector("#metricMax").textContent = `${Math.max(...ratios)}%`;
  document.querySelector("#metricMin").textContent = `${Math.min(...ratios)}%`;
  document.querySelector("#metricHigh").textContent = comparable.filter((item) => category(item) === "high").length;
  document.querySelector("#metricLow").textContent = comparable.filter((item) => category(item) === "low").length;
}

function render() {
  const items = filteredRows();
  const comparableCount = items.filter((item) => Number.isFinite(item.ratio)).length;
  const notComparableCount = items.length - comparableCount;
  countLabel.textContent = notComparableCount ? `${comparableCount}件 + 比較不能${notComparableCount}件` : `${comparableCount}件`;
  renderBars(items);
  renderTable(items);
  renderMap(items);
  renderMetrics();
}

for (const control of [search, band, sort]) {
  control.addEventListener("input", () => {
    selected = "";
    hideTooltip();
    render();
  });
}
reset.addEventListener("click", () => {
  search.value = "";
  band.value = "all";
  sort.value = "desc";
  selected = "";
  hideTooltip();
  render();
});

render();
