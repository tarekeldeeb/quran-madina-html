// Lockstep versioning: set the React, Flutter and WordPress wrappers' versions equal to the core library's new version.
// Run from the repo root during release (release-it `after:bump`), before the release commit, so
// react/package.json + lockfile are committed together with the core bump.
import { readFileSync, writeFileSync } from "node:fs";

const version = process.argv[2];
if (!version) {
  console.error("usage: node scripts/sync-wrapper-version.mjs <version>");
  process.exit(1);
}

for (const file of ["react/package.json", "react/package-lock.json"]) {
  try {
    const json = JSON.parse(readFileSync(file, "utf8"));
    json.version = version;
    // npm lockfile v2/v3 also records the root package version here:
    if (json.packages && json.packages[""]) json.packages[""].version = version;
    writeFileSync(file, JSON.stringify(json, null, 2) + "\n");
    console.log(`synced ${file} -> ${version}`);
  } catch (err) {
    console.warn(`skip ${file}: ${err.message}`);
  }
}

// Flutter wrapper (pub.dev): the pubspec version line, and a CHANGELOG entry for it (pub.dev
// expects the published version in the changelog).
try {
  const pubspec = "flutter/pubspec.yaml";
  writeFileSync(pubspec, readFileSync(pubspec, "utf8").replace(/^version: .*$/m, `version: ${version}`));
  console.log(`synced ${pubspec} -> ${version}`);
  const versionDart = "flutter/lib/src/version.dart";
  writeFileSync(versionDart, readFileSync(versionDart, "utf8")
    .replace(/kLibraryVersion = '[^']*'/, `kLibraryVersion = '${version}'`));
  console.log(`synced ${versionDart} -> ${version}`);
  const changelog = "flutter/CHANGELOG.md";
  const log = readFileSync(changelog, "utf8");
  if (!log.startsWith(`## ${version}\n`)) {
    writeFileSync(changelog, `## ${version}\n\n- Follows quran-madina-html ${version}.\n\n` + log);
    console.log(`added ${changelog} entry for ${version}`);
  }
} catch (err) {
  console.warn(`skip flutter: ${err.message}`);
}

// WordPress plugin: header Version, QMH_VERSION (the library version it loads), readme.txt's
// Stable tag, and a changelog entry.
try {
  const main = "wordpress/quran-madina-html/quran-madina-html.php";
  writeFileSync(main, readFileSync(main, "utf8")
    .replace(/^( \* Version:\s+).*$/m, `$1${version}`)
    .replace(/define\( 'QMH_VERSION', '[^']*' \);/, `define( 'QMH_VERSION', '${version}' );`));
  const readme = "wordpress/quran-madina-html/readme.txt";
  let text = readFileSync(readme, "utf8").replace(/^Stable tag: .*$/m, `Stable tag: ${version}`);
  if (!text.includes(`= ${version} =`)) {
    text = text.replace("== Changelog ==\n\n", `== Changelog ==\n\n= ${version} =\n* Follows quran-madina-html ${version}.\n\n`);
  }
  writeFileSync(readme, text);
  console.log(`synced wordpress plugin -> ${version}`);
} catch (err) {
  console.warn(`skip wordpress: ${err.message}`);
}
