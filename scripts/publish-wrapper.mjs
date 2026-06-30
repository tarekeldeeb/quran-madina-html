// Publish the React wrapper as part of the core release (release-it `after:release`).
// Guarded against dry-runs: only publishes if the core version actually landed on npm, so
// `release-it --dry-run` (whose hooks still execute) cannot accidentally publish the wrapper.
//
// The guard polls the registry with a bounded retry loop because the core `npm publish` returns
// before the new version is queryable via `npm view` — without the wait the guard could see the
// version as "not published yet" and skip the wrapper on a real release. Tunable via
// WRAPPER_PUBLISH_RETRIES / WRAPPER_PUBLISH_DELAY_MS (defaults: 15 tries x 2s ≈ 30s). A genuine
// dry-run waits out the full window once and then correctly skips.
import { execSync } from "node:child_process";
import { existsSync } from "node:fs";

const version = process.argv[2];
if (!version) {
  console.error("usage: node scripts/publish-wrapper.mjs <version>");
  process.exit(1);
}

const retries = Number(process.env.WRAPPER_PUBLISH_RETRIES ?? 15);
const delayMs = Number(process.env.WRAPPER_PUBLISH_DELAY_MS ?? 2000);

function sleepSync(ms) {
  // Synchronous sleep (cross-platform) so the polling loop stays sequential within this script.
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
}

function corePublished() {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      const out = execSync(`npm view quran-madina-html@${version} version`, {
        stdio: ["ignore", "pipe", "ignore"],
      })
        .toString()
        .trim();
      if (out === version) return true;
    } catch {
      // version not on the registry yet (or a transient error) — fall through and retry
    }
    if (attempt < retries) {
      console.log(
        `waiting for quran-madina-html@${version} on npm (attempt ${attempt}/${retries})…`
      );
      sleepSync(delayMs);
    }
  }
  return false;
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
