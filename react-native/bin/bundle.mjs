#!/usr/bin/env node
// Copies quran-madina-html (script, CSS, databases, fonts) and the WebView page into the app,
// so <QuranMadinaNative bundled /> renders offline. Run from the app's folder:
//
//   npx quran-madina-native-bundle                          # the 1441H layout
//   npx quran-madina-native-bundle --layouts 1441H,IndoPak
//   npx quran-madina-native-bundle --version 2.1.2          # another library version
//   npx quran-madina-native-bundle --from ../quran-madina-html   # a built checkout
//
// Writes android/app/src/main/assets/quran-madina/ and ios/quran-madina/ (for the platform
// folders the app has; --android / --ios pick other folders). On iOS, add the folder to the
// Xcode project once, as a folder reference.
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { LAYOUT_STEMS, readFolder, readTarGz, selectBundle } from "./lib.mjs";
import { hostPage } from "../src/page.js";

const fail = (message) => {
  console.error(`quran-madina-native-bundle: ${message}`);
  process.exit(1);
};

// released in step with the library: bundle the same version by default
const own = JSON.parse(readFileSync(join(dirname(fileURLToPath(import.meta.url)), "..", "package.json"), "utf8"));

const args = process.argv.slice(2);
let layouts = ["1441H"];
let version = own.version;
let from = null;
const targets = [];
for (let i = 0; i < args.length; i++) {
  const arg = args[i];
  const value = () => {
    if (arg.includes("=")) return arg.slice(arg.indexOf("=") + 1);
    if (i + 1 >= args.length) fail(`${arg} needs a value`);
    return args[++i];
  };
  if (arg.startsWith("--layouts")) layouts = value().split(",").map((s) => s.trim()).filter(Boolean);
  else if (arg.startsWith("--version")) version = value();
  else if (arg.startsWith("--from")) from = value();
  else if (arg.startsWith("--android")) targets.push(value());
  else if (arg.startsWith("--ios")) targets.push(value());
  else if (arg === "-h" || arg === "--help") {
    console.log(`usage: npx quran-madina-native-bundle [--layouts ${Object.keys(LAYOUT_STEMS).join(",")}] ` +
      `[--version ${own.version} | --from <folder>] [--android <folder>] [--ios <folder>]`);
    process.exit(0);
  } else fail(`unknown option ${arg}`);
}
if (!existsSync("package.json")) fail("run this from your app's folder");
if (!targets.length) {
  if (existsSync("android")) targets.push("android/app/src/main/assets/quran-madina");
  if (existsSync("ios")) targets.push("ios/quran-madina");
}
if (!targets.length) {
  fail("no android/ or ios/ folder here. With Expo, run `npx expo prebuild` first, or pass --android/--ios");
}

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
files.set("index.html", Buffer.from(hostPage(null), "utf8"));
let bytes = 0;
for (const [, data] of files) bytes += data.length;
for (const out of targets) {
  rmSync(out, { recursive: true, force: true });
  for (const [path, data] of files) {
    const target = join(out, path);
    mkdirSync(dirname(target), { recursive: true });
    writeFileSync(target, data);
  }
  console.log(`Wrote ${files.size} files (${(bytes / 1048576).toFixed(1)} MB) to ${out}/ for ${layouts.join(", ")}.`);
}
if (targets.some((t) => t.startsWith("ios"))) {
  console.log("\niOS, once: in Xcode, drag ios/quran-madina onto the project and choose");
  console.log('"Create folder references" (a blue folder), with your app target ticked.');
}
console.log("\nThen: <QuranMadinaNative bundled ... />");
