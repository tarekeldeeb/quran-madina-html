import React, { useEffect, useRef, useState } from "react";

const TAG = "quran-madina-html";
const DEFAULT_SRC = "https://unpkg.com/quran-madina-html";
// Asset base the runtime fetches its CSS + JSON DB from. Pinning it here makes the tag work
// inside a bundled app where the page host is "localhost" (React dev server, Capacitor) — the
// library would otherwise assume its assets live at `../`. Requires a build of the library that
// supports the `data-cdn` attribute (>= the release that introduced it).
const DEFAULT_CDN = "https://unpkg.com/quran-madina-html/";

// Where `npx quran-madina-bundle` puts the library by default (public/quran-madina), as served.
export const BUNDLE_BASE = "/quran-madina/";

/**
 * The script URL and asset base for a bundled copy of the library: `true` for the default
 * folder, or the URL the bundle folder is served at (e.g. "/app/quran-madina/").
 */
export function bundleUrls(bundled) {
  let base = bundled === true ? BUNDLE_BASE : String(bundled);
  if (!base.endsWith("/")) base += "/";
  return { src: `${base}dist/quran-madina-html.js`, cdn: base };
}

let loaderPromise = null;

/**
 * Inject the quran-madina-html loader <script> exactly once and resolve when the custom element
 * is registered. The layout / size / cdn config is global (one JSON DB per page), so only
 * the first call's values take effect — pass them on the first <QuranMadinaHtml> you render.
 *
 * @param {object} [opts]
 * @param {string} [opts.src]      URL of the library script (default: unpkg latest).
 * @param {string} [opts.cdn]      Base URL for the CSS + JSON assets (default: unpkg package root).
 * @param {string} [opts.layout]   data-layout: "1441H" (default) | "1405H" | "IndoPak". Letters
 *                                  stretched like the print, any font size, one DB per layout.
 * @param {string} [opts.font]     Deprecated, ignored since 2.0 (the library logs a warning).
 * @param {string} [opts.name]     Deprecated, ignored since 2.0 (the library logs a warning).
 * @param {number|string} [opts.fontSize] data-font-size in px (default 16). Any size works.
 * @param {boolean|string} [opts.bundled] Load the app's own copy of the library, written by
 *                                  `npx quran-madina-bundle`: true for /quran-madina/, or the URL
 *                                  the bundle is served at. Overrides src and cdn.
 * @returns {Promise<void>}
 */
export function loadQuranMadinaHtml(opts = {}) {
  const { layout, font, name, fontSize, bundled } = opts;
  const { src = DEFAULT_SRC, cdn = DEFAULT_CDN } = bundled ? bundleUrls(bundled) : opts;
  if (typeof window === "undefined" || typeof document === "undefined") {
    return Promise.resolve(); // SSR / non-browser: nothing to load
  }
  if (loaderPromise) return loaderPromise;
  if (window.customElements && window.customElements.get(TAG)) {
    loaderPromise = Promise.resolve();
    return loaderPromise;
  }
  loaderPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = src;
    script.async = true;
    if (cdn) script.setAttribute("data-cdn", cdn);
    if (layout) script.setAttribute("data-layout", layout);
    if (font) script.setAttribute("data-font", font);
    if (name) script.setAttribute("data-name", name);
    if (fontSize != null) script.setAttribute("data-font-size", String(fontSize));
    script.onload = () => resolve();
    script.onerror = () => {
      loaderPromise = null; // allow a later retry
      reject(new Error(`Failed to load ${src}`));
    };
    document.head.appendChild(script);
  });
  return loaderPromise;
}

/**
 * React wrapper around the <quran-madina-html> custom element.
 *
 * Render a full page:           <QuranMadinaHtml page={106} />
 * Render an aya range:          <QuranMadinaHtml sura={2} aya="8-10" />
 * Restrict to words:            <QuranMadinaHtml sura={1} aya={1} words="1:2" />
 * Mark words:                   <QuranMadinaHtml sura={2} aya={255} highlight="5-8" error="1" />
 * Mark letters in words:        <QuranMadinaHtml sura={1} aya={2} letters="1:3, 4:3-5 emerald blink" />
 * Pick the v2 layout:           <QuranMadinaHtml page={3} layout="1405H" />
 * Offline, from the app's copy:  <QuranMadinaHtml page={3} bundled />   (npx quran-madina-bundle)
 * Drop header/copy chrome:      <QuranMadinaHtml sura={2} aya="8-10" headless />
 * Drop the inline quote marks:  <QuranMadinaHtml sura={1} aya={3} quotes="no" />
 * Force the multiline layout:   <QuranMadinaHtml sura={1} aya={3} inline="no" />
 * Blank crossed-into sura names
 * (keeps the decorated line):   <QuranMadinaHtml sura={1} aya={7} words="1-14" notitle />
 * Only some verse actions:      <QuranMadinaHtml sura={2} aya="255" actions={["copy", "bookmark"]} />
 * No verse actions (plain text): <QuranMadinaHtml sura={2} aya="255" actions={[]} />
 *
 * `page` and `sura`/`aya` are mutually exclusive (page wins if both are passed).
 */
