// Reads src/templates/files/*.yml and example-event.md,
// generates src/templates/index.ts with inline string content.
// Run after editing template files to sync them into the code.

import * as fs from "node:fs";
import * as path from "node:path";

const filesDir = path.join(import.meta.dir, "..", "src", "templates", "files");
const outPath = path.join(import.meta.dir, "..", "src", "templates", "index.ts");

const templateNames = ["default", "cultivation", "survival", "fantasy"];
const nameLabels: Record<string, string> = {
  default: "默认模板",
  cultivation: "修仙模拟器",
  survival: "末日求生",
  fantasy: "龙与地牢",
};

let out = "";

// TEMPLATES
out += "export const TEMPLATES: Record<string, string> = {\n";
for (const name of templateNames) {
  const content = fs.readFileSync(path.join(filesDir, `${name}.yml`), "utf-8");
  // Escape backticks and template expressions in the YAML content
  const escaped = content
    .replace(/\\/g, "\\\\")
    .replace(/`/g, "\\`")
    .replace(/\$/g, "\\$");
  out += `  ${name}: \`${escaped}\`,\n`;
}
out += "};\n\n";

// TEMPLATE_NAMES
out += "export const TEMPLATE_NAMES: Record<string, string> = {\n";
for (const name of templateNames) {
  out += `  ${name}: "${nameLabels[name]!}",\n`;
}
out += "};\n\n";

// EXAMPLE_EVENT_MD
const exampleMd = fs.readFileSync(path.join(filesDir, "example-event.md"), "utf-8");
const escapedMd = exampleMd
  .replace(/\\/g, "\\\\")
  .replace(/`/g, "\\`")
  .replace(/\$/g, "\\$");
out += `export const EXAMPLE_EVENT_MD = \`${escapedMd}\`;\n`;

fs.writeFileSync(outPath, out, "utf-8");
console.log(`✓ Synced ${templateNames.length} templates + example-event.md → src/templates/index.ts`);
