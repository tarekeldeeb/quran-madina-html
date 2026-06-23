import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const SELECTOR = "script";

// loadQuranMadinaHtml caches a module-level singleton promise, so each test re-imports a fresh
// module copy to start from a clean slate. No React / JSX here, so this is safe to reset freely.
async function importFresh() {
  vi.resetModules();
  return import("../src/index.js");
}

beforeEach(() => {
  document.querySelectorAll(SELECTOR).forEach((s) => s.remove());
});

afterEach(() => {
  document.querySelectorAll(SELECTOR).forEach((s) => s.remove());
});

describe("loadQuranMadinaHtml", () => {
  it("injects one loader script with config attributes and the default cdn", async () => {
    const { loadQuranMadinaHtml } = await importFresh();
    loadQuranMadinaHtml({ font: "Hafs", name: "Madina05", fontSize: 24 });

    const scripts = document.querySelectorAll(SELECTOR);
    expect(scripts).toHaveLength(1);

    const script = scripts[0];
    expect(script.src).toContain("unpkg.com/quran-madina-html");
    expect(script.getAttribute("data-font")).toBe("Hafs");
    expect(script.getAttribute("data-name")).toBe("Madina05");
    expect(script.getAttribute("data-font-size")).toBe("24");
    expect(script.getAttribute("data-cdn")).toBe("https://unpkg.com/quran-madina-html/");
  });

  it("is idempotent: a second call reuses the promise and injects no new script", async () => {
    const { loadQuranMadinaHtml } = await importFresh();
    const first = loadQuranMadinaHtml({ font: "Hafs" });
    const second = loadQuranMadinaHtml({ font: "Uthman" });

    expect(first).toBe(second);
    expect(document.querySelectorAll(SELECTOR)).toHaveLength(1);
    // first call's config wins
    expect(document.querySelector(SELECTOR).getAttribute("data-font")).toBe("Hafs");
  });

  it("honors a custom src and cdn override", async () => {
    const { loadQuranMadinaHtml } = await importFresh();
    loadQuranMadinaHtml({
      src: "https://example.com/qmh.js",
      cdn: "https://cdn.example/qmh", // no trailing slash on purpose
    });

    const script = document.querySelector('script[src="https://example.com/qmh.js"]');
    expect(script).toBeTruthy();
    // the wrapper passes cdn through verbatim; the library itself normalizes the trailing slash
    expect(script.getAttribute("data-cdn")).toBe("https://cdn.example/qmh");
  });

  it("does not inject a script when the element is already registered", async () => {
    vi.spyOn(window.customElements, "get").mockReturnValue(class {});
    const { loadQuranMadinaHtml } = await importFresh();

    await loadQuranMadinaHtml();
    expect(document.querySelectorAll(SELECTOR)).toHaveLength(0);
  });

  it("rejects and clears the cache when the script fails to load", async () => {
    const { loadQuranMadinaHtml } = await importFresh();
    const promise = loadQuranMadinaHtml({ src: "https://example.com/missing.js" });

    // jsdom never fires onload/onerror for an injected <script>; simulate the failure.
    document.querySelector(SELECTOR).onerror(new Event("error"));
    await expect(promise).rejects.toThrow(/Failed to load/);

    // cache cleared → a retry injects again
    loadQuranMadinaHtml({ src: "https://example.com/retry.js" });
    expect(document.querySelector('script[src="https://example.com/retry.js"]')).toBeTruthy();
  });
});
