import * as fs from "node:fs";
import * as path from "node:path";
import { Command } from "commander";
import { watch } from "chokidar";
import { loadConfig, resolveDescriptions } from "../utils/config";
import type { GameConfig } from "../utils/types";
import { generateHTML, resolveCSS, generateGameJS } from "../generator";


function doBuild(
  configPath: string,
  outputDir: string,
  silent: boolean
): boolean {
  if (!silent) console.log(`加载配置: ${configPath}`);

  let config: GameConfig;
  try {
    config = loadConfig(configPath);
  } catch (err) {
    console.error(`错误: ${(err as Error).message}`);
    return false;
  }

  if (!silent) console.log("✓ 配置验证通过");

  const descriptions = resolveDescriptions(
    config.events,
    path.dirname(configPath)
  );

  if (fs.existsSync(outputDir)) {
    fs.rmSync(outputDir, { recursive: true });
  }

  fs.mkdirSync(path.join(outputDir, "css"), { recursive: true });
  fs.mkdirSync(path.join(outputDir, "js"), { recursive: true });

  fs.writeFileSync(
    path.join(outputDir, "index.html"),
    generateHTML(config),
    "utf-8"
  );
  if (!silent) console.log("✓ 已生成 index.html");

  fs.writeFileSync(
    path.join(outputDir, "css", "style.css"),
    resolveCSS(config, path.dirname(configPath)),
    "utf-8"
  );
  if (!silent) console.log("✓ 已生成 css/style.css");

  fs.writeFileSync(
    path.join(outputDir, "js", "game.js"),
    generateGameJS(config, descriptions),
    "utf-8"
  );
  if (!silent) console.log("✓ 已生成 js/game.js");

  return true;
}

export const buildCommand = new Command("build")
  .description("根据 game.yml 构建游戏到 dist/ 目录")
  .option("-c, --config <path>", "指定配置文件路径", "game.yml")
  .option("-o, --output <dir>", "指定输出目录", "dist")
  .option("-w, --watch", "监听文件变化，自动重新构建")
  .action((options) => {
    const cwd = process.cwd();
    const configPath = path.resolve(cwd, options.config);
    const outputDir = path.resolve(cwd, options.output);
    const configDir = path.dirname(configPath);

    const ok = doBuild(configPath, outputDir, false);
    if (!ok && !options.watch) {
      process.exit(1);
    }

    if (!ok && options.watch) {
      console.log("等待修复配置文件...");
    } else if (!options.watch) {
      console.log(`\n构建完成！输出目录: ${outputDir}`);
      console.log("运行 esimu serve 启动预览服务器");
      return;
    } else {
      console.log(`\n构建完成！输出目录: ${outputDir}`);
      console.log("监听文件变化中... (Ctrl+C 停止)");
    }

    if (!options.watch) return;

    const watcher = watch(
      [configPath, path.join(configDir, "events")],
      {
        ignored: /(^|[\/\\])\../,
        persistent: true,
      }
    );

    watcher.on("change", (filePath) => {
      console.log(`\n[${new Date().toLocaleTimeString()}] 检测到变化: ${filePath}`);
      const ok = doBuild(configPath, outputDir, true);
      if (ok) {
        console.log("✓ 重新构建完成");
      } else {
        console.log("构建失败，等待文件修复...");
      }
    });

    process.on("SIGINT", () => {
      watcher.close();
      console.log("\n监听已停止");
      process.exit(0);
    });
  });
