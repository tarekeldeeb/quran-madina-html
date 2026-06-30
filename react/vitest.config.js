import { defineConfig } from "vitest/config";

export default defineConfig({
  // vitest 4 transforms JSX with the automatic runtime by default, so no esbuild jsx option needed.
  test: {
    environment: "jsdom",
    restoreMocks: true,
  },
});
