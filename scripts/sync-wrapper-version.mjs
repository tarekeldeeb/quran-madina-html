// Lockstep versioning: set the React wrapper's version equal to the core library's new version.
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
