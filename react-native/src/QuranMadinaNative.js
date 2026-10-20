// <QuranMadinaNative />: the quran-madina-html tag in a react-native-webview WebView, sized to
// the rendered text. Plain JavaScript (React.createElement), so it needs no build step.
import React, { useEffect, useMemo, useRef, useState } from "react";
import { Linking, Platform, View } from "react-native";
import { WebView } from "react-native-webview";
import {
  DEFAULT_CDN, DEFAULT_SRC, actionSpecs, actionsScript, attributeUpdates, hostPage, startScript, tagAttributes,
  updateScript,
} from "./page.js";

/** Where `npx quran-madina-native-bundle` puts the library inside the app. */
export const BUNDLE_FOLDER = "quran-madina";

/**
 * The URL of the bundled folder: Android's assets, or a folder in the iOS app bundle (relative
 * paths resolve there). A string `bundled` is used as given.
 */
export function bundleBase(bundled, os = Platform.OS) {
  if (typeof bundled === "string") return bundled.endsWith("/") ? bundled : `${bundled}/`;
  return os === "android" ? `file:///android_asset/${BUNDLE_FOLDER}/` : `${BUNDLE_FOLDER}/`;
}

/**
 * Renders Quran text like the printed Madina Mushaf. Same options as the React component:
 * page, sura, aya, words, highlight, error, letters, headless, notitle, quotes, inline, actions,
 * layout, fontSize; plus textColor, backgroundColor, height, bundled, onOpenUrl, and verse actions:
 * ayaActions ([{id, title, icon, order}]) with onAyaAction({id, sura, aya, page, text, ...}).
 */
export default function QuranMadinaNative(props) {
  const {
    layout, fontSize, textColor, backgroundColor, src = DEFAULT_SRC, cdn = DEFAULT_CDN,
    bundled, height, onOpenUrl, onAyaAction, ayaActions, style, webViewProps,
  } = props;
  const specs = actionSpecs(ayaActions);
  const specsKey = JSON.stringify(specs);
  const shownSpecs = useRef(specs);
  const attrs = tagAttributes(props);
  const attrsKey = JSON.stringify(attrs);
  const [measured, setMeasured] = useState(1);
  const webView = useRef(null);
  const shown = useRef(attrs);

  // Loader options make a new page; tag attributes are updated in place (see below).
  const loaderKey = JSON.stringify([layout, fontSize, textColor, backgroundColor, src, cdn, bundled]);
  const { source, config, base } = useMemo(() => {
    shown.current = attrs;
    shownSpecs.current = specs;
    const common = { layout, fontSize, textColor, backgroundColor, attrs, ayaActions: specs };
    if (bundled) {
      const root = bundleBase(bundled);
      return { source: { uri: `${root}index.html` }, config: common, base: root };
    }
    const cfg = { ...common, src, cdn };
    return { source: { html: hostPage(cfg), baseUrl: cdn }, config: cfg, base: cdn };
  }, [loaderKey]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const updates = attributeUpdates(shown.current, attrs);
    if (Object.keys(updates).length && webView.current) {
      webView.current.injectJavaScript(updateScript(updates));
    }
    shown.current = attrs;
  }, [attrsKey]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (JSON.stringify(shownSpecs.current) !== specsKey && webView.current) {
      webView.current.injectJavaScript(actionsScript(specs));
    }
    shownSpecs.current = specs;
  }, [specsKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const open = (url) => (onOpenUrl ? onOpenUrl(url) : Linking.openURL(url));

  const onMessage = (event) => {
    let data;
    try {
      data = JSON.parse(event.nativeEvent.data);
    } catch (e) {
      return;
    }
    if (data.kind === "height" && typeof data.value === "number" && data.value > 0) {
      setMeasured((h) => (Math.abs(h - data.value) >= 1 ? data.value : h));
    } else if (data.kind === "open" && typeof data.value === "string") {
      open(data.value);
    } else if (data.kind === "action" && data.value && typeof data.value.id === "string") {
      if (onAyaAction) onAyaAction(data.value);
    } else if (data.kind === "error") {
      console.warn(`[quran-madina-native] ${data.value}` +
        (bundled ? " (run `npx quran-madina-native-bundle` and add the folder to the app)" : ""));
    }
  };

  // The page itself loads in place; any other navigation is a link (the translate buttons).
  const onShouldStartLoadWithRequest = (request) => {
    const url = request.url || "";
    if (url.startsWith("about:") || url.startsWith("data:") || url.startsWith(base) || url.startsWith("file:")) {
      return true;
    }
    open(url);
    return false;
  };

  return React.createElement(
    View,
    { style: [{ height: height ?? measured }, style] },
    React.createElement(WebView, {
      ref: webView,
      source,
      originWhitelist: ["*"],
      javaScriptEnabled: true,
      scrollEnabled: false,
      showsVerticalScrollIndicator: false,
      showsHorizontalScrollIndicator: false,
      setSupportMultipleWindows: false,
      style: { backgroundColor: "transparent" },
      // the bundled page reads its options before it starts; injected again on load as a fallback
      injectedJavaScriptBeforeContentLoaded: bundled ? `window.QMH_CONFIG = ${JSON.stringify(config)}; true;` : undefined,
      onLoadEnd: () => webView.current && webView.current.injectJavaScript(
        startScript({ ...config, attrs: shown.current, ayaActions: shownSpecs.current })),
      // bundled files are read from the app (file:// pages fetching file:// data)
      allowFileAccess: !!bundled,
      allowFileAccessFromFileURLs: !!bundled,
      allowUniversalAccessFromFileURLs: !!bundled,
      allowingReadAccessToURL: bundled ? base : undefined,
      onMessage,
      onShouldStartLoadWithRequest,
      ...webViewProps,
    })
  );
}
