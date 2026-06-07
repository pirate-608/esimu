import * as fs from "node:fs";
import * as path from "node:path";
import { load as loadYaml } from "js-yaml";
import { marked } from "marked";
import type { GameConfig } from "./types";

export function loadConfig(configPath: string): GameConfig {
  const fullPath = path.resolve(configPath);

  if (!fs.existsSync(fullPath)) {
    throw new Error(`Config file not found: ${fullPath}`);
  }

  const raw = fs.readFileSync(fullPath, "utf-8");
  const parsed = loadYaml(raw);

  if (!parsed || typeof parsed !== "object") {
    throw new Error("Config file is empty or invalid YAML.");
  }

  const config = parsed as Record<string, unknown>;
  validateConfig(config, path.dirname(fullPath));

  return config as unknown as GameConfig;
}

export function validateConfig(
  config: Record<string, unknown>,
  baseDir: string
): void {
  if (typeof config.title !== "string" || !config.title) {
    throw new Error('Config validation: "title" must be a non-empty string.');
  }
  if (typeof config.description !== "string" || !config.description) {
    throw new Error(
      'Config validation: "description" must be a non-empty string.'
    );
  }

  if (config.css !== undefined) {
    if (typeof config.css !== "string") {
      throw new Error('Config validation: "css" must be a string.');
    }
    const cssPath = path.resolve(baseDir, config.css);
    if (!fs.existsSync(cssPath)) {
      throw new Error(
        `Config validation: css file "${config.css}" not found at ${cssPath}.`
      );
    }
  }

  if (!config.stats || typeof config.stats !== "object") {
    throw new Error(
      'Config validation: "stats" must be an object mapping stat keys to {name, min, max, default}.'
    );
  }
  for (const [key, stat] of Object.entries(
    config.stats as Record<string, unknown>
  )) {
    if (typeof stat !== "object" || stat === null) {
      throw new Error(
        `Config validation: stats.${key} must be an object with name, min, max, default.`
      );
    }
    const s = stat as Record<string, unknown>;
    if (typeof s.name !== "string" || !s.name) {
      throw new Error(
        `Config validation: stats.${key}.name must be a non-empty string.`
      );
    }
    if (typeof s.min !== "number") {
      throw new Error(
        `Config validation: stats.${key}.min must be a number.`
      );
    }
    if (typeof s.max !== "number") {
      throw new Error(
        `Config validation: stats.${key}.max must be a number.`
      );
    }
    if (typeof s.default !== "number") {
      throw new Error(
        `Config validation: stats.${key}.default must be a number.`
      );
    }
  }

  if (
    !config.character_creation ||
    typeof config.character_creation !== "object"
  ) {
    throw new Error(
      'Config validation: "character_creation" is required.'
    );
  }
  const cc = config.character_creation as Record<string, unknown>;
  if (typeof cc.total_points !== "number") {
    throw new Error(
      'Config validation: character_creation.total_points must be a number.'
    );
  }
  if (!Array.isArray(cc.assignable)) {
    throw new Error(
      'Config validation: character_creation.assignable must be an array of stat keys.'
    );
  }
  const statKeys = Object.keys(config.stats as Record<string, unknown>);
  for (const key of cc.assignable) {
    if (typeof key !== "string") {
      throw new Error(
        "Config validation: character_creation.assignable items must be strings."
      );
    }
    if (!statKeys.includes(key)) {
      throw new Error(
        `Config validation: character_creation.assignable includes "${key}" which is not a defined stat.`
      );
    }
  }

  if (!Array.isArray(config.events)) {
    throw new Error('Config validation: "events" must be an array.');
  }
  const eventIds = new Set<string>();
  for (let i = 0; i < (config.events as unknown[]).length; i++) {
    const ev = (config.events as unknown[])[i] as Record<string, unknown>;
    if (typeof ev.id !== "string" || !ev.id) {
      throw new Error(
        `Config validation: events[${i}].id must be a non-empty string.`
      );
    }
    if (eventIds.has(ev.id)) {
      throw new Error(
        `Config validation: duplicate event id "${ev.id}".`
      );
    }
    eventIds.add(ev.id);

    if (typeof ev.title !== "string" || !ev.title) {
      throw new Error(
        `Config validation: events[${i}].title must be a non-empty string.`
      );
    }

    if (ev.descriptionFile !== undefined) {
      if (typeof ev.descriptionFile !== "string") {
        throw new Error(
          `Config validation: events[${i}].descriptionFile must be a string.`
        );
      }
      const descPath = path.resolve(baseDir, ev.descriptionFile);
      if (!fs.existsSync(descPath)) {
        throw new Error(
          `Config validation: events[${i}].descriptionFile "${ev.descriptionFile}" not found at ${descPath}.`
        );
      }
    }

    if (!Array.isArray(ev.choices) || (ev.choices as unknown[]).length === 0) {
      throw new Error(
        `Config validation: events[${i}].choices must be a non-empty array.`
      );
    }
    for (let j = 0; j < (ev.choices as unknown[]).length; j++) {
      const ch = (ev.choices as unknown[])[j] as Record<string, unknown>;
      if (typeof ch.text !== "string" || !ch.text) {
        throw new Error(
          `Config validation: events[${i}].choices[${j}].text must be a non-empty string.`
        );
      }
      if (typeof ch.next_event !== "string" || !ch.next_event) {
        throw new Error(
          `Config validation: events[${i}].choices[${j}].next_event must be a non-empty string.`
        );
      }
      if (ch.condition !== undefined && typeof ch.condition !== "object") {
        throw new Error(
          `Config validation: events[${i}].choices[${j}].condition must be an object.`
        );
      }
      if (ch.effects !== undefined && typeof ch.effects !== "object") {
        throw new Error(
          `Config validation: events[${i}].choices[${j}].effects must be an object.`
        );
      }
    }
  }

  const hasStart = eventIds.has("start");
  if (!hasStart) {
    throw new Error(
      'Config validation: an event with id "start" is required as the entry point.'
    );
  }

  // ── Warn about events where ALL choices are conditional ──────────
  for (const ev of config.events as unknown[] as Array<Record<string, unknown>>) {
    const choices = ev.choices as Array<Record<string, unknown>>;
    if (choices.every((ch) => ch.condition !== undefined && ch.condition !== null)) {
      console.warn(
        `⚠ 警告: 事件 "${String(ev.id)}" (${String(ev.title)}) 的所有选项都有条件，` +
        "当条件都不满足时玩家将卡死。建议添加一个无条件的兜底选项。"
      );
    }
  }

  if (!Array.isArray(config.endings) || (config.endings as unknown[]).length === 0) {
    throw new Error(
      'Config validation: "endings" must be a non-empty array.'
    );
  }
  for (let i = 0; i < (config.endings as unknown[]).length; i++) {
    const end = (config.endings as unknown[])[i] as Record<string, unknown>;
    if (typeof end.title !== "string" || !end.title) {
      throw new Error(
        `Config validation: endings[${i}].title must be a non-empty string.`
      );
    }
    if (typeof end.description !== "string" || !end.description) {
      throw new Error(
        `Config validation: endings[${i}].description must be a non-empty string.`
      );
    }
  }
}

export function loadDescriptionFile(
  descriptionFile: string,
  baseDir: string
): string {
  const fullPath = path.resolve(baseDir, descriptionFile);
  return fs.readFileSync(fullPath, "utf-8");
}

export function resolveDescriptions(
  events: { description?: string; descriptionFile?: string }[],
  baseDir: string
): string[] {
  return events.map((ev) => {
    let text = ev.description ?? "";

    if (ev.descriptionFile) {
      const fileContent = loadDescriptionFile(ev.descriptionFile, baseDir);
      const html = marked.parse(fileContent) as string;
      text = text ? `${text}\n${html}` : html;
    }

    return text;
  });
}