export default function QuranMadinaHtml({
  page,
  sura,
  aya,
  words,
  highlight,
  error,
  letters,
  headless,
  quotes,
  inline,
  notitle,
  actions,
  // loader config (only honored on first mount, see loadQuranMadinaHtml)
  src,
  cdn,
  layout,
  font,
  name,
  fontSize,
  bundled,
  className,
  style,
  ...rest
}) {
  const ref = useRef(null);
  const [ready, setReady] = useState(
    typeof window !== "undefined" &&
      !!window.customElements &&
      !!window.customElements.get(TAG)
  );

  useEffect(() => {
    let active = true;
    loadQuranMadinaHtml({ src, cdn, layout, font, name, fontSize, bundled })
      .then(() => active && setReady(true))
      .catch((err) => console.error("[quran-madina-html]", err));
    return () => {
      active = false;
    };
  }, [src, cdn, layout, font, name, fontSize, bundled]);

  // Sync attributes imperatively. We avoid passing page/sura/aya as React props because attribute
  // handling for custom elements differs across React versions; setting them on the DOM node is
  // version-proof and the element re-renders itself on each attribute change.
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const set = (key, value) => {
      if (value === undefined || value === null || value === false || value === "") {
        el.removeAttribute(key);
      } else {
        el.setAttribute(key, value === true ? "" : String(value));
      }
    };
    if (page !== undefined && page !== null && page !== "") {
      set("page", page);
      set("sura", null);
      set("aya", null);
    } else {
      set("page", null);
      set("sura", sura);
      set("aya", aya);
    }
    set("words", words);
    set("highlight", highlight);
    set("error", error);
    set("letters", letters);
    set("headless", headless);
    set("quotes", quotes);
    set("inline", inline);
    set("notitle", notitle);
    set("actions", Array.isArray(actions) ? (actions.length ? actions.join(" ") : "none") : actions);
  }, [ready, page, sura, aya, words, highlight, error, letters, headless, quotes, inline, notitle,
      Array.isArray(actions) ? actions.join(" ") + "|" + actions.length : actions]);

  // Render as `class` rather than `className`: React < 19 does not map className -> class for
  // custom elements, so passing className would silently drop the class on those versions.
  return React.createElement(TAG, { ref, class: className, style, ...rest });
}

// ----------------------------------------------------------------------------
// Verse actions: the buttons of the popup a click on a verse opens. Page-wide, for every tag;
// each call waits until the library is loaded. See the docs' "Verse actions" guide.
// ----------------------------------------------------------------------------

const whenReady = () =>
  typeof window === "undefined" || !window.customElements
    ? new Promise(() => {}) // server rendering: never
    : window.customElements.whenDefined(TAG);

/** Add an action (or replace the one with the same id): {id, title, icon, order, when, onSelect}. */
export const registerAction = (spec) => whenReady().then((Q) => Q.registerAction(spec));
/** Remove an action by id; resolves to whether it was there. */
export const unregisterAction = (id) => whenReady().then((Q) => Q.unregisterAction(id));
/** Remove every action, the built-in copy and translate too: verses become plain text. */
export const clearActions = () => whenReady().then((Q) => Q.clearActions());
/** Back to the built-in copy and translate. */
export const resetActions = () => whenReady().then((Q) => Q.resetActions());

/**
 * Register an action while the calling component is mounted. The latest `spec` is used on
 * each click, so its onSelect can use the component's current state.
 */
export function useAyaAction(spec) {
  const latest = useRef(spec);
  latest.current = spec;
  const { id, title, icon, order } = spec;
  useEffect(() => {
    let active = true;
    registerAction({
      id, title, icon, order,
      when: (aya) => (latest.current.when ? latest.current.when(aya) : true),
      onSelect: (aya) => latest.current.onSelect(aya),
    }).then(() => { if (!active) unregisterAction(id); });
    return () => {
      active = false;
      unregisterAction(id);
    };
  }, [id, title, typeof icon === "string" ? icon : null, order]); // eslint-disable-line react-hooks/exhaustive-deps
}
