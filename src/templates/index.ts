import * as fs from "node:fs";
import * as path from "node:path";

const filesDir = path.join(import.meta.dir, "files");

function read(name: string): string {
  return fs.readFileSync(path.join(filesDir, name), "utf-8");
}

export const TEMPLATES: Record<string, string> = {
  default: read("default.yml"),
  cultivation: read("cultivation.yml"),
  survival: read("survival.yml"),
  fantasy: read("fantasy.yml"),
};

export const TEMPLATE_NAMES: Record<string, string> = {
  default: "默认模板",
  cultivation: "修仙模拟器",
  survival: "末日求生",
  fantasy: "龙与地牢",
};

export const EXAMPLE_EVENT_MD = read("example-event.md");
