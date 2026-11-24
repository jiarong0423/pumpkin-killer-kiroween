#!/usr/bin/env node
/* Save the task-204b review captures without opening or decoding them. */
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const result = spawnSync(process.execPath, ["scripts/measure_phone_layout.mjs", "--review"], {
  cwd: root,
  encoding: "utf8",
  timeout: 180000
});
process.stdout.write(result.stdout || "");
process.stderr.write(result.stderr || "");
if (result.error) throw result.error;
if (result.status !== 0) process.exit(result.status || 1);
console.log("shoot_views: saved numeric review captures");
