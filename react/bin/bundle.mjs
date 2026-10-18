#!/usr/bin/env node
// Copies quran-madina-html (script, CSS, databases, fonts) into the app's public/ folder, so
// <QuranMadinaHtml bundled /> renders offline. Run from the app's folder:
//
//   npx quran-madina-bundle                          # the 1441H layout, into public/quran-madina
//   npx quran-madina-bundle --layouts 1441H,IndoPak
//   npx quran-madina-bundle --out static/quran-madina --version 2.1.1
//   npx quran-madina-bundle --from ../quran-madina-html   # a built checkout instead of npm
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { DEFAULT_OUT, LAYOUT_STEMS, readFolder, readTarGz, selectBundle } from "./lib.mjs";

const fail = (message) => {
  console.error(`quran-madina-bundle: ${message}`);
  process.exit(1);
};

// the wrapper is released in step with the library: bundle the same version by default
const own = JSON.parse(readFileSync(join(dirname(fileURLToPath(import.meta.url)), "..", "package.json"), "utf8"));

const args = process.argv.slice(2);
let layouts = ["1441H"];
let version = own.version;
let out = DEFAULT_OUT;
let from = null;
for (let i = 0; i < args.length; i++) {
  const arg = args[i];
  const value = () => {
    if (arg.includes("=")) return arg.slice(arg.indexOf("=") + 1);
    if (i + 1 >= args.length) fail(`${arg} needs a value`);
    return args[++i];
  };
  if (arg.startsWith("--layouts")) layouts = value().split(",").map((s) => s.trim()).filter(Boolean);
  else if (arg.startsWith("--version")) version = value();
  else if (arg.startsWith("--out")) out = value().replace(/\/+$/, "");
  else if (arg.startsWith("--from")) from = value();
  else if (arg === "-h" || arg === "--help") {
    console.log(`usage: npx quran-madina-bundle [--layouts ${Object.keys(LAYOUT_STEMS).join(",")}] ` +
      `[--out ${DEFAULT_OUT}] [--version ${own.version} | --from <folder>]`);
    process.exit(0);
  } else fail(`unknown option ${arg}`);
}
if (!existsSync("package.json")) fail("run this from your app's folder");

let pkg;
if (from) {
  if (!existsSync(from)) fail(`no folder ${from}`);
  console.log(`Reading ${from}`);
  pkg = readFolder(from);
} else {
  const url = `https://registry.npmjs.org/quran-madina-html/-/quran-madina-html-${version}.tgz`;
  console.log(`Downloading ${url}`);
  const response = await fetch(url).catch((err) => fail(`download failed: ${err.message}`));
  if (!response.ok) fail(`download failed: HTTP ${response.status}`);
  pkg = readTarGz(Buffer.from(await response.arrayBuffer()));
}

let files;
try {
  files = selectBundle(pkg, layouts);
} catch (err) {
  fail(err.message);
}
rmSync(out, { recursive: true, force: true });
let bytes = 0;
for (const [path, data] of files) {
  const target = join(out, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, data);
  bytes += data.length;
}
const base = `/${out.replace(/^public\/?/, "").replace(/^\/+/, "")}/`.replace(/\/+$/, "/");
console.log(`Wrote ${files.size} files (${(bytes / 1048576).toFixed(1)} MB) to ${out}/ for ${layouts.join(", ")}.`);
console.log("");
console.log(out.startsWith("public/") || out === "public"
  ? `Then: <QuranMadinaHtml bundled ... />${base === "/quran-madina/" ? "" : `  (or bundled="${base}")`}`
  : `Serve ${out}/ from your app, then: <QuranMadinaHtml bundled="/<where it is served>/" ... />`);
