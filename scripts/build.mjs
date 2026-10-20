// The build (npm run build), in place of the old Gruntfile:
//   1. lint src/**/*.js with jshint
//   2. clean dist/
//   3. write dist/quran-madina-html.js and .css: the src/ files under the license banner, plus
//      identical .min.js / .min.css copies for 2.x pages that link those names (drop in 3.0)
//   4. minify assets/db/*.json (the 1.x databases) in place, whitespace only
//
//   node scripts/build.mjs          everything
//   node scripts/build.mjs --lint   step 1 only
// Grunt was dropped because its file-matching dependencies (braces, sprintf-js) have open
// advisories with no fixed release.
import { mkdirSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import jshint from "jshint";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const pkg = JSON.parse(readFileSync(join(root, "package.json"), "utf8"));

function filesUnder(dir, ext) {
  let out = [];
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) out = out.concat(filesUnder(path, ext));
    else if (path.endsWith(ext)) out.push(path);
  }
  return out;
}

function lint() {
  // The options the Gruntfile used.
  const options = { esnext: true };
  const globals = { jQuery: true, console: true, module: true, document: true };
  const files = filesUnder(join(root, "src"), ".js");
  let errors = 0;
  for (const file of files) {
    jshint.JSHINT(readFileSync(file, "utf8"), options, globals);
    for (const e of jshint.JSHINT.errors.filter(Boolean)) {
      errors++;
      console.error(`${relative(root, file)}:${e.line}:${e.character} ${e.reason} (${e.code})`);
    }
  }
  if (errors) {
    console.error(`jshint: ${errors} problem(s)`);
    process.exit(1);
  }
  console.log(`jshint: ${files.length} file(s) lint free`);
}

const banner =
  "/*!\n" +
  ` * ${pkg.name} v${pkg.version}\n` +
  ` * ${pkg.description}\n` +
  ` * ${pkg.homepage}\n` +
  " *\n" +
  ` * Copyright (c) ${pkg.author}\n` +
  ' * Licensed under the "Waqf" General Public License 2.0, 3 Muharram 1435\n' +
  " * https://github.com/ojuba-org/waqf/tree/master/2.0\n" +
  " * See LICENSE.md in the package for details.\n" +
  " */\n";

function buildDist() {
  const dist = join(root, "dist");
  rmSync(dist, { recursive: true, force: true });
  mkdirSync(dist);
  for (const ext of ["js", "css"]) {
    const body = banner + readFileSync(join(root, "src", `${pkg.name}.${ext}`), "utf8");
    for (const name of [`${pkg.name}.${ext}`, `${pkg.name}.min.${ext}`]) {
      writeFileSync(join(dist, name), body);
    }
  }
  console.log(`dist: ${pkg.name}.js/.css (+ .min copies), v${pkg.version}`);
}

// Drop whitespace outside strings; the values stay byte-for-byte as they are.
export function minifyJson(text) {
  let out = "";
  let inString = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inString) {
      out += c;
      if (c === "\\") out += text[++i];
      else if (c === '"') inString = false;
    } else if (c === '"') {
      inString = true;
      out += c;
    } else if (!/\s/.test(c)) {
      out += c;
    }
  }
  return out;
}

function minifyDatabases() {
  const dir = join(root, "assets", "db");
  const files = readdirSync(dir).filter((n) => n.endsWith(".json"));
  let changed = 0;
  for (const name of files) {
    const path = join(dir, name);
    const text = readFileSync(path, "utf8");
    const small = minifyJson(text);
    if (small !== text) {
      JSON.parse(small); // never write a broken file
      writeFileSync(path, small);
      changed++;
    }
  }
  console.log(`json: ${files.length} database(s), ${changed} minified`);
}

lint();
if (!process.argv.includes("--lint")) {
  buildDist();
  minifyDatabases();
}
