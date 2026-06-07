import * as fs from "node:fs";
import * as path from "node:path";
import { Command } from "commander";
import { loadConfig } from "../utils/config";
import type { GameConfig } from "../utils/types";

function statName(config: GameConfig, key: string): string {
  return config.stats[key]?.name ?? key;
}

function formatCondition(config: GameConfig, condition?: Record<string, number>): string {
  if (!condition) return "";
  const parts = Object.entries(condition).map(
    ([key, val]) => `${statName(config, key)}≥${val}`
  );
  return ` ?${parts.join(" ")}`;
}

function formatEffects(config: GameConfig, effects?: Record<string, number>): string {
  if (!effects) return "";
  const parts = Object.entries(effects).map(([key, delta]) => {
    const sign = delta >= 0 ? "+" : "";
    return ` ${sign}${statName(config, key)}${delta}`;
  });
  return parts.join("");
}

function edgeLabel(
  config: GameConfig,
  text: string,
  condition?: Record<string, number>,
  effects?: Record<string, number>
): string {
  const cond = formatCondition(config, condition);
  const eff = formatEffects(config, effects);
  return `${text}${cond}${eff}`;
}

function isEndingTarget(nextEvent: string): boolean {
  return nextEvent.startsWith("ending_");
}

function generateMermaid(config: GameConfig): string {
  const lines: string[] = [];
  lines.push("flowchart TD");

  // ── Event nodes ──────────────────────────────────────────────────
  for (const event of config.events) {
    // Use rectangular bracket shape for nodes; "start" gets a special marker
    const shape = event.id === "start"
      ? `([${event.title}])`  // stadium shape for entry point
      : `[${event.title}]`;   // rectangle for regular events
    lines.push(`  ${event.id}${shape}`);
  }
  lines.push("");

  // ── Choice edges ─────────────────────────────────────────────────
  const endingTargets = new Set<string>();

  for (const event of config.events) {
    for (const choice of event.choices) {
      if (isEndingTarget(choice.next_event)) {
        // Collect ending references — we'll draw them to the eval node later
        endingTargets.add(choice.next_event);
        const label = edgeLabel(config, choice.text, choice.condition, choice.effects);
        lines.push(`  ${event.id} -->|"${label}"| ending_eval`);
      } else {
        const label = edgeLabel(config, choice.text, choice.condition, choice.effects);
        lines.push(`  ${event.id} -->|"${label}"| ${choice.next_event}`);
      }
    }
  }

  // ── Ending evaluation node ───────────────────────────────────────
  if (endingTargets.size > 0) {
    lines.push("");
    lines.push(`  ending_eval["结局判定"]`);
    for (const ending of config.endings) {
      if (ending.default) continue;
      const cond = formatCondition(config, ending.condition).replace(/^\s*\?\s*/, "");
      const label = cond ? `${ending.title}: ${cond}` : ending.title;
      const endingId = `ending_${config.endings.indexOf(ending)}`;
      lines.push(`  ending_eval -->|"${label}"| ${endingId}("${ending.title}")`);
    }
    // Default ending
    const defaultEnding = config.endings.find((e) => e.default);
    if (defaultEnding) {
      const endingId = `ending_default`;
      lines.push(`  ending_eval -->|"其他"| ${endingId}("${defaultEnding.title}")`);
    }
  }

  return lines.join("\n") + "\n";
}

export const graphCommand = new Command("graph")
  .description("导出事件流程图为 Mermaid 图表")
  .option("-c, --config <path>", "指定配置文件路径", "game.yml")
  .option("-o, --output <file>", "输出到文件（默认打印到终端）")
  .action((options) => {
    const cwd = process.cwd();
    const configPath = path.resolve(cwd, options.config);
    const config = loadConfig(configPath);
    const mermaid = generateMermaid(config);

    if (options.output) {
      const outPath = path.resolve(cwd, options.output);
      fs.writeFileSync(outPath, mermaid, "utf-8");
      console.log(`Mermaid 图表已保存到 ${options.output}`);
    } else {
      console.log(mermaid);
    }
  });
