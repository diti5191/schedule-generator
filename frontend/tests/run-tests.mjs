#!/usr/bin/env node
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const testsPath = resolve(__dirname);

const child = spawn(process.execPath, ["--test", testsPath], {
  stdio: "inherit",
});

child.on("exit", (code) => {
  process.exit(code ?? 1);
});