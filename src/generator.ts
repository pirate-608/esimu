import * as fs from "node:fs";
import * as path from "node:path";
import type { GameConfig } from "./utils/types";

const LIVE_RELOAD_SCRIPT = `
<script>
(function() {
  var es = new EventSource("/__esimu_live");
  es.addEventListener("reload", function() {
    es.close();
    location.reload();
  });
  es.onerror = function() {
    setTimeout(function() { es.close(); }, 3000);
  };
})();
</script>`;

export function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

export function generateHTML(config: GameConfig, liveReload = false): string {
  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escapeHtml(config.title)}</title>
  <link rel="stylesheet" href="css/style.css">
</head>
<body class="dark-theme">
  <div id="app">
    <div id="screen-character-creation" class="screen">
      <h1 class="game-title">${escapeHtml(config.title)}</h1>
      <p class="game-description">${escapeHtml(config.description)}</p>
      <div id="character-form"></div>
      <button id="btn-start-game" class="btn btn-primary" disabled>开始冒险</button>
    </div>
    <div id="screen-game" class="screen hidden">
      <div id="stats-panel"></div>
      <div id="event-area">
        <h2 id="event-title"></h2>
        <div id="event-description"></div>
        <div id="choices-container"></div>
      </div>
    </div>
    <div id="screen-ending" class="screen hidden">
      <h2 id="ending-title"></h2>
      <div id="ending-description"></div>
      <button id="btn-restart" class="btn btn-primary">重新开始</button>
    </div>
  </div>
  <script src="js/game.js"></script>${liveReload ? LIVE_RELOAD_SCRIPT : ""}
</body>
</html>`;
}

export function generateCSS(): string {
  return `:root {
  --bg: #1a1a2e;
  --surface: #16213e;
  --surface-alt: #0f3460;
  --text: #e0e0e0;
  --text-muted: #a0a0b0;
  --accent: #e94560;
  --border: #0f3460;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  line-height: 1.6;
  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
}

#app {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.screen { display: flex; flex-direction: column; gap: 20px; }
.hidden { display: none !important; }

.game-title { font-size: 2rem; text-align: center; color: var(--accent); }
.game-description { text-align: center; color: var(--text-muted); margin-bottom: 20px; }

#stats-panel {
  display: flex; flex-wrap: wrap; gap: 8px;
  padding: 12px;
  background: var(--surface);
  border-radius: 8px;
  border: 1px solid var(--border);
}

.stat-item {
  padding: 4px 10px;
  background: var(--surface-alt);
  border-radius: 4px;
  font-size: 0.9rem;
}

.stat-item .stat-name { color: var(--accent); margin-right: 4px; }

.stat-allocator {
  display: flex; align-items: center; gap: 10px; margin: 5px 0;
}

.stat-allocator label { min-width: 80px; font-weight: bold; color: var(--accent); }

.stat-allocator input {
  width: 80px; padding: 5px 10px;
  background: var(--surface-alt);
  border: 1px solid var(--accent);
  border-radius: 4px;
  color: var(--text); font-size: 1rem;
}

.stat-allocator span { color: var(--text-muted); font-size: 0.85rem; }

#points-remaining {
  padding: 10px; background: var(--surface);
  border-radius: 4px; text-align: center;
  font-weight: bold; color: var(--accent);
}

#event-area {
  background: var(--surface);
  border-radius: 8px;
  padding: 25px;
  border: 1px solid var(--border);
}

#event-title { color: var(--accent); margin-bottom: 15px; font-size: 1.5rem; }

#event-description { margin-bottom: 20px; line-height: 1.8; }

#event-description h1, #event-description h2, #event-description h3 {
  color: var(--accent); margin: 15px 0 10px;
}

#event-description ul, #event-description ol { margin: 10px 0 10px 20px; }

#event-description blockquote {
  border-left: 3px solid var(--accent);
  padding: 10px 15px; margin: 10px 0;
  background: var(--surface-alt);
  border-radius: 0 4px 4px 0;
}

#event-description code {
  background: var(--surface-alt);
  padding: 2px 6px; border-radius: 3px;
  font-size: 0.9em;
}

#choices-container { display: flex; flex-direction: column; gap: 10px; }

.btn {
  padding: 12px 24px; border: none; border-radius: 6px;
  font-size: 1rem; cursor: pointer;
  transition: opacity 0.2s;
}

.btn:hover { opacity: 0.85; }

