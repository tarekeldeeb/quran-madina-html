// The page inside the WebView, and the helpers that talk to it. Pure JavaScript (no React Native
// imports), so it is unit-tested in Node and shared with the bundle command, which writes the
// same page as index.html next to the bundled library.

/** The library script loaded by default (latest 2.x on unpkg). */
export const DEFAULT_SRC = "https://unpkg.com/quran-madina-html@2";
/** Base URL the library fetches its CSS, databases and fonts from by default. */
export const DEFAULT_CDN = "https://unpkg.com/quran-madina-html@2/";

/** Attributes of the <quran-madina-html> tag, in the order they are written. */
export const TAG_ATTRIBUTES = [
  "page", "sura", "aya", "words", "highlight", "error", "letters", "headless", "notitle", "quotes", "inline",
];

/**
 * The tag's attributes for the given props: `page` wins over `sura`/`aya`, `true` becomes an
 * empty attribute, and null, false or "" leave the attribute out.
 */
export function tagAttributes(props) {
  const out = {};
  const set = (key, value) => {
    if (value === undefined || value === null || value === false || value === "") return;
    out[key] = value === true ? "" : String(value);
  };
  const hasPage = props.page !== undefined && props.page !== null && props.page !== "";
  for (const key of TAG_ATTRIBUTES) {
    if (hasPage && (key === "sura" || key === "aya")) continue;
    set(key, props[key]);
  }
  return out;
}

/** The changes that turn attributes `from` into `to`: new values, and null to remove. */
export function attributeUpdates(from, to) {
  const out = {};
  for (const [key, value] of Object.entries(to)) if (from[key] !== value) out[key] = value;
  for (const key of Object.keys(from)) if (!(key in to)) out[key] = null;
  return out;
}

/** JavaScript that applies `updates` on the page (for WebView.injectJavaScript). */
export const updateScript = (updates) => `window.qmhSet && qmhSet(${JSON.stringify(updates)}); true;`;

/** JavaScript that starts the page with `config` (idempotent: the page starts once). */
export const startScript = (config) => `window.QMH_CONFIG = ${JSON.stringify(config)}; window.qmhStart && qmhStart(); true;`;

/**
 * The page the WebView shows. With `config` it is self-contained (the online mode, loaded as an
 * HTML string); without, it waits for window.QMH_CONFIG (the bundled index.html, whose options
 * arrive through injected JavaScript). config: {src, cdn, layout, fontSize, textColor,
 * backgroundColor, attrs}; src/cdn default to the files next to the page.
 */
export function hostPage(config) {
  const inline = config ? `window.QMH_CONFIG = ${JSON.stringify(config).replace(/</g, "\\u003c")};` : "";
  return `<!DOCTYPE html>
<html dir="rtl" lang="ar"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>quran-madina-html</title>
<style>
  html, body { margin: 0; padding: 0; background: transparent; color: #20201d; }
  body { display: flow-root; }
</style>
</head><body>
<script>
  ${inline}
  function qmhPost(kind, value) {
    try { window.ReactNativeWebView.postMessage(JSON.stringify({ kind: kind, value: value })); } catch (e) {}
  }
  function qmhSet(attrs) {
    var tag = document.getElementById("qmh");
    if (!tag) return;
    Object.keys(attrs).forEach(function (k) {
      if (attrs[k] === null) tag.removeAttribute(k); else tag.setAttribute(k, attrs[k]);
    });
  }
  function qmhReport() {
    qmhPost("height", Math.ceil(document.body.getBoundingClientRect().height));
  }
  window.open = function (url) { qmhPost("open", String(url)); return null; };
  var qmhStarted = false;
  function qmhStart() {
    var cfg = window.QMH_CONFIG;
    if (qmhStarted || !cfg) return;
    qmhStarted = true;
    document.body.style.color = cfg.textColor || "#20201d";
    document.body.style.background = cfg.backgroundColor || "transparent";
    var tag = document.createElement("quran-madina-html");
    tag.id = "qmh";
    var attrs = cfg.attrs || {};
    Object.keys(attrs).forEach(function (k) { tag.setAttribute(k, attrs[k]); });
    document.body.appendChild(tag);
    var here = location.href.replace(/[#?].*$/, "").replace(/[^/]*$/, "");
    var script = document.createElement("script");
    script.src = cfg.src || here + "dist/quran-madina-html.min.js";
    script.setAttribute("data-cdn", cfg.cdn || here);
    if (cfg.layout) script.setAttribute("data-layout", cfg.layout);
    if (cfg.fontSize) script.setAttribute("data-font-size", String(cfg.fontSize));
    script.onerror = function () { qmhPost("error", "could not load " + script.src); };
    document.head.appendChild(script);
    new ResizeObserver(qmhReport).observe(document.body);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", qmhStart);
  else qmhStart();
</script>
</body></html>
`;
}
