import * as path from "node:path";
import { Command } from "commander";
import { watch } from "chokidar";
import { loadConfig, resolveDescriptions } from "../utils/config";
import type { GameConfig } from "../utils/types";
import { generateHTML, resolveCSS, generateGameJS } from "../generator";

interface BuildResult {
  html: string;
  css: string;
  js: string;
}

function buildInMemory(configPath: string): BuildResult | null {
  let config: GameConfig;
  try {
    config = loadConfig(configPath);
  } catch (err) {
    console.error(`构建错误: ${(err as Error).message}`);
    return null;
  }

  const descriptions = resolveDescriptions(
    config.events,
    path.dirname(configPath)
  );

  return {
    html: generateHTML(config, true),
    css: resolveCSS(config, path.dirname(configPath)),
    js: generateGameJS(config, descriptions),
  };
}

export const serveCommand = new Command("serve")
  .description("启动本地预览服务器（内存构建，文件变化自动刷新）")
  .option("-p, --port <number>", "指定端口", "3000")
  .option("-c, --config <path>", "指定配置文件路径", "game.yml")
  .option("--no-open", "不自动打开浏览器")
  .action((options) => {
    const port = parseInt(options.port, 10);
    const configPath = path.resolve(process.cwd(), options.config);
    const configDir = path.dirname(configPath);

    // Initial in-memory build
    let build = buildInMemory(configPath);
    if (!build) process.exit(1);
    console.log("✓ 内存构建完成");

    const liveClients = new Set<ReadableStreamDefaultController>();

    const server = Bun.serve({
      port,
      fetch(req) {
        const url = new URL(req.url);

        // SSE endpoint for live reload
        if (url.pathname === "/__esimu_live") {
          let controller: ReadableStreamDefaultController;
          const stream = new ReadableStream({
            start(c) {
              controller = c;
              liveClients.add(controller!);
            },
            cancel() {
              liveClients.delete(controller!);
            },
          });
          return new Response(stream, {
            headers: {
              "Content-Type": "text/event-stream",
              "Cache-Control": "no-cache",
              Connection: "keep-alive",
            },
          });
        }

        // Serve from in-memory build
        if (url.pathname === "/" || url.pathname === "/index.html") {
          return new Response(build!.html, {
            headers: { "Content-Type": "text/html; charset=utf-8" },
          });
        }

        if (url.pathname === "/css/style.css") {
          return new Response(build!.css, {
            headers: { "Content-Type": "text/css; charset=utf-8" },
          });
        }

        if (url.pathname === "/js/game.js") {
          return new Response(build!.js, {
            headers: { "Content-Type": "application/javascript; charset=utf-8" },
          });
        }

        return new Response("404 Not Found", { status: 404 });
      },
    });

    const address = `http://localhost:${server.port}`;
    console.log(`服务器已启动: ${address}`);

    // Open browser
    if (options.open !== false) {
      const platform = process.platform;
      if (platform === "win32") {
        Bun.spawn(["cmd.exe", "/c", "start", "", address]);
      } else {
        Bun.spawn([platform === "darwin" ? "open" : "xdg-open", address]);
      }
      console.log("已打开浏览器");
    }

    // Watch source files
    const watcher = watch(
      [configPath, path.join(configDir, "events")],
      {
        ignored: /(^|[\/\\])\../,
        persistent: true,
      }
    );

    const notifyClients = (data: string) => {
      const encoder = new TextEncoder();
      const msg = encoder.encode(`event: reload\ndata: ${data}\n\n`);
      for (const ctrl of liveClients) {
        try {
          ctrl.enqueue(msg);
        } catch {
          liveClients.delete(ctrl);
        }
      }
    };

    watcher.on("change", (filePath) => {
      console.log(
        `\n[${new Date().toLocaleTimeString()}] 检测到变化: ${filePath}`
      );
      const newBuild = buildInMemory(configPath);
      if (newBuild) {
        build = newBuild;
        console.log("✓ 重新构建完成，刷新浏览器...");
        notifyClients("reload");
      } else {
        console.log("构建失败，等待文件修复...");
      }
    });

    process.on("SIGINT", () => {
      watcher.close();
      server.stop();
      console.log("\n服务器已停止");
      process.exit(0);
    });

    console.log("按 Ctrl+C 停止服务器");
  });
