import * as fs from "node:fs";
import * as path from "node:path";
import { Command } from "commander";
import { ask, askNumber, askYesNo } from "../utils/prompt";
import { TEMPLATES, TEMPLATE_NAMES, EXAMPLE_EVENT_MD } from "../templates";

const GITIGNORE_CONTENT = `dist/
node_modules/
*.log
`;

function scaffold(cwd: string, gameYml: string, force: boolean) {
  const gameYmlPath = path.join(cwd, "game.yml");
  const eventsDir = path.join(cwd, "events");
  const gitignorePath = path.join(cwd, ".gitignore");

  if (fs.existsSync(gameYmlPath) && !force) {
    throw new Error(
      "game.yml 已存在。使用 --force 选项覆盖，或手动删除后重试。"
    );
  }
  if (fs.existsSync(eventsDir) && !force) {
    throw new Error(
      "events/ 目录已存在。使用 --force 选项覆盖，或手动删除后重试。"
    );
  }

  fs.writeFileSync(gameYmlPath, gameYml, "utf-8");
  console.log("✓ 已创建 game.yml");

  if (!fs.existsSync(eventsDir)) {
    fs.mkdirSync(eventsDir, { recursive: true });
  }
  fs.writeFileSync(
    path.join(eventsDir, "example.md"),
    EXAMPLE_EVENT_MD,
    "utf-8"
  );
  console.log("✓ 已创建 events/example.md");

  if (!fs.existsSync(gitignorePath)) {
    fs.writeFileSync(gitignorePath, GITIGNORE_CONTENT, "utf-8");
    console.log("✓ 已创建 .gitignore");
  }
}

async function interactiveConfig(): Promise<string> {
  console.log("\n🎮 交互式游戏配置向导\n");
  console.log("按 Enter 使用默认值，Ctrl+C 退出\n");

  const title = await ask("游戏标题 (默认: 我的文字模拟器): ");
  const desc = await ask("游戏描述 (默认: 一个简单的文字模拟器游戏): ");

  const gameTitle = title || "我的文字模拟器";
  const gameDesc = desc || "一个简单的文字模拟器游戏";

  console.log("\n--- 数值系统 ---");
  const statsEntries: string[] = [];
  const statDefaults: Record<string, { min: number; max: number; def: number }> = {};

  const statKeys = ["hp", "mana", "strength", "intelligence"];
  const statNames = ["生命值", "法力值", "力量", "智力"];
  const defaults: Record<string, { min: number; max: number; def: number }> = {
    hp: { min: 0, max: 100, def: 100 },
    mana: { min: 0, max: 100, def: 50 },
    strength: { min: 0, max: 20, def: 5 },
    intelligence: { min: 0, max: 20, def: 5 },
  };

  const includeStat = await askYesNo("使用默认四项数值 (生命/法力/力量/智力)?");
  if (includeStat) {
    for (let i = 0; i < statKeys.length; i++) {
      const key = statKeys[i]!;
      const name = statNames[i]!;
      const d = defaults[key]!;
      statsEntries.push(`  ${key}:
    name: ${name}
    min: ${d.min}
    max: ${d.max}
    default: ${d.def}`);
      statDefaults[key] = d;
    }
  } else {
    console.log("跳过数值系统，可以在 game.yml 中手动添加数值。");
  }

  console.log("\n--- 角色创建 ---");
  const totalPoints = await askNumber("可分配点数 (默认: 15): ", 15);
  let assignableKeys = statKeys.slice(2); // strength, intelligence
  if (!includeStat) {
    assignableKeys = [];
  }

  console.log("可分配属性: " + assignableKeys.join(", ") || "(无)");

  const eventsYml = `events:
  - id: start
    title: 冒险开始
    description: 你站在一个分岔路口，前方有两条路。
    choices:
      - text: 向左走
        next_event: left_path
      - text: 向右走
        next_event: right_path
  - id: left_path
    title: 左路
    description: 你选择了左边，发现了一个宝箱。
    choices:
      - text: 打开宝箱
        effects:
          strength: 2
        next_event: ending_treasure
  - id: right_path
    title: 右路
    description: 你选择了右边，遇到了一位贤者。
    choices:
      - text: 与贤者交谈
        effects:
          intelligence: 3
        next_event: ending_wisdom

endings:
  - condition:
      strength: 8
    title: 力量之路
    description: 你用力量征服了冒险！
  - condition:
      intelligence: 8
    title: 智慧之路
    description: 你用智慧照亮了前路！
  - default: true
    title: 平凡结局
    description: 你的冒险结束了。`;

  return `title: ${gameTitle}
description: ${gameDesc}

stats:
${statsEntries.join("\n") || "  # 在此添加自定义数值"}

character_creation:
  total_points: ${totalPoints}
  assignable:
${assignableKeys.map((k) => `    - ${k}`).join("\n") || "    # - 可分配数值键名"}

${eventsYml}
`;
}

export const initCommand = new Command("init")
  .description("在当前目录初始化游戏项目脚手架")
  .option("-f, --force", "覆盖已存在的文件")
  .option("-i, --interactive", "交互式问答生成自定义配置")
  .option("-t, --template <name>", "选择预设模板 (default/cultivation/survival/fantasy)")
  .action(async (options) => {
    const cwd = process.cwd();
    const force = options.force ?? false;

    let gameYml: string;

    if (options.interactive) {
      gameYml = await interactiveConfig();
    } else if (options.template) {
      if (!TEMPLATES[options.template]) {
        const names = Object.keys(TEMPLATES)
          .map((k) => `${k} (${TEMPLATE_NAMES[k] ?? k})`)
          .join(", ");
        console.error(
          `未知模板 "${options.template}"。可用模板: ${names}`
        );
        process.exit(1);
      }
      gameYml = TEMPLATES[options.template]!;
      console.log(`使用模板: ${TEMPLATE_NAMES[options.template] ?? options.template}`);
    } else {
      gameYml = TEMPLATES.default!;
    }

    try {
      scaffold(cwd, gameYml, force);
    } catch (err) {
      console.error((err as Error).message);
      process.exit(1);
    }

    console.log("\n项目脚手架已生成！下一步：");
    console.log("  esimu build    # 构建游戏");
    console.log("  esimu serve     # 启动预览服务器");
  });
