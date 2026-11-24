#!/usr/bin/env node
"use strict";

const { spawnSync } = require("child_process");
const path = require("path");

const root = path.resolve(__dirname, "..");
const result = spawnSync(process.execPath, ["scripts/measure_phone_layout.mjs", "--start"], {
  cwd: root,
  encoding: "utf8",
  timeout: 180000
});
process.stdout.write(result.stdout || "");
process.stderr.write(result.stderr || "");
if (result.error) throw result.error;
if (result.status !== 0) process.exit(result.status || 1);
if (!/measure_phone_layout: 15\/15 viewports passed/.test(result.stdout)) {
  throw new Error("start-screen fit check did not measure every required viewport");
}
console.log("test_start_screen_fit: 15 landscape viewports passed");
