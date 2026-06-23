import * as esbuild from "esbuild";
import { copyFile, mkdir } from "node:fs/promises";

// react (and react-dom, if ever used) stay external — the consumer provides them as peers.
const shared = {
  entryPoints: ["src/index.js"],
  bundle: true,
  external: ["react", "react-dom"],
  jsx: "automatic",
  logLevel: "info",
};

await mkdir("dist", { recursive: true });
await Promise.all([
  esbuild.build({ ...shared, format: "esm", outfile: "dist/index.mjs" }),
  esbuild.build({ ...shared, format: "cjs", outfile: "dist/index.cjs" }),
]);
await copyFile("src/index.d.ts", "dist/index.d.ts");
console.log("built dist/index.mjs, dist/index.cjs, dist/index.d.ts");
