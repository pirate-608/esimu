#!/usr/bin/env bun

import { Command } from "commander";
import { initCommand } from "./commands/init";
import { buildCommand } from "./commands/build";
import { serveCommand } from "./commands/serve";
import { graphCommand } from "./commands/graph";

const program = new Command();

program
  .name("esimu")
  .description("Easy Simulator Generator - build text simulator games from YAML")
  .version("0.1.0");

program.addCommand(initCommand);
program.addCommand(buildCommand);
program.addCommand(serveCommand);
program.addCommand(graphCommand);

program.parse();
