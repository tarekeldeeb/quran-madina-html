import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { gzipSync } from "node:zlib";
import { describe, expect, it } from "vitest";
import { layoutStem, readFolder, readTar, readTarGz, selectBundle } from "../bin/lib.mjs";

/** A ustar archive of `files` ({path: text}), like npm pack writes. */
function tarOf(files) {
  const parts = [];
  for (const [path, text] of Object.entries(files)) {
    const data = Buffer.from(text, "utf8");
    const header = Buffer.alloc(512);
    let prefix = "";
    let name = path;
    if (path.length > 100) {
      prefix = path.slice(0, path.lastIndexOf("/"));
      name = path.slice(path.lastIndexOf("/") + 1);
    }
    header.write(name, 0, "ascii");
    header.write("0000644", 100, "ascii");
    header.write(data.length.toString(8).padStart(11, "0"), 124, "ascii");
    header.write("0", 156, "ascii");
    header.write("ustar", 257, "ascii");
    header.write(prefix, 345, "ascii");
    parts.push(header, data, Buffer.alloc((512 - (data.length % 512)) % 512));
  }
  parts.push(Buffer.alloc(1024));
  return Buffer.concat(parts);
}

const manifest = (font) => JSON.stringify({ version: 2, font_url: font });
const PACKAGE = {
  "package/package.json": "{}",
  "package/dist/quran-madina-html.js": "js",
  "package/dist/quran-madina-html.css": "css",
  "package/dist/quran-madina-html.min.js": "js",
  "package/dist/quran-madina-html.min.css": "css",
  "package/assets/img/sura_border_sym4.svg": "<svg/>",
  "package/assets/db/v2/Madina-1441H.json": "monolith",
  "package/assets/db/v2/Madina-1441H/manifest.json": manifest("assets/db/v2/madina-qmh.woff2"),
  "package/assets/db/v2/Madina-1441H/juz-01.json": "j1",
  "package/assets/db/v2/IndoPak-15/manifest.json": manifest("assets/db/v2/indopak-qmh.woff2"),
  "package/assets/db/v2/IndoPak-15/juz-01.json": "i1",
  "package/assets/db/v2/madina-qmh.woff2": "f1",
  "package/assets/db/v2/indopak-qmh.woff2": "f2",
  "package/assets/db/v2/oldmadina-qmh.woff2": "f3",
};

describe("readTar", () => {
  it("reads plain files, sizes and long (prefixed) names", () => {
    const long = `package/${"a".repeat(60)}/${"b".repeat(60)}/c.json`;
    const files = readTar(tarOf({ "package/x.txt": "hello", [long]: '{"k": 1}', e: "" }));
    expect([...files.keys()]).toEqual(["package/x.txt", long, "e"]);
    expect(files.get("package/x.txt").toString()).toBe("hello");
    expect(files.get(long).toString()).toBe('{"k": 1}');
    expect(files.get("e").length).toBe(0);
  });

  it("reads a gzipped archive", () => {
    expect(readTarGz(gzipSync(tarOf({ "a/b": "xyz" }))).get("a/b").toString()).toBe("xyz");
  });
});

describe("selectBundle", () => {
  const pkg = readTar(tarOf(PACKAGE));

  it("takes the script, CSS, images, and each layout's shards and font", () => {
    expect(new Set(selectBundle(pkg, ["1441H", "indopak"]).keys())).toEqual(new Set([
      "dist/quran-madina-html.js",
      "dist/quran-madina-html.css",
      "dist/quran-madina-html.min.js",
      "dist/quran-madina-html.min.css",
      "assets/img/sura_border_sym4.svg",
      "assets/db/v2/Madina-1441H/manifest.json",
      "assets/db/v2/Madina-1441H/juz-01.json",
      "assets/db/v2/madina-qmh.woff2",
      "assets/db/v2/IndoPak-15/manifest.json",
      "assets/db/v2/IndoPak-15/juz-01.json",
      "assets/db/v2/indopak-qmh.woff2",
    ]));
  });

  it("an older package (only .min.*): the script is also written under the new name", () => {
    const old = { ...PACKAGE };
    delete old["package/dist/quran-madina-html.js"];
    delete old["package/dist/quran-madina-html.css"];
    const out = selectBundle(readTar(tarOf(old)), ["1441H"]);
    expect(out.get("dist/quran-madina-html.js").toString()).toBe("js");
    expect(out.has("dist/quran-madina-html.min.css")).toBe(true);
  });

  it("rejects an unknown layout and a layout missing from the package", () => {
    expect(() => selectBundle(pkg, ["Warsh"])).toThrow(/unknown layout/);
    expect(() => selectBundle(pkg, ["1405H"])).toThrow(/missing/);
  });

  it("knows the layout names in any case", () => {
    expect(layoutStem("indopak")).toBe("IndoPak-15");
    expect(layoutStem("1441h")).toBe("Madina-1441H");
    expect(layoutStem("x")).toBeNull();
  });
});

describe("readFolder", () => {
  it("reads a checkout like a package, only the bundle folders", () => {
    const dir = mkdtempSync(join(tmpdir(), "qmh-"));
    try {
      for (const path of ["dist/a.js", "assets/db/v2/X/manifest.json", "src/big.py", "README.md"]) {
        mkdirSync(join(dir, path, ".."), { recursive: true });
        writeFileSync(join(dir, path), path);
      }
      const files = readFolder(dir);
      expect(new Set(files.keys())).toEqual(new Set(["package/dist/a.js", "package/assets/db/v2/X/manifest.json"]));
      expect(files.get("package/dist/a.js").toString()).toBe("dist/a.js");
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
  });
});
