import React from "react";
import TestRenderer, { act } from "react-test-renderer";
import { beforeEach, describe, expect, it, vi } from "vitest";

const injected = [];
const openURL = vi.fn();
let platform = "android";
let lastWebView = null;

vi.mock("react-native", () => ({
  View: (props) => React.createElement("View", props),
  Linking: { openURL: (url) => openURL(url) },
  Platform: { get OS() { return platform; } },
}));
vi.mock("react-native-webview", () => ({
  WebView: React.forwardRef((props, ref) => {
    React.useImperativeHandle(ref, () => ({ injectJavaScript: (js) => injected.push(js) }));
    lastWebView = props;
    return React.createElement("WebView", props);
  }),
}));

const { default: QuranMadinaNative, bundleBase } = await import("../src/index.js");

globalThis.IS_REACT_ACT_ENVIRONMENT = true;
const render = (props) => {
  let r;
  act(() => { r = TestRenderer.create(React.createElement(QuranMadinaNative, props)); });
  return r;
};
const outerHeight = (r) => [].concat(r.root.findByType("View").props.style).find((s) => s && "height" in s).height;
const message = (data) => act(() => lastWebView.onMessage({ nativeEvent: { data: JSON.stringify(data) } }));

beforeEach(() => { injected.length = 0; openURL.mockClear(); platform = "android"; });

describe("QuranMadinaNative", () => {
  it("online: the page as HTML from unpkg, with the tag's attributes and options", () => {
    render({ sura: 2, aya: "255", highlight: "5-8", layout: "IndoPak", fontSize: 22 });
    expect(lastWebView.source.baseUrl).toBe("https://unpkg.com/quran-madina-html@2/");
    expect(lastWebView.source.html).toContain('"attrs":{"sura":"2","aya":"255","highlight":"5-8"}');
    expect(lastWebView.source.html).toContain('"layout":"IndoPak","fontSize":22');
    expect(lastWebView.allowFileAccess).toBe(false);
  });

  it("takes the height the page reports, unless given one", () => {
    const r = render({ sura: 1, aya: 1 });
    expect(outerHeight(r)).toBe(1);
    message({ kind: "height", value: 240 });
    expect(outerHeight(r)).toBe(240);
    const fixed = render({ sura: 1, aya: 1, height: 100 });
    message({ kind: "height", value: 240 });
    expect(outerHeight(fixed)).toBe(100);
  });

  it("changing a tag attribute updates the page in place; a loader option makes a new page", () => {
    const r = render({ sura: 2, aya: "255" });
    const first = lastWebView.source;
    act(() => r.update(React.createElement(QuranMadinaNative, { sura: 2, aya: "256", headless: true })));
    expect(lastWebView.source).toBe(first);
    expect(injected.at(-1)).toBe('window.qmhSet && qmhSet({"aya":"256","headless":""}); true;');
    act(() => r.update(React.createElement(QuranMadinaNative, { sura: 2, aya: "256", headless: true, layout: "1405H" })));
    expect(lastWebView.source).not.toBe(first);
    expect(lastWebView.source.html).toContain('"aya":"256"');
  });

  it("opens links the library opens, or hands them to onOpenUrl", () => {
    render({ sura: 1, aya: 1 });
    message({ kind: "open", value: "https://quran.com/1/1" });
    expect(openURL).toHaveBeenCalledWith("https://quran.com/1/1");
    const onOpenUrl = vi.fn();
    render({ sura: 1, aya: 1, onOpenUrl });
    expect(lastWebView.onShouldStartLoadWithRequest({ url: "https://quran.com/2/255" })).toBe(false);
    expect(onOpenUrl).toHaveBeenCalledWith("https://quran.com/2/255");
    expect(lastWebView.onShouldStartLoadWithRequest({ url: "about:blank" })).toBe(true);
  });

  it("bundled: the app's index.html, with file access and its options injected first", () => {
    render({ page: 50, bundled: true, layout: "IndoPak" });
    expect(lastWebView.source).toEqual({ uri: "file:///android_asset/quran-madina/index.html" });
    expect(lastWebView.allowFileAccess && lastWebView.allowFileAccessFromFileURLs).toBe(true);
    expect(lastWebView.injectedJavaScriptBeforeContentLoaded).toContain('"layout":"IndoPak"');
    expect(lastWebView.injectedJavaScriptBeforeContentLoaded).toContain('"attrs":{"page":"50"}');
    act(() => lastWebView.onLoadEnd());
    expect(injected.at(-1)).toContain("qmhStart()");
  });

  it("bundled folder per platform", () => {
    expect(bundleBase(true, "android")).toBe("file:///android_asset/quran-madina/");
    expect(bundleBase(true, "ios")).toBe("quran-madina/");
    expect(bundleBase("file:///data/qmh", "android")).toBe("file:///data/qmh/");
    platform = "ios";
    render({ sura: 1, aya: 1, bundled: true });
    expect(lastWebView.source).toEqual({ uri: "quran-madina/index.html" });
    expect(lastWebView.allowingReadAccessToURL).toBe("quran-madina/");
  });
});
