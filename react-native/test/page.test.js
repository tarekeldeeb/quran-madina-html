import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import {
  DEFAULT_CDN, actionSpecs, actionsScript, attributeUpdates, hostPage, startScript, tagAttributes, updateScript,
} from "../src/page.js";

describe("tagAttributes", () => {
  it("page wins over sura/aya", () => {
    expect(tagAttributes({ page: 50, sura: 2, aya: "255", headless: true })).toEqual({ page: "50", headless: "" });
  });
  it("passes marks and letters, leaves out empty values, keeps the tag's order", () => {
    const attrs = tagAttributes({ sura: 1, aya: "2-4", letters: "1:3 blink", highlight: "1", error: "", notitle: false, quotes: null });
    expect(attrs).toEqual({ sura: "1", aya: "2-4", highlight: "1", letters: "1:3 blink" });
    expect(Object.keys(attrs)).toEqual(["sura", "aya", "highlight", "letters"]);
  });
  it("ignores props that aren't tag attributes", () => {
    expect(tagAttributes({ sura: 1, aya: 1, layout: "IndoPak", fontSize: 22, style: {} })).toEqual({ sura: "1", aya: "1" });
  });
});

describe("verse actions", () => {
  it("actions: an array is joined, an empty one means none", () => {
    expect(tagAttributes({ sura: 1, aya: 1, actions: ["copy", "bookmark"] }).actions).toBe("copy bookmark");
    expect(tagAttributes({ sura: 1, aya: 1, actions: [] }).actions).toBe("none");
    expect(tagAttributes({ sura: 1, aya: 1, actions: "translate" }).actions).toBe("translate");
    expect("actions" in tagAttributes({ sura: 1, aya: 1 })).toBe(false);
  });
  it("ayaActions keep only the data, with defaults, and drop entries without an id", () => {
    expect(actionSpecs([{ id: " bookmark ", icon: "<svg/>", onSelect: () => {} }, { title: "no id" }, null]))
      .toEqual([{ id: "bookmark", title: "bookmark", icon: "<svg/>", order: 100 }]);
    expect(actionSpecs(undefined)).toEqual([]);
    expect(actionsScript([{ id: "a" }])).toBe('window.qmhActions && qmhActions([{"id":"a"}]); true;');
  });
  it("the page registers them and posts a choice back", () => {
    const html = hostPage(null);
    expect(html).toContain("function qmhActions(list)");
    expect(html).toContain('qmhPost("action"');
  });
});

describe("attributeUpdates", () => {
  it("lists changed, added and removed attributes", () => {
    expect(attributeUpdates({ sura: "2", aya: "255", highlight: "5-8" }, { sura: "2", aya: "256", headless: "" }))
      .toEqual({ aya: "256", headless: "", highlight: null });
  });
  it("is empty when nothing changed", () => {
    expect(attributeUpdates({ sura: "1" }, { sura: "1" })).toEqual({});
  });
  it("turns into a call on the page", () => {
    expect(updateScript({ aya: "3", words: null })).toBe('window.qmhSet && qmhSet({"aya":"3","words":null}); true;');
    expect(startScript({ attrs: { sura: "1" } })).toContain("qmhStart()");
  });
});

describe("hostPage", () => {
  it("with a config: self-contained, the config inlined safely", () => {
    const html = hostPage({ src: "https://x/q.js", cdn: DEFAULT_CDN, attrs: { letters: "</script><script>alert(1)" } });
    expect(html).toContain("window.QMH_CONFIG = {");
    expect(html).not.toContain("</script><script>alert(1)");
    expect(html).toContain("\\u003c/script>");
  });
  it("without: waits for the injected config (the bundled index.html)", () => {
    const html = hostPage(null);
    expect(html).not.toContain("window.QMH_CONFIG = {");
    expect(html).toContain("function qmhStart()");
  });
});

describe("bin/lib.mjs", () => {
  it("is the same as the React package's (one set of bundling rules)", () => {
    const body = (p) => readFileSync(new URL(p, import.meta.url), "utf8").split("\n").filter((l) => !l.startsWith("//")).join("\n");
    expect(body("../bin/lib.mjs")).toBe(body("../../react/bin/lib.mjs"));
  });
});