.btn-primary { background: var(--accent); color: #fff; }

.btn-primary:disabled { background: #555; cursor: not-allowed; opacity: 1; }

.btn-choice {
  background: var(--surface-alt); color: var(--text);
  text-align: left;
  border: 1px solid #1a4a8a;
}

.btn-choice:hover { border-color: var(--accent); }

.btn-choice:disabled { opacity: 0.5; cursor: not-allowed; }

#screen-ending {
  text-align: center; justify-content: center;
  align-items: center; min-height: 60vh;
}

#ending-title { font-size: 2rem; color: var(--accent); }

#ending-description { font-size: 1.1rem; color: var(--text-muted); max-width: 500px; line-height: 1.8; }

@media (max-width: 600px) {
  #app { padding: 10px; }
  .game-title { font-size: 1.5rem; }
  #stats-panel { gap: 5px; }
  .stat-item { font-size: 0.8rem; padding: 3px 8px; }
  #event-area { padding: 15px; }
}`;
}

/**
 * Returns custom CSS if configured in game.yml, otherwise the generated default.
 * Path is resolved relative to the config file directory.
 */
export function resolveCSS(config: GameConfig, baseDir: string): string {
  if (config.css) {
    return fs.readFileSync(path.resolve(baseDir, config.css), "utf-8");
  }
  return generateCSS();
}

export function generateGameJS(
  config: GameConfig,
  descriptions: string[]
): string {
  const serializedConfig = JSON.stringify(config);
  const serializedDescriptions = JSON.stringify(descriptions);

  return `// Generated by esimu — do not edit manually
const GAME_CONFIG = ${serializedConfig};
const EVENT_DESCRIPTIONS = ${serializedDescriptions};

let state = {
  currentEvent: "start",
  stats: {},
  history: [],
};

function init() {
  for (const [key, stat] of Object.entries(GAME_CONFIG.stats)) {
    state.stats[key] = stat.default;
  }
}

function getStat(key) {
  return state.stats[key] ?? 0;
}

function setStat(key, value) {
  const stat = GAME_CONFIG.stats[key];
  state.stats[key] = Math.max(stat.min, Math.min(stat.max, value));
}

function applyEffects(effects) {
  if (!effects) return;
  for (const [key, delta] of Object.entries(effects)) {
    setStat(key, getStat(key) + delta);
  }
}

function checkCondition(condition) {
  if (!condition) return true;
  for (const [key, threshold] of Object.entries(condition)) {
    if (getStat(key) < threshold) return false;
  }
  return true;
}

function findEvent(id) {
  return GAME_CONFIG.events.find((e) => e.id === id);
}

function showScreen(screenId) {
  document.querySelectorAll(".screen").forEach((s) => s.classList.add("hidden"));
  document.getElementById(screenId).classList.remove("hidden");
}

function renderStats() {
  const panel = document.getElementById("stats-panel");
  if (!panel) return;
  panel.innerHTML = Object.entries(GAME_CONFIG.stats)
    .map(
      ([key, stat]) =>
        \`<div class="stat-item"><span class="stat-name">\${stat.name}</span> \${getStat(key)}/\${stat.max}</div>\`
    )
    .join("");
}

function renderEvent(eventId) {
  const event = findEvent(eventId);
  if (!event) {
    console.error("Event not found:", eventId);
    return;
  }

  state.currentEvent = eventId;
  state.history.push(eventId);

  document.getElementById("event-title").textContent = event.title;

  const descIdx = GAME_CONFIG.events.findIndex((e) => e.id === eventId);
  document.getElementById("event-description").innerHTML =
    EVENT_DESCRIPTIONS[descIdx] || "";

  const container = document.getElementById("choices-container");
  container.innerHTML = "";

  for (const choice of event.choices) {
    const btn = document.createElement("button");
    btn.className = "btn btn-choice";
    btn.textContent = choice.text;

    if (!checkCondition(choice.condition)) {
      btn.disabled = true;
      btn.textContent += " (条件不满足)";
    } else {
      btn.addEventListener("click", () => {
        applyEffects(choice.effects);
        handleNextEvent(choice.next_event);
      });
    }

    container.appendChild(btn);
  }

  renderStats();
  showScreen("screen-game");
}

function handleNextEvent(nextId) {
  if (nextId.startsWith("ending_") || GAME_CONFIG.endings.some((e) => {
    if (e.condition && checkCondition(e.condition)) return true;
    return false;
  })) {
    checkEndings();
    return;
  }
  renderEvent(nextId);
}

function checkEndings() {
  for (const ending of GAME_CONFIG.endings) {
    if (ending.default) continue;
    if (ending.condition && checkCondition(ending.condition)) {
      showEnding(ending);
      return;
    }
  }

  const defaultEnding = GAME_CONFIG.endings.find((e) => e.default);
  if (defaultEnding) {
    showEnding(defaultEnding);
  }
}

function showEnding(ending) {
  document.getElementById("ending-title").textContent = ending.title;
  document.getElementById("ending-description").textContent = ending.description;
  showScreen("screen-ending");
}

function buildCharacterForm() {
  const form = document.getElementById("character-form");
  if (!form) return;

  const cc = GAME_CONFIG.character_creation;
  form.innerHTML = \`
    <div id="points-remaining">剩余点数: \${cc.total_points}</div>
    \${cc.assignable
      .map(
        (key) => \`
      <div class="stat-allocator">
        <label>\${GAME_CONFIG.stats[key].name}</label>
        <input type="number" id="alloc-\${key}" value="\${GAME_CONFIG.stats[key].default}" min="\${GAME_CONFIG.stats[key].min}" max="\${GAME_CONFIG.stats[key].max}">
        <span>(基础: \${GAME_CONFIG.stats[key].default})</span>
      </div>\`
      )
      .join("")}
  \`;

  const btn = document.getElementById("btn-start-game");
  const updatePoints = () => {
    let used = 0;
    let valid = true;
    for (const key of cc.assignable) {
      const input = document.getElementById("alloc-" + key);
      const val = parseInt(input?.value || "0", 10);
      const stat = GAME_CONFIG.stats[key];
      if (isNaN(val) || val < stat.min || val > stat.max) valid = false;
      used += val - stat.default;
    }
    document.getElementById("points-remaining").textContent =
      "剩余点数: " + (cc.total_points - used);
    btn.disabled = used > cc.total_points || !valid;
  };

  for (const key of cc.assignable) {
    const input = document.getElementById("alloc-" + key);
    if (input) input.addEventListener("input", updatePoints);
  }

  btn.addEventListener("click", () => {
    for (const key of cc.assignable) {
      const input = document.getElementById("alloc-" + key);
      state.stats[key] = parseInt(input?.value || "0", 10);
    }
    renderEvent("start");
  });

  updatePoints();
}

document.getElementById("btn-restart").addEventListener("click", () => {
  init();
  buildCharacterForm();
  showScreen("screen-character-creation");
});

init();
buildCharacterForm();
`;
}
