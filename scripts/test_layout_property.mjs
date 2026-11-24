#!/usr/bin/env node
/* Runs the measured 200-case property loop with its fixed seed. */
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const result = spawnSync(process.execPath, ["scripts/measure_phone_layout.mjs", "--property"], { cwd: root, encoding: "utf8", timeout: 180000 });
process.stdout.write(result.stdout || "");
process.stderr.write(result.stderr || "");
if (result.error) throw result.error;
if (result.status !== 0) process.exit(result.status || 1);
if (!/measure_phone_layout: 200\/200 viewports passed \(seed 19120261116\)/.test(result.stdout)) {
  throw new Error("the layout property run did not report all 200 seeded viewports");
}
console.log("test_layout_property: 200 seeded landscape viewports passed");
