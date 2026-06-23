// Publish the React wrapper as part of the core release (release-it `after:release`).
// Guarded against dry-runs: only publishes if the core version actually landed on npm, so
// `release-it --dry-run` (whose hooks still execute) cannot accidentally publish the wrapper.
import { execSync } from "node:child_process";
import { existsSync } from "node:fs";

const version = process.argv[2];
if (!version) {
  console.error("usage: node scripts/publish-wrapper.mjs <version>");
  process.exit(1);
}

function corePublished() {
  try {
    const out = execSync(`npm view quran-madina-html@${version} version`, {
      stdio: ["ignore", "pipe", "ignore"],
    })
      .toString()
      .trim();
    return out === version;
  } catch {
    return false;
  }
}

if (!corePublished()) {
  console.log(
    `core quran-madina-html@${version} not on npm (dry run / publish skipped) — not publishing wrapper`
  );
  process.exit(0);
}

// Ensure build deps exist (esbuild); prepublishOnly then rebuilds dist on publish.
if (!existsSync("react/node_modules/esbuild")) {
  console.log("installing wrapper dev deps…");
  execSync("npm install --no-audit --no-fund", { cwd: "react", stdio: "inherit" });
}

console.log(`publishing @tarekeldeeb/quran-madina-react@${version} …`);
execSync("npm publish --access public", { cwd: "react", stdio: "inherit" });
