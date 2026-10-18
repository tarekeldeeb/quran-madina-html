// Pure helpers for `quran-madina-bundle` (bin/bundle.mjs): read the quran-madina-html npm
// package and pick the files an app needs to render offline. Same rules as the Flutter
// package's bundler (flutter/lib/src/bundle.dart).
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, sep } from "node:path";
import { gunzipSync } from "node:zlib";

/** The layouts the library ships, by the name `layout` takes, and their database folders. */
export const LAYOUT_STEMS = { "1441H": "Madina-1441H", "1405H": "Madina-1405H", IndoPak: "IndoPak-15" };

/** Where the bundle goes by default, under the app's public/ folder, and the URL it is served at. */
export const DEFAULT_OUT = "public/quran-madina";
export const DEFAULT_BASE = "/quran-madina/";

/** The files of a tar archive, by path. Plain files only (ustar names with prefixes). */
export function readTar(tar) {
  const out = new Map();
  const text = (start, length) => {
    const raw = tar.subarray(start, start + length);
    const end = raw.indexOf(0);
    return Buffer.from(end < 0 ? raw : raw.subarray(0, end)).toString("utf8");
  };
  let pos = 0;
  while (pos + 512 <= tar.length) {
    if (tar.subarray(pos, pos + 512).every((b) => b === 0)) break; // end of archive
    const name = text(pos, 100);
    const sizeText = text(pos + 124, 12).trim();
    const size = sizeText ? parseInt(sizeText, 8) : 0;
    const type = tar[pos + 156];
    const prefix = text(pos + 257, 6).startsWith("ustar") ? text(pos + 345, 155) : "";
    const path = prefix ? `${prefix}/${name}` : name;
    const start = pos + 512;
    if (type === 0 || type === 0x30) out.set(path, Buffer.from(tar.subarray(start, start + size)));
    pos = start + Math.ceil(size / 512) * 512;
  }
  return out;
}

/** The files of a .tgz (an npm package), by path. */
export const readTarGz = (bytes) => readTar(gunzipSync(bytes));

const BUNDLE_ROOTS = ["dist/", "assets/img/", "assets/db/v2/"];

/**
 * The files under `dir` (an unpacked package or a built checkout), laid out like an npm package:
 * each path starts with `package/`. Only the folders a bundle draws from are read.
 */
export function readFolder(dir) {
  const out = new Map();
  const walk = (folder) => {
    for (const entry of readdirSync(folder)) {
      const full = join(folder, entry);
      const path = relative(dir, full).split(sep).join("/");
      if (statSync(full).isDirectory()) {
        if (BUNDLE_ROOTS.some((root) => root.startsWith(`${path}/`) || path.startsWith(root))) walk(full);
      } else if (BUNDLE_ROOTS.some((root) => path.startsWith(root))) {
        out.set(`package/${path}`, readFileSync(full));
      }
    }
  };
  walk(dir);
  return out;
}

/** The stem for a layout name, any case; null if the library has no such layout. */
export function layoutStem(layout) {
  const key = Object.keys(LAYOUT_STEMS).find((k) => k.toLowerCase() === String(layout).toLowerCase());
  return key ? LAYOUT_STEMS[key] : null;
}

/**
 * The files of the package (paths under `package/`) an app needs for `layouts`: the script, the
 * CSS, the images, and each layout's sharded database and font. Result paths are relative to the
 * bundle folder.
 */
export function selectBundle(pkg, layouts) {
  const files = new Map();
  for (const [path, data] of pkg) if (path.startsWith("package/")) files.set(path.slice(8), data);
  const out = new Map();
  const take = (path) => {
    if (!files.has(path)) throw new Error(`${path} is missing from the package`);
    out.set(path, files.get(path));
  };
  take("dist/quran-madina-html.min.js");
  take("dist/quran-madina-html.min.css");
  for (const path of files.keys()) if (path.startsWith("assets/img/")) take(path);
  for (const layout of layouts) {
    const stem = layoutStem(layout);
    if (!stem) throw new Error(`unknown layout "${layout}" (use ${Object.keys(LAYOUT_STEMS).join(", ")})`);
    const dir = `assets/db/v2/${stem}/`;
    for (const path of files.keys()) if (path.startsWith(dir)) take(path);
    const manifest = files.get(`${dir}manifest.json`);
    if (!manifest) throw new Error(`${dir}manifest.json is missing from the package`);
    take(JSON.parse(manifest.toString("utf8")).font_url);
  }
  return out;
}
