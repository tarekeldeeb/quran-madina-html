/*!
 * quran-madina-html v2.2.2
 * A Madina Quran HTML Renderer without images.
 * https://github.com/tarekeldeeb/quran-madina-html#readme
 *
 * Copyright (c) Tarek Eldeeb
 * Licensed under the "Waqf" General Public License 2.0, 3 Muharram 1435
 * https://github.com/ojuba-org/waqf/tree/master/2.0
 * See LICENSE.md in the package for details.
 */
(
  function(){
  var name = "quran-madina-html";

  // ==========================================================================
  // Configuration & shared state
  // ==========================================================================

  // Base URL the runtime fetches its CSS + JSON DB from. Default: the repo root when served
  // from localhost (local dev / demo), otherwise the unpkg package root. A `data-cdn` attribute
  // on the loader <script> overrides this, which is what makes the tag embeddable inside a
  // bundled app (React dev server, Capacitor, etc.) where the host is also "localhost" but the
  // assets do NOT live at `../`. Resolved below once the script element is known.
  var cdn = (/localhost/.test(document.location.hostname))? "../":`https://www.unpkg.com/${name}/`;
  var madina_data = {"content":"Loading .."};

  // A render token counts as a selectable word only if it contains an Arabic letter. Everything
  // else in the Madina text appears as its own whitespace-separated token and must NOT be counted
  // or selectable, otherwise the words= index drifts: aya-number ornaments (ornate parens ﴿N﴾ for
  // Hafs/Uthman/me_quran, end-of-aya ۝N for Amiri), waqf/pause marks (ۖ ۗ ۘ ۙ ۚ ۛ ۜ), and the
  // ۞ (rub-el-hizb) / ۩ (sajdah) ornaments — none of these carry an Arabic letter.
  // ASCII \u escapes on purpose: a literal Arabic class here would be misread if the script is ever
  // served without charset=utf-8 (some static servers do this), breaking the match and hiding every
  // word. The ranges are U+0621-U+064A (basic Arabic letters) and U+0671-U+06D3 (alef-wasla etc.).
  var ARABIC_LETTER = /[\u0621-\u064A\u0671-\u06D3]/;

  // The traditional basmala ligature (U+FDFD). Since 0.9.0 the DB stores each sura's basmala
  // decoration as its 4 real word tokens so the words= indexing can count and select them
  // individually - but whenever the *complete* basmala shows (a full page/aya render, or a
  // words= selection covering all 4 words) the renderer swaps the tokens for this ligature,
  // matching the ornamental basmala line of the printed Mushaf. A partial selection (1-3 of the
  // 4 words) renders the individual tokens so the selection stays visible.
  var BASMALA_LIGATURE = "\uFDFD";
  function isBasmalaSlot(sura_idx, aya_idx){
    // Internal aya index 1 is the basmala decoration slot of every sura except Al-Fatiha (whose
    // slot 1 holds its title; its basmala is real aya 1). At-Tawba's slot exists but is blank.
    return aya_idx === 1 && sura_idx !== 0;
  }

  // ==========================================================================
  // Small utilities
  // ==========================================================================

  // In-memory cache of every DB shard/manifest fetched so far this page load, keyed by URL.
  // sessionStorage backs it up so a full page reload/navigation within the same tab still hits
  // the cache instead of the network (in-memory state alone would reset on reload).
  var jsonCache = {};
  function readJSONCache(path){
    if(jsonCache[path]) return jsonCache[path];
    try {
      var raw = sessionStorage.getItem("quran-madina-html:" + path);
      if(raw){ return (jsonCache[path] = JSON.parse(raw)); }
    } catch(e) { /* sessionStorage disabled/full or entry corrupted: fall through to network */ }
    return null;
  }
  function writeJSONCache(path, data, raw){
    jsonCache[path] = data;
    try { sessionStorage.setItem("quran-madina-html:" + path, raw); }
    catch(e) { /* quota exceeded or sessionStorage disabled: in-memory cache still holds it */ }
  }
  // Drops every cached shard (sessionStorage + in-memory) fetched from under `base` so far this
  // session. Used when the manifest's content_hash (see bootFromManifest) shows the DB was
  // rebuilt/updated since a shard from the old content was cached - otherwise that stale shard
  // would keep being served from cache for the rest of the browser session.
  function clearShardCache(base){
    try {
      for(var i = sessionStorage.length - 1; i >= 0; i--){
        var key = sessionStorage.key(i);
        if(key && key.indexOf("quran-madina-html:" + base) === 0) sessionStorage.removeItem(key);
      }
    } catch(e) { /* sessionStorage disabled */ }
    Object.keys(jsonCache).forEach(function(path){
      if(path.indexOf(base) === 0) delete jsonCache[path];
    });
  }
  // path -> array of {success, error} waiting on an XHR already in flight for that path. Several
  // <quran-madina-html> elements on the same page independently need the same juz' shard and would
  // otherwise each fire their own fetch before the first one lands (loadedJuz only flips to true
  // once a fetch *completes*); queuing waiters here coalesces them into a single request.
  var pendingRequests = {};
  // A file:// (or app-bundle) URL, as in a React Native or Cordova WebView loading bundled files,
  // answers with status 0 rather than 200: the body is the file.
  function localFileLoaded(xhr, path){
    if(xhr.status !== 0 || !xhr.responseText) return false;
    try { return !/^https?:$/.test(new URL(path, document.baseURI).protocol); }
    catch(e) { return false; }
  }
  function loadJSON(path, success, error, forceFresh){
    // forceFresh (used for manifest.json only): skip the cache read and always hit the network.
    // The manifest is small, so this costs nothing, and it's what lets bootFromManifest notice a
    // rebuilt/updated DB on every load rather than only once per session.
    var cached = !forceFresh && readJSONCache(path);
    // Deferred even on a cache hit: callers (the module boot sequence in particular) rely on
    // loadJSON always resolving asynchronously, so a cache hit can't race ahead of a cache miss
    // and complete synchronously while another caller's fetch is still pending.
    if(cached){ if(success) setTimeout(function(){ success(cached); }, 0); return; }
    if(pendingRequests[path]){ pendingRequests[path].push({success: success, error: error}); return; }
    pendingRequests[path] = [{success: success, error: error}];
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function()
    {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            var waiters = pendingRequests[path];
            delete pendingRequests[path];
            if (xhr.status === 200 || localFileLoaded(xhr, path)) {
                var data = JSON.parse(xhr.responseText);
                writeJSONCache(path, data, xhr.responseText);
                waiters.forEach(function(w){ if(w.success) w.success(data); });
            } else {
                waiters.forEach(function(w){ if(w.error) w.error(xhr); });
            }
        }
    };
    xhr.open("GET", path, true);
    xhr.send();
  }
  function print(str){
    console.log(`${name}> ${str}`);
  }
  function pad2(n){ return (n < 10 ? "0" : "") + n; }
  function isTrue(val){
    // Boolean HTML attribute: true when present as `headless`, `headless=""`, "true", "1" or "yes".
    if(val == null) return false;
    var v = String(val).trim().toLowerCase();
    return v === "" || v === "true" || v === "1" || v === "yes";
  }
  function safeBaseUrl(value){
    // data-cdn is the base the CSS, databases and fonts load from: resolve it against the page,
    // with a trailing slash, and refuse schemes that run code instead of fetching a file.
    // Everything else stays allowed (http(s), file: in app bundles, app schemes such as
    // capacitor: or tauri:), so self-hosted and offline setups keep working.
    var url;
    try { url = new URL(String(value), document.baseURI); }
    catch(e){ return null; }
    if(/^(javascript|data|vbscript):$/i.test(url.protocol)) return null;
    url.search = ""; url.hash = "";
    return url.href.replace(/\/?$/, "/");
  }
  function resolveUrl(url){
    // Resolve an asset URL from the DB against `cdn`. Absolute (http(s):// or //) URLs are used
    // as-is for backward compatibility with older DBs; relative paths (e.g. "assets/fonts/X.woff2")
    // are prefixed with `cdn`, so a `data-cdn` override redirects fonts too (self-host / offline).
    if(url == null) return url;
    if(/^(https?:)?\/\//.test(url)) return url;
    return cdn + String(url).replace(/^\//, "");
  }
  // Properties mirror their attributes, as on built-in elements: `tag.sura = 2` sets sura="2",
  // which re-renders. Frameworks that bind properties on custom elements (Vue, Svelte, Angular,
  // Lit) then work like plain HTML. null/undefined/false remove the attribute; true sets it empty.
  function reflectAttribute(tag, key, value){
    if(value === undefined || value === null || value === false) tag.removeAttribute(key);
    else tag.setAttribute(key, value === true ? "" : String(value));
  }

  function relativeLuminance(rgbString){
    // WCAG relative luminance of a getComputedStyle "rgb(r, g, b)"/"rgba(...)" string.
    var m = rgbString && rgbString.match(/[\d.]+/g);
    if(!m) return 1; // unparseable: assume light text (safer default is the dark-pair path)
    function lin(c){ c = c / 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }
    return 0.2126 * lin(+m[0]) + 0.7152 * lin(+m[1]) + 0.0722 * lin(+m[2]);
  }
  function applyMarkTextScheme(tag){
    // highlight=/error= need a bg+text pair that contrasts with whatever the host page's actual
    // ambient text color is. Reading the real computed color (rather than guessing from
    // prefers-color-scheme) works regardless of how/whether the host implements dark mode.
    var lum = relativeLuminance(getComputedStyle(tag).color);
    tag.setAttribute("data-qmh-text-scheme", lum > 0.5 ? "dark" : "light");
  }

  // ==========================================================================
  // Attribute range parsing
  // ==========================================================================

  function parseSuraRange(str){
    // Sura count is 0-based, we need to subtract 1
    return Array(2).fill(str.split('-')[0]-1);
  }
  function parseAyaRange(str){
    // Aya count is 0-based, there are 2 extra ayas (Title + Basmala)
    if(str.split('-').length == 2) return str.split('-').map(elem => parseInt(elem) +1);
    return Array(2).fill(parseInt(str.split('-')[0])+1);
  }
  function parseWordsRange(str){
    // 1-based, inclusive. "n" => [n,n]; "n:m" or "n-m" => [n,m]. Returns null if malformed.
    if(str == null) return null;
    var parts = str.split(/[-:]/).map(elem => parseInt(elem, 10));
    if(parts.length == 1) parts = [parts[0], parts[0]];
    if(parts.length != 2 || isNaN(parts[0]) || isNaN(parts[1])) return null;
    if(parts[0] < 1 || parts[1] < parts[0]) return null; // 1-based; start must not exceed end
    return parts;
  }
  function clampedOrNull(label, range, bounds){
    // Validates a highlight=/error= range against the words actually being displayed
    // (bounds = [min,max], 1-based inclusive). Malformed (range already null) or
    // out-of-bounds -> warn and skip (return null) rather than aborting the whole
    // render, unlike a malformed words= (which falls back to the normal verse render).
    if(range == null) return null;
    if(range[0] < bounds[0] || range[1] > bounds[1]){
      print(`${label} range ${range[0]}-${range[1]} outside displayed words ${bounds[0]}-${bounds[1]}, ignoring`);
      return null;
    }
    return range;
  }
  function applyInlineOverride(inlineOpt, multiline){
    // inline="no": force the multiline/header layout even for a selection that would fit one line.
    // inline="yes": force a single inline line even for a selection that overflows it - NOT
    // IMPLEMENTED YET, falls back to the auto (default, current-fits-one-line) behavior.
    // inline="auto"/absent: auto (default).
    if(inlineOpt == null || inlineOpt === "auto") return multiline;
    if(inlineOpt === "no") return true;
    if(inlineOpt === "yes"){
      print('inline="yes" is not implemented yet; falling back to "auto"');
      return multiline;
    }
    print(`Bad inline parameter: ${inlineOpt}`);
    return multiline;
  }

  // ==========================================================================
  // Word counting (for the words= selection)
  // ==========================================================================

  function isWordToken(token){ return ARABIC_LETTER.test(token); }
  function isCountableAya(sura_idx, aya_idx){
    // Title slots never count as words: index 0 everywhere, and Al-Fatiha's title lives
    // at index 1 (where every other sura keeps its counted basmala) since its own
    // basmala is real aya 1 - see collectWordParts.
    return aya_idx >= (sura_idx === 0 ? 2 : 1);
  }
  function countPartWords(part){
    // Selectable words in a single render part: whitespace-separated tokens that carry a letter
    // (markers, pause marks and ornaments are excluded by isWordToken).
    var n = 0;
    part.t.split(/\s+/).forEach(function(token){
      if(isWordToken(token)) n = n + 1;
    });
    return n;
  }
  function countAyaWords(aya){
    // Number of selectable words in an aya, summed over its render parts.
    var n = 0;
    aya.r.forEach(function(part){ n = n + countPartWords(part); });
    return n;
  }
  // Pre-render bounds for validating highlight=/error= (see clampedOrNull): the total
  // count of countable words in whatever is about to be rendered, so a range can be
  // checked against what's actually displayed *before* the render pass builds it. Not
  // used for the render pass itself - words= mode already has its bound (words_range).
  function ayaLastPage(aya){
    // An aya's parts carry only their line: a part on a lower line than the one before it
    // has moved on to the next page.
    var page = aya.p, prev = null;
    for(var i = 0; i < aya.r.length; i++){
      if(prev !== null && aya.r[i].l < prev) page = page + 1;
      prev = aya.r[i].l;
    }
    return page;
  }
  function countVerseRangeWords(sura_idx, aya_from, aya_to){
    // Verse mode is always single-sura (parseSuraRange forces sura_to = sura_from).
    var ayas = madina_data.suras[sura_idx].ayas, n = 0;
    for(var a = aya_from; a <= aya_to; a++){
      if(isCountableAya(sura_idx, a)) n = n + countAyaWords(ayas[a]);
    }
    return n;
  }
  function countPageWords(sura_from, aya_from, sura_to, aya_to, page){
    // Flat counting pass over a page's real ayas - deliberately not reusing the main
    // render loop's line-grouping/sura-jump bookkeeping (doRender), since that exists
    // only to build line-keyed DOM groups and isn't needed for a total.
    var n = 0;
    for(var s = sura_from; s <= sura_to; s++){
      var ayas = madina_data.suras[s].ayas;
      var from = (s === sura_from) ? aya_from : 0;
      var to = (s === sura_to) ? aya_to : ayas.length - 1;
      for(var a = from; a <= to; a++){
        var aya = ayas[a];
        if(aya === undefined || aya.p !== page) continue;
        if(isCountableAya(s, a)) n = n + countAyaWords(aya);
      }
    }
    return n;
  }

  // ==========================================================================
  // DOM building blocks (icons, hover, header/copy chrome, classes)
  // ==========================================================================

  function hoverShade(elm){
    // A faint wash of the text's own colour: subtle on light and dark pages alike (iOS keeps
    // the hover on after a tap). --qmh-hover on the tag overrides it.
    var custom = getComputedStyle(elm).getPropertyValue("--qmh-hover").trim();
    if(custom) return custom;
    var rgb = (getComputedStyle(elm).color.match(/[\d.]+/g) || [128, 128, 128]).slice(0, 3);
    return `rgba(${rgb.join(",")},0.12)`;
  }
  function hoverByType(class_name, type="class", color_bg=null, color_out="transparent"){
    var elms = (type.toLowerCase() === "tag") ? document.getElementsByTagName(class_name)
                                              : document.getElementsByClassName(class_name);
    Array.from(elms).forEach(function(elm) {
      elm.onmouseover = function() {
        // Only verses with something to do on click are highlighted (see ayaActionsFor).
        if(!elm._qmhAya || !ayaActionsFor(elm._qmhAya.tag, ayaContext(elm)).length){
          elm.style.cursor = "";
          Array.from(elms).forEach(function(element){ element.style.backgroundColor = color_out; });
          return;
        }
        elm.style.cursor = "pointer";
        var bg = color_bg || hoverShade(elm);
        Array.from(elms).forEach(function(element) {
          element.style.backgroundColor = bg;
        });
      };
      elm.onmouseout = function() {
        Array.from(elms).forEach(function(element) {
          element.style.backgroundColor = color_out;
        });
      };
    });
  }
  function getAyaClass(sura, aya){
    const zeroPad = (num, places) => String(num).padStart(places, '0');
    const classes = [`${name}-part`, `${name}-${zeroPad(sura,3)}-${zeroPad(aya,3)}`];
    // Decorate Sura Name lines: slot 0 (aya == -1 here) everywhere, plus Al-Fatiha's title,
    // which lives at slot 1 (== aya 0 here) since its basmala is real aya 1. (1,0) is unique
    // to that title: Al-Fatiha's slot 0 is a blank placeholder that never renders.
    if(aya == -1 || (sura == 1 && aya == 0)) classes.push("quran-madina-html-sura-start");
    return classes;
  }
  function getCopyIcon(){
    let htmlString = '<svg viewBox="0 0 24 24" class="quran-madina-html-icon quran-madina-html-icon-copy">'+
      '<path d="M16.02 20.96H3.78c-.41 0-.75-.34-.75-.75V7.74c0-.41.34-.75.75-.75h7.87c.21 0 '+
      '.39.08.53.22l4.37 4.37c.14.14.22.32.22.53v8.11c0 .4-.34.74-.75.74ZM4.53 19.47h10.75v-6'+
      '.61h-3.62c-.41 0-.75-.34-.75-.75V8.48H4.53v10.99Z"></path><path d="m20.74 7.63-4.37-4.'+
      '37c-.14-.14-.36-.2-.53-.22H8.01c-.41 0-.75.34-.75.75V5.5h1.49v-.97h6.34v3.62c0 .41.34.'+
      '75.75.75h3.62v8.19h-1.2v1.49h1.95c.41 0 .75-.34.75-.75V8.16c0-.21-.08-.4-.22-.53Z">'+
      '</path></svg>';
      var div = document.createElement('div');
      div.innerHTML = htmlString.trim();
      return div.firstChild;
  }
  function getTranslateIcon(){
    let htmlString = '<svg class="quran-madina-html-icon quran-madina-html-icon-translate" viewBox="0 0 820 615"><path d="M70 '+
    '1.9C37.6 8.8 12.6 33.4 3.4 67.5c-1.8 6.6-1.9 11.9-1.9 98v91l2.3 8c5.1 17.8 17 36.4 29.9 46.7 '+
    '10.8 8.6 25.4 15.4 38.1 17.8 3.1.6 15.2 1 26.8 1 17.7 0 21.3.2 21.7 1.4.4.9.6 17.1.7 36.1 0 '+
    '32.4.2 34.9 2 38.5 6.4 12.5 21.4 17.4 33.3 10.8 2.3-1.3 7.5-6.4 12.1-11.9l63-74.1c.6-.4 16.3-.8 '+
    '34.9-.8H300l-.2-18.3-.3-18.2-42.8.1-43.1.5c-.2.2-12.7 15.1-27.9 33.1-15.1 18-27.8 32.4-28.1 '+
    '32.1-.3-.4-.6-15.3-.6-33.2v-32.6l-38.8-.1c-42.1-.2-43.9-.4-54.3-6-6.5-3.6-16.9-14.6-20.2-21.5-5.8'+
    '-11.9-5.7-10-5.7-100.7 0-92-.2-89.4 6.3-101.7 3.9-7.3 13.5-17.1 20.3-20.7C76 36.7 66.1 37 244.5 '+
    '37L412 38.1c18 4.1 33.5 20.5 37.5 39.6 2.2 10.2 2.1 164.6 0 174.8-3.9 18.3-16.4 32.7-33.5 '+
    '38.5-3.2 1.1-7.8 2-10 2-3.1 0-4 .4-4 1.7 0 1-.2 8.8-.3 17.3-.2 8.5-.2 16.2 0 17 .9 3.3 21.7-.5 '+
    '34.1-6 13.7-6.3 27.5-17.9 36.2-30.5 5-7.2 10.8-20.4 13.2-30.1l2.3-8.9V165 '+
    '76.5l-2.3-9c-8.1-31.4-30.5-54.9-61.7-64.8l-7-2.2-169-.2C87.7.1 78 .2 70 1.9zm277.294 '+
    '102.559q19.5-.5 28.25 24.5 2.5 7.25-3.75 19.75-5.75 11.75-9.75 16-19.5 21.5-67 25.25-27.75 '+
    '2.25-50.25-2.25-5.25 38.25-16.5 50-26 26.75-66 29.5-27.75 2-42.5-11-20.25-17.75-16.5-48.5 '+
    '3-23.75 14.25-42.5 2.75-4.5 4.75-7.5 2-3 3-4.25 2.25-2.75 4.75-1.25 2.75 1.5 0 6.25-12.75 '+
    '24.5-10 45 4 30.5 44.5 30.5 30.25 0 53.25-15.5 12.5-8.25 '+
    '14.75-14.25-2.25-20.75-13.75-35.75-3.5-4.25-1.75-8l9.5-23.5q3-7.5 8.25 1.25l8.75 14.75q7.75 4.25 '+
    '28.25 5 16.75-19.25 39.25-36.25 22.5-16.75 36.25-17.25zm11.5 40.5q-12.5-9.5-31.75-5.75-19 '+
    '3.75-41.25 19.5 50.75.5 73-13.75zm-71.5-89.75q1.5-2 4.25-1.25 5 1.75 9.5 4.5 4.75 2.75 8.75 6.25 '+
    '2 2 .75 4.5l-12 19q-1.75 2.5-4.5.5-2.5-2-18-11.25-2.75-1.75-1-4.25zm278.784 '+
    '232.623c-4.7.4-4.7.4-6.7 6.1-1.2 3.1-9.3 25.9-18 50.7l-36.6 102.7-3.5 9.8h17.9 17.8l5.7-17 '+
    '5.7-17h31.7 31.8l5.6 17.2 5.6 17.3 17.9-.3 '+
    '18-.3-6-17.2-15-43.2-13.3-38.5-14.1-41-9.9-28.7c-.3-.6-30.2-1.1-34.6-.6zm35.7 106c-.2.2-10 '+
    '.2-21.9.1l-21.5-.3 9.8-29.5 11-32.5c1.2-2.9 1.8-1.4 12.1 29.4l10.5 32.8zm148.8 139.609c32.4-6.9 '+
    '57.4-31.5 66.6-65.6 1.8-6.6 1.9-11.9 '+
    '1.9-98v-91l-2.3-8c-5.1-17.8-17-36.4-29.9-46.7-10.8-8.6-25.4-15.4-38.1-17.8-3.1-.6-15.2-1-26.8-1-1'+
    '7.7 0-21.3-.2-21.7-1.4-.4-.9-.6-17.1-.7-36.1 '+
    '0-32.4-.2-34.9-2-38.5-6.4-12.5-21.4-17.4-33.3-10.8-2.3 1.3-7.5 6.4-12.1 11.9l-63 '+
    '74.1c-.6.4-16.3.8-34.9.8h-33.7l.2 18.3.3 18.2 42.8-.1 43.1-.5c.2-.2 12.7-15.1 27.9-33.1 15.1-18 '+
    '27.8-32.4 28.1-32.1.3.4.6 15.3.6 33.2v32.6l38.8.1c42.1.2 43.9.4 54.3 6 6.5 3.6 16.9 14.6 20.2 '+
    '21.5 5.8 11.9 5.7 10 5.7 100.7 0 92 .2 89.4-6.3 101.7-3.9 7.3-13.5 17.1-20.3 20.7-11.4 6.1-1.5 '+
    '5.8-179.9 5.8-108.2 0-164.5-.4-167.5-1.1-18-4.1-33.5-20.5-37.5-39.6-2.2-10.2-2.1-164.6 0-174.8 '+
    '3.9-18.3 16.4-32.7 33.5-38.5 3.2-1.1 7.8-2 10-2 3.1 0 4-.4 4-1.7 0-1 .2-8.8.3-17.3.2-8.5.2-16.2 '+
    '0-17-.9-3.3-21.7.5-34.1 6-13.7 6.3-27.5 17.9-36.2 30.5-5 7.2-10.8 20.4-13.2 30.1l-2.3 8.9v88.5 '+
    '88.5l2.3 9c8.1 31.4 30.5 54.9 61.7 64.8l7 2.2 169 .2 177.5-1.6z"/></svg>';
    var div = document.createElement('div');
    div.innerHTML = htmlString.trim();
    return div.firstChild;
  }
  function getLoadingIcon(){
    return '<img src="data:image/png;base64,R0lGODlhIAAKAPQVALSytMzOzLy6vPz6/NTW1LS2tNTS1Ly+vPz+'+
    '/AQCBFxaXOzu7BwaHCQmJGxubCwuLBQWFGRmZPT29CwqLHx6fAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'+
    'CH/C05FVFNDQVBFMi4wAwEAAAAh+QQFEAAVACwAAAAAIAAKAAAFYyBCHEJZGkMlkuaBqtTTzLMjjUCuA0GF77keJUEsEi'+
    'MsYK6SVFYeRiOjCWQqdc9oEWK6Wq+FrDbBBYcLZrG2DP56G2Myded2QscQA7gX2FcccQoDfWg7CCqEQIcSEQwQj4+CIQA'+
    'h+QQFEAAVACwLAAAAFQAKAAAFSOBAPU1ZOlKFEIfguoaYzPQcVSyg70Dw1DVGpcXjNYA0yLBoRM6UL2bh6IRKdVSk9fqr'+
    'Lq8OZ0LxlUoiDIharVioAoX4LiAJAQAh+QQFEAAVACwAAAAAHgAKAAAFXeBAPU1ZOlKFEIfgusagsq9LJXiORxUN/MBA'+
    'D0h86HSMSotIVDJ/jWMO4nz+qsyJFEetPbHFbaJrvRas2i25DAYa1e3mkukQK+I/YcAqiTAggIAKCzNnhj8IhYcFIQAh'+
    '+QQFEAAJACwAAAAAIAAKAAAEOhCRI2o1I+nNu08TII5A8J0fRZJou6mrmBwuasVF3cLxrKc4Ge3X4a2IH0PQhOwMAoUo'+
    'CZHIaFiuQQQAOw==" alt="Loading .." />';
  }
  function buildHeader(sura){
    // The multiline chrome: sura name + copy + translate icons, shared by both render paths.
    // The icons stay direct children: copyToClipboard reaches the host via parentElement twice.
    // v2 names carry per-word height corrections (nf, see cursive_fix.py): one span per word.
    var header = document.createElement("quran-madina-html-header");
    var title = document.createElement("span");
    title.className = `${name}-sura-name`;
    if(sura.nf){
      sura.name.split(" ").forEach(function(word, j){
        if(j > 0) title.appendChild(document.createTextNode(" "));
        var span = document.createElement("span");
        span.textContent = word;
        if(sura.nf[j]) span.style.fontFeatureSettings = v2FeatureSettings(sura.nf[j]);
        title.appendChild(span);
      });
    } else {
      title.textContent = sura.name;
    }
    header.appendChild(title);
    var copy = getCopyIcon(); copy.addEventListener("click", copyToClipboard);
    var translation = getTranslateIcon(); translation.addEventListener("click", openTranslate);
    header.appendChild(translation);   // right to left: name, translate, copy at the far left
    header.appendChild(copy);
    return header;
  }
  // ==========================================================================
  // Per-aya click popup: clicking a hovered aya shows a small copy/translate
  // popup scoped to *that* aya, instead of the frame-level buildHeader actions
  // above (which always act on the whole frame / its first aya). Inline (single-line)
  // renders used to also get their own lone copy button (buildInlineCopy) - removed,
  // since this popup already covers them (their aya divs are wired the same way).
  // ==========================================================================

  var openAyaPopup = null; // {popup, outsideClick, onEscape} for the currently shown popup, if any
  function closeAyaPopup(){
    if(!openAyaPopup) return;
    openAyaPopup.popup.classList.remove(`${name}-open`);
    document.removeEventListener("click", openAyaPopup.outsideClick);
    document.removeEventListener("keydown", openAyaPopup.onEscape);
    openAyaPopup = null;
  }
  function getOrCreateAyaPopup(tag){
    // One popup for the whole document, lazily created and reused across clicks and host tags
    // (only one is ever open — see openAyaPopup). It must live on document.body, NOT inside the
    // host tag: it is position:fixed, and ANY transformed ancestor — a line's own scaleX, or a
    // host-app wrapper with transform/perspective/filter (e.g. quranquiz's card-flip rotateY) —
    // would become its containing block, re-basing the viewport coordinates positionAyaPopup
    // computes and trapping it under the ancestor's overflow clipping and stacking context.
    // Renders call closeAyaPopup() since tag.innerHTML="" no longer discards it.
    var popup = document.querySelector(`body > ${name}-aya-popup`);
    if(!popup){
      popup = document.createElement(`${name}-aya-popup`);
      popup.setAttribute("role", "toolbar");
      document.body.appendChild(popup);
    }
    // The --qmh-* theme vars are scoped to the quran-madina-html tag; copy the host tag's
    // resolved values so the body-level popup keeps the tag's (possibly customized) theme.
    ["--qmh-header", "--qmh-background"].forEach(function(prop){
      popup.style.setProperty(prop, getComputedStyle(tag).getPropertyValue(prop));
    });
    return popup;
  }
  function ayaFragmentsText(tag, class_name){
    // Every line fragment of this aya shares class_name (see hoverByType/getAyaClass), so joining
    // them gives the aya's full text even when it wraps across lines. Scoped to `tag`, not
    // document-wide: the same aya can appear in more than one <quran-madina-html> tag on a page
    // (e.g. a normal render and a headless="true" one of the same range), which would otherwise
    // duplicate the copied text with fragments from every tag that happens to share the class.
    var text = Array.from(tag.getElementsByClassName(class_name))
      .map(function(e){ return e.textContent; })
      .join(" ").replace(/\s+/g, " ").trim();
    return isV2() ? v2CleanText(text) : text;
  }
  function positionAyaPopup(popup, elm){
    var rect = elm.getBoundingClientRect();
    popup.style.left = Math.max(4, rect.left) + "px";
    // Prefer floating above the aya; if that would run off the top of the viewport, place it below.
    var estHeight = 34;
    popup.style.top = (rect.top - estHeight - 6 > 0 ? rect.top - estHeight - 6 : rect.bottom + 6) + "px";
  }
  // ==========================================================================
  // Verse actions: the buttons of the popup a click on a verse opens. A page-wide registry
  // (registerAction & co., static methods on the element class), with copy and translate as
  // ordinary built-in entries. A tag's `actions` attribute picks a subset ("copy bookmark") or
  // none ("none", also hides the header icons via CSS). A verse with no action left (after the
  // attribute and each action's `when`) is plain text: no hover, no pointer, no click.
  // ==========================================================================

  var DEFAULT_ACTIONS = [
    {id: "copy", title: "Copy", order: 10, icon: function(){ return getCopyIcon(); },
      onSelect: function(aya){
        var text = "“" + aya.text + "”" + "\n\n" + aya.suraName;
        navigator.clipboard.writeText(text);
        alert("⎘ تم نسخ:\n\n" + text);
      }},
    {id: "translate", title: "Translation", order: 20, icon: function(){ return getTranslateIcon(); },
      onSelect: function(aya){ window.open(`https://quran.com/${aya.sura}/${aya.aya}`, '_blank'); }}
  ];
  var ayaActions = DEFAULT_ACTIONS.slice();

  function checkAction(spec){
    if(!spec || typeof spec !== "object") throw new TypeError(`${name}: an action is an object`);
    if(typeof spec.id !== "string" || !spec.id.trim()) throw new TypeError(`${name}: an action needs an id`);
    if(typeof spec.onSelect !== "function") throw new TypeError(`${name}: action "${spec.id}" needs onSelect`);
    if(spec.when != null && typeof spec.when !== "function") throw new TypeError(`${name}: action "${spec.id}": when must be a function`);
    return {
      id: spec.id.trim(), title: spec.title || spec.id.trim(), icon: spec.icon,
      order: Number.isFinite(spec.order) ? spec.order : 100, when: spec.when || null, onSelect: spec.onSelect
    };
  }
  function actionsChanged(){
    ayaActions.sort(function(x, y){ return x.order - y.order; });
    closeAyaPopup();
    Array.from(document.getElementsByTagName(name)).forEach(updateInteractive);
  }
  function tagActionIds(tag){
    // null: every registered action. []: none. Otherwise the listed ids.
    var attr = tag.getAttribute("actions");
    if(attr == null) return null;
    var ids = attr.split(/[\s,]+/).filter(Boolean);
    return (ids.length === 1 && ids[0].toLowerCase() === "none") ? [] : ids;
  }
  function ayaActionsFor(tag, ctx){
    var ids = tagActionIds(tag);
    return ayaActions.filter(function(action){
      if(ids !== null && ids.indexOf(action.id) < 0) return false;
      if(!action.when || !ctx) return true;
      try { return !!action.when(ctx); }
      catch(e){ console.error(`${name}: action "${action.id}" when() failed`, e); return false; }
    });
  }
  function updateInteractive(tag){
    // A class for styling: the tag has at least one action (before per-verse `when` filters).
    tag.classList.toggle(`${name}-interactive`, ayaActionsFor(tag, null).length > 0);
  }
  function ayaContext(elm){
    // What an action's when()/onSelect() gets. text is computed on first read only.
    var info = elm._qmhAya, tag = info.tag;
    var sura_data = madina_data.suras[info.sura - 1] || {};
    var aya_data = sura_data.ayas && sura_data.ayas[info.aya + 1];
    var ctx = {
      sura: info.sura, aya: info.aya, suraName: sura_data.name, layout: doc_layout,
      page: aya_data ? aya_data.p : null, tag: tag, element: elm, close: closeAyaPopup
    };
    Object.defineProperty(ctx, "text", {enumerable: true, get: function(){
      return ayaFragmentsText(tag, info.class_name);
    }});
    return ctx;
  }
  function actionIcon(action){
    var icon = action.icon;
    if(typeof icon === "function") icon = icon();
    if(icon instanceof Element) return icon.isConnected ? icon.cloneNode(true) : icon;
    if(typeof icon === "string" && icon.trim().charAt(0) === "<"){
      var holder = document.createElement("span");
      holder.innerHTML = icon.trim();   // the page's own markup (developer-supplied, not visitor input)
      return holder.firstElementChild || document.createTextNode(action.title);
    }
    if(typeof icon === "string" && icon){
      var img = document.createElement("img");
      img.src = icon; img.alt = "";
      return img;
    }
    return document.createTextNode(action.title);
  }
  function showAyaPopup(tag, elm, ctx, actions){
    closeAyaPopup(); // only one popup open at a time
    var popup = getOrCreateAyaPopup(tag);
    popup.textContent = "";
    actions.forEach(function(action){
      var button = document.createElement("button");
      button.type = "button";
      button.className = `${name}-action ${name}-action-${action.id.replace(/[^\w-]/g, "_")}`;
      button.title = action.title;
      button.setAttribute("aria-label", action.title);
      button.appendChild(actionIcon(action));
      button.onclick = function(e){
        e.stopPropagation();
        closeAyaPopup();
        try { action.onSelect(ctx); }
        catch(err){ console.error(`${name}: action "${action.id}" failed`, err); }
      };
      popup.appendChild(button);
    });
    positionAyaPopup(popup, elm);
    popup.classList.add(`${name}-open`);
    var outsideClick = function(e){ if(!popup.contains(e.target)) closeAyaPopup(); };
    var onEscape = function(e){ if(e.key === "Escape") closeAyaPopup(); };
    document.addEventListener("click", outsideClick);
    document.addEventListener("keydown", onEscape);
    openAyaPopup = {popup: popup, outsideClick: outsideClick, onEscape: onEscape};
  }
  function wireAyaClick(tag, class_name, sura, aya){
    // Decoration slots stay non-clickable, deliberately: the title has nothing to copy or
    // translate, and the basmala — although it now renders as real, counted word spans — has no
    // quran.com verse of its own to deep-link (it's only a verse in Al-Fatiha, where it's real
    // aya 1 and clickable through the normal path anyway).
    if(aya < 1) return;
    // Scoped to `tag`, not document-wide: the same aya/class can exist in another
    // <quran-madina-html> tag on the page, whose elements must not be rebound to *this* tag/popup.
    Array.from(tag.getElementsByClassName(class_name)).forEach(function(elm){
      elm._qmhAya = {tag: tag, class_name: class_name, sura: sura, aya: aya};
      // Overwrite (not addEventListener) so re-registering this aya's other line fragments doesn't
      // stack duplicate handlers - mirrors hoverByType's onmouseover/onmouseout assignment above.
      elm.onclick = function(e){
        var ctx = ayaContext(elm);
        var actions = ayaActionsFor(tag, ctx);
        if(!actions.length) return;   // plain text: let the click through
        e.stopPropagation();
        showAyaPopup(tag, elm, ctx, actions);
      };
    });
  }

  // ==========================================================================
  // Line layout helpers (stretch/center, spacers, structural line starts)
  // ==========================================================================

  function styleMultilineTag(tag, page, headless){
    // Apply the shared block-level chrome to the host tag for a multiline render: font, page-fitting
    // width, and (unless headless) the inset "gutter" shadow whose side depends on the page parity
    // (odd = right page) - headless means no chrome at all, not just no header.
    tag.style = "display:block;";
    tag.style.setProperty('font-family', madina_data.font_family, '');
    tag.style.setProperty('font-size', madina_data.font_size+"px", '');
    if(madina_data.font_family === "me_quran"){
      tag.style.setProperty('line-height', madina_data.font_size*2+"px", '');
    }
    if(isV2()) tag.style.setProperty('line-height', "1.8", ''); // DigitalKhatt line pitch
    tag.style.width = (madina_data.line_width+10)+"px";
    if(!headless){
      tag.style.setProperty('box-shadow', 'inset '+(page%2==1?"":"-")+'8px 0 7px -7px #333', '');
    }
  }
  // --------------------------------------------------------------------------
  // v2 DBs (version: 2). Lines are justified by stretching letters: each word carries its own
  // font-feature-settings (position features of the v2 font, chosen by HarfBuzz at build
  // time) and each space its exact width. All widths are in em, so any font-size renders the same
  // layout. Line geometry lives in madina_data.lines[page-1][line-1] = {k, w, s, x, c}: c narrows
  // the words of a dense line (aya numbers excluded), x the whole line (rare last resort).
  // --------------------------------------------------------------------------
  function isV2(){ return madina_data.version === 2; }
  function v2InitLine(line, page, line_no){
    // Attach the line's layout row; words appended later consume its spaces in order.
    var row = madina_data.lines[page - 1][line_no - 1];
    line._qmh = {row: row, words: 0};
    // z: the page's text is set z times smaller so its widest line fits undistorted;
    // the line keeps its width, measured in its own (smaller) em.
    if(row.z){
      line.style.setProperty('font-size', row.z + "em", '');
      line.style.setProperty('line-height', String(1.8 / row.z), ''); // keep the page's line pitch
    }
    line.style.setProperty('width', (row.w / (row.z || 1)) + "em", '');
    line.style.setProperty('margin', "0 auto", '');
    line.style.setProperty('white-space', "nowrap", '');
    if(row.k !== "text") line.style.setProperty("text-align", "center", "");
    if(row.x) line.style.setProperty("transform", `scaleX(${row.x})`, "");
  }
  function v2FeatureSettings(f){
    // "jp04=3,jp06=1,z12k" -> '"q043", "q061", "z12k"'. The DB keeps HarfBuzz's form (jpKK =
    // alternate v); the browser gets the font's on/off twin of each pair, q<KK><v in base 36>,
    // because Apple's CoreText (every iOS browser) ignores feature values there and always
    // takes alternate 1. Bare tags (z<p><dd>: a height correction, see cursive_fix.py) pass as is.
    return f.split(",").filter(Boolean).map(function(kv){
      var p = kv.split("=");
      if(p[0].slice(0, 2) !== "jp") return `"${p[0]}"`;
      return `"q${p[0].slice(2)}${Number(p[1] || 1).toString(36)}"`;
    }).join(", ");
  }
  function v2PlainFeatures(part, j){
    // An unstretched word (title, basmala, inline quote) takes the height corrections (z tags)
    // of its stretched form, unless the part lists its own (g[j] non-null; "" = none).
    if(part.g && part.g[j] !== null && part.g[j] !== undefined) return part.g[j];
    var f = part.f && part.f[j];
    return f ? f.split(",").filter(function(t){ return t.charAt(0) === "z"; }).join(",") : "";
  }
  function v2InitPlainLine(line){
    // Inline (single-line quote) renders: natural spacing, no stretching.
    line._qmh = {row: null, words: 0};
  }
  function v2AppendWords(parent, line, part, onWord){
    // Append a part's words to `parent` (an aya div inside `line`). Justified lines get their
    // exact space widths and per-word features; other lines (titles, basmala, inline quotes)
    // plain spaces and no stretching. onWord(span, token) lets callers count/hide/mark words.
    if(!line._qmh) v2InitPlainLine(line);
    var state = line._qmh;
    var justified = state.row !== null && state.row.k === "text";
    part.t.split(" ").forEach(function(token, j){
      if(token === "") return;
      if(state.words > 0){
        if(justified){
          var sp = document.createElement("span");
          sp.className = `${name}-space`;
          sp.textContent = " ";
          var w = state.row.s[state.words - 1];
          // a negative space overlaps the word boxes (never the ink): pull the next word in
          sp.style.cssText = w >= 0 ? `display:inline-block;width:${w}em`
            : `display:inline-block;width:0;margin-left:${w}em`;
          parent.appendChild(sp);
        } else {
          parent.appendChild(document.createTextNode(" "));
        }
      }
      state.words = state.words + 1;
      var span = document.createElement("span");
      span.textContent = token;
      span.classList.add(`${name}-word`);
      var feats = justified ? (part.f && part.f[j]) : v2PlainFeatures(part, j);
      if(feats) span.style.fontFeatureSettings = v2FeatureSettings(feats);
      if(justified && state.row.c && token.indexOf("\u06DD") < 0){
        // dense line: the words (never the aya numbers) are written narrower, as in print;
        // the box keeps its width, the spaces were computed for that
        span.style.display = "inline-block";
        span.style.transform = `scaleX(${state.row.c})`;
        // the line's first and last words narrow from the line's edges, the others about
        // their centre (the build computed the spaces for exactly this)
        var index = state.words - 1;
        if(index === 0) span.style.transformOrigin = "right";
        else if(index === state.row.s.length) span.style.transformOrigin = "left";
      }
      if(onWord) onWord(span, token);
      parent.appendChild(span);
    });
  }
  function v2CleanText(text){
    // Copy/paste: undo the font's encoding (CGJ joiners, decomposed hamza, open tanween) so the
    // clipboard gets standard Uthmani text.
    // Since 2.2.2 the DB drops most CGJs (cursive_fix.py): recompose with or without them.
    return text
      .replace(/ا͏?ٔ͏?/g, "أ").replace(/إ͏?/g, "إ")
      .replace(/و͏?ٔ͏?/g, "ؤ").replace(/ي͏?ٔ͏?/g, "ئ")
      .replace(/͏/g, "")
      .replace(/ࣰ/g, "ً").replace(/ࣱ/g, "ٌ").replace(/ࣲ/g, "ٍ");
  }

  function applyLineStyle(line, stretch){
    // A stretch >= 0 is a scaleX factor filling the line; -1 means center this line instead.
    // stretch_scale (1 unless the font-size is interpolated, see bootInterpolated) corrects the
    // anchor DB's factors: glyph widths grow proportionally with font-size but the fitted
    // line_width does not, so every justified line needs the same small scaleX adjustment.
    if(isV2()) return; // v2 lines are styled once, by v2InitLine
    if(stretch >= 0){
      line.style.setProperty("transform", `scaleX(${stretch * (madina_data.stretch_scale || 1)})`, "");
    } else {
      line.style.setProperty("text-align", "center", "");
    }
  }
  function applyMarkClass(span, counter, highlightRange, errorRange){
    // highlight=/error= mark a word span in addition to (independent of) the words=
    // show/hide handling above. Error wins when the two ranges overlap on a word.
    if(errorRange && counter >= errorRange[0] && counter <= errorRange[1]){
      span.classList.add(`${name}-word-error`);
    } else if(highlightRange && counter >= highlightRange[0] && counter <= highlightRange[1]){
      span.classList.add(`${name}-word-highlight`);
    }
  }
  function appendWords(parent, text, range, counter, highlightRange, errorRange, part, line){
    // Render each whitespace-separated word as its own span so non-selected words can be
    // hidden in place (visibility:hidden) while keeping the original Madina line geometry.
    // `counter` is the running 1-based word index across the whole selection (spans ayas).
    // `range` is optional: null means nothing is hidden (used by the plain render path,
    // which has no words= selection to restrict to - see doRender).
    // v2 DBs pass the `part` and its `line`, so words keep their stretch features and spaces.
    if(isV2() && part && line){
      v2AppendWords(parent, line, part, function(span, token){
        if(isWordToken(token)){ counter = counter + 1; span.setAttribute("data-qmh-w", counter); }
        if(range && (counter < range[0] || counter > range[1])) span.classList.add(`${name}-word-hidden`);
        applyMarkClass(span, counter, highlightRange, errorRange);
      });
      return counter;
    }
    text.split(/(\s+)/).forEach(function(token){
      if(token === "") return;
      if(/^\s+$/.test(token)){ parent.appendChild(document.createTextNode(token)); return; }
      var span = document.createElement("span");
      span.textContent = token;
      span.classList.add(`${name}-word`);
      if(!isWordToken(token)){
        // Marker/pause/ornament: never counted as a word itself, but it attaches to the word it
        // follows (e.g. the aya-end marker is appended to that aya's last word at build time), so
        // show/mark it exactly like that preceding word.
        if(range && (counter < range[0] || counter > range[1])) span.classList.add(`${name}-word-hidden`);
        applyMarkClass(span, counter, highlightRange, errorRange);
      } else {
        counter = counter + 1;
        span.setAttribute("data-qmh-w", counter); // the word number letters= refers to
        if(range && (counter < range[0] || counter > range[1])) span.classList.add(`${name}-word-hidden`);
        applyMarkClass(span, counter, highlightRange, errorRange);
      }
      parent.appendChild(span);
    });
    return counter;
  }
  // --------------------------------------------------------------------------
  // letters= : emphasise single letters inside words (colour + a soft halo behind the ink).
  // Comma-separated groups "word:letters [colour] [blink]", e.g. "1:3, 4:3-5 emerald blink":
  // word number as in words=/highlight=/error=, letter numbers (n, n-m, or n+m+...), optional
  // colour (a palette name below or any CSS colour; crimson when omitted), optional "blink"
  // (the halo pulses; no animation by default). Each letter is wrapped
  // in its own span inside the word span: only colour and shadow change, so the browser shapes
  // the word exactly as before (no re-layout).
  // --------------------------------------------------------------------------
  var LETTER_COLORS = {          // tuned to read on plain, highlight= and error= words
    crimson: "#a3263a", emerald: "#0f6b4f", lapis: "#1f4fb0", gold: "#8a5a00", violet: "#5b2aa8"
  };
  function parseLetters(str){
    // -> [{word, letters: [n...], color, blink}] or null when nothing valid
    if(str == null) return null;
    var out = [];
    String(str).split(",").forEach(function(group){
      var m = group.trim().match(/^(\d+)\s*:\s*([\d+\-\s]*\d)\s*(\S.*)?$/);
      if(!m) return;
      var letters = [];
      m[2].replace(/\s+/g, "").split("+").forEach(function(item){
        var r = item.match(/^(\d+)(?:-(\d+))?$/);
        if(!r) return;
        var from = parseInt(r[1], 10), to = r[2] ? parseInt(r[2], 10) : from;
        for(var n = from; n <= to && n - from < 50; n++){ if(n >= 1) letters.push(n); }
      });
      if(!letters.length) return;
      var rest = m[3] ? m[3].trim().split(/\s+/) : [], blink = false;
      if(rest.length && rest[rest.length - 1].toLowerCase() === "blink"){ blink = true; rest.pop(); }
      var color = rest.length ? rest.join(" ") : null;
      if(color && LETTER_COLORS[color.toLowerCase()]) color = LETTER_COLORS[color.toLowerCase()];
      out.push({word: parseInt(m[1], 10), letters: letters, color: color, blink: blink});
    });
    return out.length ? out : null;
  }
  // Characters that ride on the letter before them: combining marks, Arabic harakat and Quranic
  // annotation marks (not the aya end/rub/sajda signs), the font encoding's CGJ/ZWNJ/ZWJ, tatweel.
  var LETTER_RIDER = /[\u0300-\u036F\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED\u08D3-\u08FF\u200C\u200D\u0640]/;
  function letterStarts(text){
    // Index where each letter begins. A letter is a base character plus everything that rides
    // on it: harakat and other marks, the CGJ/ZWJ joiners of the font encoding, a tatweel.
    var starts = [];
    for(var i = 0; i < text.length; i++){
      var ch = text[i];
      if(!LETTER_RIDER.test(ch)) starts.push(i);
    }
    starts.push(text.length);
    return starts;
  }
  function inkSpan(text){
    // The rest of a lettered word, lifted above the letter so its halo sits behind this ink.
    var sp = document.createElement("span");
    sp.className = `${name}-ink`;
    sp.textContent = text;
    return sp;
  }
  function wrapLetters(word, colors){
    // colors: {letter number: {color: CSS colour or null (default), blink: bool}}
    var text = word.textContent, starts = letterStarts(text), nodes = [], last = 0, any = false;
    Object.keys(colors).map(Number).filter(function(n){ return n < starts.length; })
      .sort(function(a, b){ return a - b; })
      .forEach(function(n){
        if(starts[n - 1] > last) nodes.push(inkSpan(text.slice(last, starts[n - 1])));
        var sp = document.createElement("span");
        sp.className = `${name}-letter`;
        if(colors[n].color) sp.style.setProperty("--qmh-letter", colors[n].color);
        if(colors[n].blink) sp.classList.add(`${name}-letter-blink`);
        sp.textContent = text.slice(starts[n - 1], starts[n]);
        nodes.push(sp);
        last = starts[n];
        any = true;
      });
    if(!any) return false;
    if(last < text.length) nodes.push(inkSpan(text.slice(last)));
    word.textContent = "";
    nodes.forEach(function(nd){ word.appendChild(nd); });
    word.classList.add(`${name}-word-lettered`);
    return true;
  }
  function applyLetters(tag, spec, shift){
    tag.classList.remove(`${name}-lettered`);
    if(!spec) return;
    applyMarkTextScheme(tag); // dark pages get a lighter shade of the letter colour
    var spans = {}, perWord = {};
    tag.querySelectorAll(`.${name}-word[data-qmh-w]`).forEach(function(w){
      spans[w.getAttribute("data-qmh-w")] = w;
    });
    spec.forEach(function(g){             // later groups win on the same letter
      var colors = perWord[g.word] = perWord[g.word] || {};
      g.letters.forEach(function(n){ colors[n] = {color: g.color, blink: g.blink}; });
    });
    var missing = [];
    Object.keys(perWord).forEach(function(k){
      var w = spans[parseInt(k, 10) + (shift || 0)];
      if(!w || !wrapLetters(w, perWord[k])) missing.push(k);
    });
    if(missing.length) print(`letters: no such word/letter for word(s) ${missing.join(", ")}`);
    tag.classList.add(`${name}-lettered`); // lifts the other ink above the letters (see CSS)
  }
  function basmalaRenderMode(counter, basmalaWords, displayRange, highlightRange, errorRange){
    // Decides whether a fully-displayed basmala renders as the single ligature glyph or
    // as its 4 individual word tokens. displayRange is the words= selection (null in the
    // plain render path, which has no selection and always shows the full basmala).
    function fullyIn(rng){ return !rng || (counter + 1 >= rng[0] && counter + basmalaWords <= rng[1]); }
    function partiallyIn(rng){
      return !!rng && !fullyIn(rng) && counter + basmalaWords >= rng[0] && counter + 1 <= rng[1];
    }
    if(isV2()) return {ligature: false}; // v2 fonts draw the basmala line from its 4 words
    if(!fullyIn(displayRange)) return {ligature: false};
    // A highlight/error range that cuts into only some of the basmala's words forces the
    // individual tokens so the partial mark is actually visible.
    if(partiallyIn(highlightRange) || partiallyIn(errorRange)) return {ligature: false};
    var cls = null;
    if(errorRange && fullyIn(errorRange)) cls = "error";
    else if(highlightRange && fullyIn(highlightRange)) cls = "highlight";
    return {ligature: true, cls: cls};
  }
  function partOnLine(aya, line_no){
    // The aya's render part that falls on the given page-line, or null.
    for(var k = 0; k < aya.r.length; k++){ if(aya.r[k].l === line_no) return aya.r[k]; }
    return null;
  }
  function isLineStartPart(sura_idx, aya_idx, line_no){
    // True if this aya's part on line_no is the first (rightmost, RTL) on its page-line — i.e. the
    // previous aya in the same sura does not also sit on that line. This replaces the old `o === 0`
    // sentinel now that the pixel offset is gone from the DB: line starts are derivable structurally
    // because the render walks ayas in order. A sura that begins mid-line is treated as a line start
    // (its preceding text lives in the previous sura), matching the earlier same-sura behavior.
    var ayas = madina_data.suras[sura_idx].ayas;
    if(aya_idx <= 0) return true;
    var prev = ayas[aya_idx - 1];
    if(prev === undefined) return true; // previous aya not loaded (sharded boundary): treat as start
    if(prev.p !== ayas[aya_idx].p) return true;
    return partOnLine(prev, line_no) === null;
  }
  function lineContext(sura_idx, page, line_no, aya_idx, dir){
    // Parts on (page, line_no) that lie outside the selection on one side, in reading order. dir<0
    // walks back from the first selected aya (text preceding it); dir>0 walks forward from the last
    // selected aya (text following it). Rendering these invisibly lets the line's own centering or
    // stretch place the visible text exactly where it sits on the full page.
    var ayas = madina_data.suras[sura_idx].ayas, parts = [];
    for(var a = aya_idx + dir; a >= 0 && a < ayas.length; a += dir){
      if(ayas[a] === undefined) break; // reached a not-yet-loaded aya (sharded boundary)
      if(ayas[a].p != page) break;
      var match = partOnLine(ayas[a], line_no);
      if(match === null) break;
      if(dir < 0){ parts.unshift(match); if(isLineStartPart(sura_idx, a, line_no)) break; } // reached the line's right start
      else { parts.push(match); }
    }
    return parts;
  }
  function appendSpacers(line_el, parts){
    // Render parts as invisible spacers: they hold the line's layout but show nothing and are
    // excluded from copy-to-clipboard. Shared by the verse and words= render paths.
    for(var i = 0; i < parts.length; i++){
      var spacer = document.createElement("div");
      spacer.style.cssText = 'display:inline;visibility:hidden';
      if(isV2()) v2AppendWords(spacer, line_el, parts[i]); // same words + spaces as when visible
      else spacer.textContent = parts[i].t;
      line_el.appendChild(spacer);
    }
  }

  // ==========================================================================
  // Clipboard & translate actions
  // ==========================================================================

  function visibleClone(host){
    // Clone the rendered tag and strip everything that must not be copied: the header chrome,
    // word spans hidden by a words= selection, and the invisible layout spacers. Working on a
    // detached clone lets us read textContent (no layout needed) instead of relying on innerText's
    // browser-specific handling of visibility:hidden.
    var clone = host.cloneNode(true);
    var header = clone.querySelector("quran-madina-html-header");
    if(header) header.parentNode.removeChild(header);
    Array.from(clone.querySelectorAll(`.${name}-word-hidden`)).forEach(function(e){
      e.parentNode.removeChild(e);
    });
    Array.from(clone.querySelectorAll("div,span")).forEach(function(e){
      if(/visibility:\s*hidden/.test(e.getAttribute("style") || "")) e.parentNode.removeChild(e);
    });
    return clone;
  }
  function copyToClipboard(){
    var host = this.parentElement.parentElement;
    var header = host.querySelector("quran-madina-html-header");
    var sura_name;
    if(header){
      sura_name = header.textContent.replace(/\s+/g, " ").trim(); // icons are svg, contribute no text
    } else {
      let sura_index = host.getAttribute("sura");
      sura_name = (sura_index != null) ? madina_data.suras[sura_index - 1].name : "";
    }
    var clone = visibleClone(host);
    var lines = clone.querySelectorAll("quran-madina-html-line");
    var body;
    if(lines.length){
      body = Array.from(lines).map(function(l){ return l.textContent.replace(/\s+/g, " ").trim(); })
                  .filter(function(s){ return s !== ""; }).join(" ");
    } else {
      body = clone.textContent.replace(/\s+/g, " ").trim();
    }
    if(isV2()) body = v2CleanText(body);
    var text = "\u201C" + body + "\u201D" + "\n\n" + sura_name;
    navigator.clipboard.writeText(text);
    alert("\u2398 تم نسخ:\n\n" + text);
  }
  function openTranslate(){
    let host = this.parentElement.parentElement;
    let url;
    if(host.getAttribute("sura") != null && host.getAttribute("aya") != null){
      let sura_index = host.getAttribute("sura");
      let aya_index = host.getAttribute("aya");
      url = `https://quran.com/${sura_index}/${aya_index}`;
    } else {
      let page_index = host.getAttribute("page");
      url = `https://quran.com/page/${page_index}`;
    }
    window.open(url, '_blank');
  }

  // ==========================================================================
  // words= render path (spans pages and suras from a start aya)
  // ==========================================================================

  function collectWordParts(sura_start, aya_start, range){
    // Walk ayas in reading order from (sura_start, aya_start), crossing page AND sura
    // boundaries, grouping parts into visual lines keyed by (page, line), until the end word
    // index is covered. Past the end of An-Nas the walk WRAPS AROUND to Al-Fatiha, matching
    // the flat Tanzil indexing consumers count with modulo the Quran (e.g. quranquiz questions
    // at the very end whose continuation rotates back to the beginning); the ≤500-word cap
    // (and the single-cycle bound below) keeps the wrap finite. The title slot (aya index 0)
    // is only ever entered when the walk crosses into another sura, and stays uncounted
    // decoration (under notitle its name text is hidden at render time, keeping the decorated
    // line — see renderWordsSpan). The basmala slot (index 1) is real Quran text and counts
    // like any other words (4 in current DBs — matching the flat Tanzil word indexing that
    // consumers count against; in pre-0.9 DBs it was the "﷽" ligature, which carries no Arabic
    // letter and so still counts 0 there). The walk enters it both when crossing into another
    // sura and when anchored at a sura's first real aya (internal index 2, see parseAyaRange) —
    // word 1 of an aya-1 anchor is بسم, the same Tanzil indexing as everywhere else. Al-Fatiha
    // is exempt from the anchor rewind AND from basmala counting when wrapped into: its slot 1
    // holds its *title* (its basmala is real aya 1) and titles never count.
    var groups = [];
    var current = null;
    var counted = 0;
    var sura_count = madina_data.suras.length;
    // Anchor at a sura's first real aya ⇒ rewind to its basmala slot (Al-Fatiha exempt).
    var anchor_begin = (aya_start === 2 && sura_start > 0) ? 1 : aya_start;
    for(var si = 0; si < sura_count; si++){
      var s = (sura_start + si) % sura_count; // wraps An-Nas → Al-Fatiha
      var ayas = madina_data.suras[s].ayas;
      var aya_begin = (si === 0) ? anchor_begin : 0;
      var reached = false;
      for(var a = aya_begin; a < ayas.length; a++){
        var countable = isCountableAya(s, a);
        var aya = ayas[a];
        if(aya === undefined) break; // not-yet-loaded aya (sharded boundary): stop collecting
        for(var pi = 0; pi < aya.r.length; pi++){
          var part = aya.r[pi];
          // Blank decoration placeholders (Al-Fatiha's slot 0, At-Tawba's basmala-less slot 1)
          // must not become empty rendered lines.
          if(part.t === "") continue;
          var key = `${aya.p}:${part.l}`;
          if(!current || current.key !== key){
            current = {key: key, stretch: part.s, parts: []};
            groups.push(current);
          }
          current.parts.push({sura: s, ayaIdx: a, part: part, countable: countable});
        }
        if(countable){
          counted = counted + countAyaWords(aya);
          if(counted >= range[1]){ reached = true; break; }
        }
      }
      if(reached) break;
    }
    // Annotate each visual line with the running countable-word index it ends at, then drop the
    // lines that are entirely outside the selection — leading lines before range[0] and trailing
    // lines after range[1] (the latter appear because collection grabs whole ayas, which may run
    // onto further lines). The block then begins and ends on lines that actually show a selected
    // word (requirement: no fully-hidden lines). Words on dropped leading lines are carried over as
    // `counterStart` so word visibility downstream still lines up.
    var running = 0;
    groups.forEach(function(g){
      g.parts.forEach(function(item){ if(item.countable){ running = running + countPartWords(item.part); } });
      g.lastWord = running;
    });
    var start = 0;
    while(start < groups.length - 1 && groups[start].lastWord < range[0]) start = start + 1;
    var end = start;
    while(end < groups.length - 1 && groups[end].lastWord < range[1]) end = end + 1;
    return {groups: groups.slice(start, end + 1), counterStart: start > 0 ? groups[start - 1].lastWord : 0};
  }
  function renderWordsSpan(tag, sura_start, aya_start, range, headless, noQuotes, inlineOpt, notitle,
                            highlight_range, error_range){
    // Dedicated render path for the words= selection. Unlike the page/aya loop it is not bound
    // to a single page or sura, so a word range can span both.
    if(highlight_range || error_range) applyMarkTextScheme(tag);
    var collected = collectWordParts(sura_start, aya_start, range);
    var groups = collected.groups;
    var multiline = applyInlineOverride(inlineOpt, groups.length > 1);
    var counter = collected.counterStart; // running 1-based word index, seeded past any skipped lines
    closeAyaPopup(); // the body-level popup outlives tag.innerHTML="", so re-renders must close it
    tag.innerHTML = "";
    tag.removeAttribute('style');
    // Inline (single-line) renders get quote marks around the verse instead of any chrome (see the
    // -inline CSS rule) - it's their only visual cue that this is a quoted excerpt, now that they
    // have no header and no lone copy button (removed; the per-aya click popup covers them too).
    // quotes="no" opts out of this.
    tag.classList.toggle(`${name}-inline`, !multiline && !noQuotes);
    if(multiline){
      let start_page = parseInt(groups[0].key.split(':')[0], 10); // page of the first visible line
      styleMultilineTag(tag, start_page, headless);
      if(!headless){
        tag.appendChild(buildHeader(madina_data.suras[groups[0].parts[0].sura]));
      }
    }
    groups.forEach(function(group, gi){
      var line = document.createElement("quran-madina-html-line");
      if(multiline){
        line.style.setProperty('display', 'block', '');
        if(isV2()){
          var key = group.key.split(':');
          v2InitLine(line, parseInt(key[0], 10), parseInt(key[1], 10));
        }
        applyLineStyle(line, group.stretch);
        var first = group.parts[0];
        if(!isLineStartPart(first.sura, first.ayaIdx, first.part.l)){
          // This line begins mid-line — its first word is preceded on the page by text from ayas
          // before the selection start. Rebuild that preceding text invisibly so the line's own
          // centering/stretch positions the first visible word exactly as on the page. (Only the
          // leading line can be mid-line; every later group enters a line at its right start.)
          appendSpacers(line, lineContext(first.sura,
            madina_data.suras[first.sura].ayas[first.ayaIdx].p, first.part.l, first.ayaIdx, -1));
        }
      } else {
        line.style.setProperty('font-family', madina_data.font_family, '');
        line.style.setProperty('font-size', madina_data.font_size+"px", '');
      }
      tag.appendChild(line);
      group.parts.forEach(function(item){
        var aya_part = document.createElement("div");
        var classes = getAyaClass(item.sura+1, item.ayaIdx-1);
        DOMTokenList.prototype.add.apply(aya_part.classList, classes);
        if(item.countable){
          var basmalaWords = isBasmalaSlot(item.sura, item.ayaIdx) ? countPartWords(item.part) : 0;
          var mode = (basmalaWords > 0) ?
            basmalaRenderMode(counter, basmalaWords, range, highlight_range, error_range) : {ligature: false};
          if(mode.ligature){
            // The whole basmala falls inside the selection (and no highlight/error cuts into
            // only part of it): render the traditional ligature instead of its individual
            // tokens (it still advances the word counter by all 4 words, so following word
            // indices are unchanged).
            var lig = document.createElement("span");
            lig.classList.add(`${name}-word`, `${name}-basmala`);
            if(mode.cls) lig.classList.add(`${name}-word-${mode.cls}`);
            lig.textContent = BASMALA_LIGATURE;
            aya_part.appendChild(lig);
            counter = counter + basmalaWords;
          } else {
            // A partial words= overlap, or a highlight/error range cutting into only some of
            // the basmala's words, falls through to appendWords so the right words show/mark.
            counter = appendWords(aya_part, item.part.t, range, counter, highlight_range, error_range,
                                  item.part, line);
          }
        } else if(notitle && (item.ayaIdx === 0 || (item.sura === 0 && item.ayaIdx === 1))){
          // notitle: keep the title's line and its decorative frame (the sura_border SVG is
          // painted on the line via :has(.quran-madina-html-sura-start), so the div and its
          // class must stay) but hide the name text itself. visibility:hidden preserves the
          // line's height/centering and excludes the name from copy (visibleClone strips it).
          // The sura===0 arm: Al-Fatiha keeps its title at slot 1 (reached when a words= walk
          // wraps around from An-Nas), where every other sura keeps its basmala.
          var hiddenName = document.createElement("span");
          hiddenName.textContent = item.part.t;
          hiddenName.style.visibility = "hidden";
          aya_part.appendChild(hiddenName);
        } else {
          aya_part.textContent = item.part.t; // sura title: always visible
        }
        aya_part.style.cssText = 'display:inline';
        line.appendChild(aya_part);
        hoverByType(classes.slice(-1)[0]);
        wireAyaClick(tag, classes.slice(-1)[0], item.sura+1, item.ayaIdx-1);
      });
      if(multiline && gi === groups.length - 1){
        // The selection ends mid-line: rebuild the following text invisibly to keep the last line
        // laid out (and centered) exactly as on the page.
        var last = group.parts[group.parts.length - 1];
        appendSpacers(line, lineContext(last.sura,
          madina_data.suras[last.sura].ayas[last.ayaIdx].p, last.part.l, last.ayaIdx, 1));
      }
    });
  }

  // ==========================================================================
  // Boot configuration (read from the loader <script> tag)
  // ==========================================================================

  var DEFAULT_FONT_SIZE = 16;
  // Every font ships a pre-built DB at exactly these sizes (see src/db/build_all.py). Any other
  // requested size gets no DB of its own: it is served by interpolating between the two anchors
  // (see bootInterpolated below), so data-font-size accepts any value in FONT_SIZE_RANGE.
  var ANCHOR_SIZES = [16, 24];
  var FONT_SIZE_RANGE = [6, 100];
  var this_script = document.currentScript || document.querySelector(`script[src*="${name}"]`);
  var doc_name    = this_script.getAttribute('data-name') || "Madina05";
  var doc_font    = (this_script.getAttribute('data-font') || "me_quran").replaceAll(" ","_");
  var doc_font_sz = parseFloat(this_script.getAttribute('data-font-size')) || DEFAULT_FONT_SIZE;
  if(doc_font_sz < FONT_SIZE_RANGE[0] || doc_font_sz > FONT_SIZE_RANGE[1]){
    print(`font-size ${doc_font_sz} outside ${FONT_SIZE_RANGE[0]}..${FONT_SIZE_RANGE[1]}, using ${DEFAULT_FONT_SIZE}`);
    doc_font_sz = DEFAULT_FONT_SIZE;
  }
  // Since 2.0 every tag renders a v2 layout: data-layout="1441H" (default) | "1405H" | "IndoPak"
  // loads assets/db/v2/<stem>.json, whose lines are justified by stretching letters. The v1
  // attributes data-font / data-name are ignored (a drop-in upgrade: no page needs editing).
  var doc_layout  = this_script.getAttribute('data-layout') || "1441H";
  var use_v2      = true;
  ['data-font', 'data-name'].forEach(function(attr){
    if(this_script.hasAttribute(attr)){
      console.warn(`${name}> ${attr} is ignored since 2.0: every tag uses the v2 fonts ` +
                   `(choose a layout with data-layout="1441H" | "1405H" | "IndoPak")`);
    }
  });
  // v2 layouts and their DB names (assets/db/v2/<stem>.json and <stem>/ shards)
  var V2_STEMS = {"1441H": "Madina-1441H", "1405H": "Madina-1405H", "indopak": "IndoPak-15"};
  if(V2_STEMS[doc_layout] === undefined){
    if(V2_STEMS[String(doc_layout).toLowerCase()] !== undefined){
      doc_layout = String(doc_layout).toLowerCase();
    } else {
      console.warn(`${name}> unknown data-layout "${doc_layout}", using 1441H`);
      doc_layout = "1441H";
    }
  }
  var doc_cdn     = this_script.getAttribute('data-cdn');
  if (doc_cdn){
    var safe_cdn = safeBaseUrl(doc_cdn);
    if (safe_cdn) cdn = safe_cdn;
    else console.warn(`${name}> data-cdn "${doc_cdn}" is not a URL the library can load from; using ${cdn}`);
  }
  print(`layout: ${doc_layout} size: ${doc_font_sz}`);
  const name_css = new URL("dist/" + name + ".css?v=1.1", new URL(cdn, document.baseURI)).href;
  if (!document.getElementById(name))
  {
      var head  = document.getElementsByTagName('head')[0];
      var link  = document.createElement('link');
      link.id   = name;
      link.rel  = 'stylesheet';
      link.type = 'text/css';
      link.href = name_css;
      link.media = 'all';
      head.appendChild(link);
  }

  // ==========================================================================
  // Sharded DB loading
  // ==========================================================================

  // DB loading is sharded by default: a small manifest.json (header + sura skeleton + juz'/page
  // maps) loads first, then each juz' data shard is fetched on demand as pages/ranges render.
  // Falls back to the single monolithic <stem>.json when no manifest is present. `dbstem`/`shardBase`
  // are recomputed (not const) so a font-size with no DB built for it can fall back to the default
  // size's DB — see the boot sequence below.
  var dbstem, shardBase;
  function setFontSize(sz){
    doc_font_sz = sz;
    dbstem = `${doc_name}-${doc_font}-${doc_font_sz}px`;
    shardBase = `${cdn}assets/db/${dbstem}/`;
  }
  setFontSize(doc_font_sz);
  // Set by bootInterpolated for a non-anchor font-size: the DB loaded is the nearest anchor's,
  // and these header overrides re-target it to the requested size. Applied by both boot paths
  // right before initTag, and null for anchor sizes (the DB is then used as-is).
  var sizeOverrides = null; // {font_size, line_width, stretch_scale}
  function applySizeOverrides(){
    if(!sizeOverrides) return;
    madina_data.font_size = sizeOverrides.font_size;
    madina_data.line_width = sizeOverrides.line_width;
    madina_data.stretch_scale = sizeOverrides.stretch_scale;
  }
  var loadedJuz = {}; // juz' index (0..29) -> true once its shard is merged into madina_data
  function suraAyaToJuz(sura0, aya_idx){
    // Last juz' whose (startSura, startAya) <= (sura0, aya). Decoration slots (idx 0/1) use aya 1's
    // position so a sura that opens a juz' keeps its title/basmala in the new juz'.
    if(!madina_data.juz) return -1;
    var pa = Math.max(aya_idx, 2), j = 0, J = madina_data.juz;
    for(var k = 0; k < J.length; k++){
      if(J[k][0] < sura0 || (J[k][0] === sura0 && J[k][1] <= pa)) j = k; else break;
    }
    return j;
  }
  function mergeShard(shard){
    // shard.d = [[suraIdx, ayaIdx, page, parts], ...] -> fill the sparse skeleton in place.
    for(var i = 0; i < shard.d.length; i++){
      var e = shard.d[i];
      madina_data.suras[e[0]].ayas[e[1]] = {p: e[2], r: e[3]};
    }
    // v2: shard.L = {page: rows} - the line geometry of the pages its ayas sit on
    if(shard.L && madina_data.lines){
      for(var page in shard.L){
        if(Object.prototype.hasOwnProperty.call(shard.L, page)) madina_data.lines[page - 1] = shard.L[page];
      }
    }
  }
  function ensureJuz(list, cb){
    // Fetch+merge any not-yet-loaded juz' shards in `list`, then call cb. Monolith mode: no-op.
    if(!madina_data.juz){ cb(); return; }
    var need = [];
    for(var i = 0; i < list.length; i++){
      var j = list[i];
      if(j >= 0 && j < madina_data.juz.length && !loadedJuz[j] && need.indexOf(j) < 0) need.push(j);
    }
    if(need.length === 0){ cb(); return; }
    var remaining = need.length;
    need.forEach(function(j){
      loadJSON(shardBase + "juz-" + pad2(j + 1) + ".json",
        function(shard){ mergeShard(shard); loadedJuz[j] = true; if(--remaining === 0) cb(); },
        function(xhr){ console.error(`${name}> failed to load juz ${j + 1}`, xhr);
                       loadedJuz[j] = true; if(--remaining === 0) cb(); });
    });
  }
  function neededJuz(el){
    // Which juz' shards a pending render will read, derived from its attributes. Monolith: none.
    if(!madina_data.juz) return [];
    var out = [], k;
    if(el.getAttribute("sura") != null && el.getAttribute("aya") != null){
      var sura0 = parseSuraRange(el.getAttribute("sura"))[0];
      var ar = parseAyaRange(el.getAttribute("aya")); // [from,to] internal indices
      if(el.getAttribute("words") != null){
        // words spill forward < one juz'; from the last juz' they wrap around to Al-Fatiha's
        // (see collectWordParts), so the successor juz' is taken modulo the juz' count.
        var j = suraAyaToJuz(sura0, ar[0]);
        return [j, (j + 1) % madina_data.juz.length];
      }
      for(k = suraAyaToJuz(sura0, ar[0]); k <= suraAyaToJuz(sura0, ar[1]); k++) out.push(k);
      return out;
    }
    if(el.getAttribute("page") != null){
      var pb = madina_data.pages[parseInt(el.getAttribute("page"), 10) - 1];
      if(!pb) return [];
      for(k = suraAyaToJuz(pb[0], pb[1]); k <= suraAyaToJuz(pb[2], pb[3]); k++) out.push(k);
      return out;
    }
    return [];
  }

  // ==========================================================================
  // Custom-element registration & the render loop
  // ==========================================================================

  function initTag(){
    const myFont = new FontFace(madina_data.font_family, 'url('+encodeURI(resolveUrl(madina_data.font_url))+')');
    myFont.load().then( () => {document.fonts.add(myFont);});

    class QuranMadinaHtml extends HTMLElement {
      static get observedAttributes() {
        return [
          "page", "page_param", "aya", "sura", "words", "highlight", "error", "headless", "quotes",
          "inline", "notitle", "letters", "actions"
        ];
      }

      // Verse actions (see the "Verse actions" section): page-wide, for every tag.
      static registerAction(spec) {
        var action = checkAction(spec);
        ayaActions = ayaActions.filter(function(a){ return a.id !== action.id; });
        ayaActions.push(action);
        actionsChanged();
        return action.id;
      }
      static unregisterAction(id) {
        var before = ayaActions.length;
        ayaActions = ayaActions.filter(function(a){ return a.id !== id; });
        actionsChanged();
        return ayaActions.length < before;
      }
      static clearActions() { ayaActions = []; actionsChanged(); }
      static resetActions() { ayaActions = DEFAULT_ACTIONS.slice(); actionsChanged(); }
      static get actions() {
        return ayaActions.map(function(a){ return {id: a.id, title: a.title, order: a.order}; });
      }

      constructor() {
        super();
        this._data = {}; // render bookkeeping (the re-entry guard)
      }

      connectedCallback() {
        this.render();
      }

      attributeChangedCallback() {
        // A tag not yet in the page renders once it's inserted (connectedCallback). Frameworks
        // set attributes one by one before inserting it; rendering each step would log
        // "Bad arguments" for the half-set ones.
        if (this.isConnected) this.render();
      }

      get page() { return this.getAttribute("page"); }
      set page(value) { reflectAttribute(this, "page", value); }

      get page_param() { return this.getAttribute("page_param"); }
      set page_param(value) { reflectAttribute(this, "page_param", value); }

      get aya() { return this.getAttribute("aya"); }
      set aya(value) { reflectAttribute(this, "aya", value); }

      get sura() { return this.getAttribute("sura"); }
      set sura(value) { reflectAttribute(this, "sura", value); }

      get words() { return this.getAttribute("words"); }
      set words(value) { reflectAttribute(this, "words", value); }

      get highlight() { return this.getAttribute("highlight"); }
      set highlight(value) { reflectAttribute(this, "highlight", value); }

      get error() { return this.getAttribute("error"); }
      set error(value) { reflectAttribute(this, "error", value); }

      get letters() { return this.getAttribute("letters"); }
      set letters(value) { reflectAttribute(this, "letters", value); }

      get headless() { return this.getAttribute("headless"); }
      set headless(value) { reflectAttribute(this, "headless", value); }

      get quotes() { return this.getAttribute("quotes"); }
      set quotes(value) { reflectAttribute(this, "quotes", value); }

      get inline() { return this.getAttribute("inline"); }
      set inline(value) { reflectAttribute(this, "inline", value); }

      get notitle() { return this.getAttribute("notitle"); }
      set notitle(value) { reflectAttribute(this, "notitle", value); }

      get actions() { return this.getAttribute("actions"); }
      set actions(value) {
        reflectAttribute(this, "actions", Array.isArray(value) ? (value.length ? value.join(" ") : "none") : value);
      }

      render(tag = this) {
        // Re-entrancy guard. Kept from the pre-native-Custom-Elements version, where the platform
        // watched every attribute mutation (including the `style`/class churn this build performs
        // mid-render) and could re-enter render() before the current build finished. observedAttributes
        // now scopes attributeChangedCallback to just the public attrs, so that particular re-entrancy
        // source is gone - but the guard stays cheap insurance against any other overlapping render call.
        if(this._data.rendering){ return; }
        var self = this;
        // Sharded DB: ensure the juz' shard(s) this render will read are loaded, then render
        // synchronously. Monolith mode: ensureJuz invokes the callback immediately.
        ensureJuz(neededJuz(this), function(){
          if(self._data.rendering){ return; }
          self._data.rendering = true;
          try {
            tag._qmhLetterShift = 0;
            var letters = parseLetters(self.letters);
            if(self.letters != null && letters == null) print(`Bad letters parameter: ${self.letters}`);
            tag._qmhLetters = letters;
            self.doRender(tag);
            applyLetters(tag, letters, tag._qmhLetterShift);
            updateInteractive(tag);
          } finally {
            self._data.rendering = false;
          }
        });
      }

      doRender(tag){
        var sura_from, sura_to, aya_from, aya_to, line_from, line_to;
        var multiline;
        var words_range = null;
        // highlight=/error= use the same 1-based range format as words= (parseWordsRange),
        // and are validated below against whatever ends up being displayed - the words=
        // selection if present, otherwise the full verse/page (see clampedOrNull calls).
        var highlight_range = (this.highlight != null) ? parseWordsRange(this.highlight) : null;
        if(this.highlight != null && highlight_range == null){
          print(`Bad highlight parameter: ${this.highlight}`);
        }
        var error_range = (this.error != null) ? parseWordsRange(this.error) : null;
        if(this.error != null && error_range == null){
          print(`Bad error parameter: ${this.error}`);
        }
        // `page` is the page to render, derived locally. We deliberately never write derived
        // state (sura/aya/page) back onto the element: those are attribute-backed accessors,
        // and writing them re-triggers render(), which used to cascade and duplicate output.
        var page = this.page;
        var headless = isTrue(this.headless); // hide header (multiline) / copy button (inline)
        // notitle: when a words= walk crosses into a new sura, keep the title's decorated
        // line but hide the sura name text. Only wired into the words= path — the ordinary
        // page/aya render reproduces the printed page, so it deliberately ignores this
        // attribute; revisit if a consumer needs it there.
        var notitle = isTrue(this.notitle);
        // quotes="no" (or "false") opts out of the inline quote marks; absent/anything else
        // keeps the default (shown).
        var noQuotes = this.quotes != null && !isTrue(this.quotes);
        var inlineOpt = this.inline; // "no" | "auto" (default) | "yes" (not implemented yet)
        var verse_mode = (this.sura != null && this.aya != null);
        if(verse_mode){
          sura_from = parseSuraRange(this.sura)[0];
          sura_to = sura_from;
          multiline = false;
          [aya_from,aya_to] = parseAyaRange(this.aya);
          if(this.page != null) print("Ignoring page parameter!");
          page = madina_data.suras[sura_from].ayas[aya_from].p;
        } else if(this.page != null){
          if(madina_data.pages){ // sharded: page -> [sura_from,aya_from,sura_to,aya_to]
            var pb = madina_data.pages[page - 1];
            sura_from = pb[0]; aya_from = pb[1]; sura_to = pb[2]; aya_to = pb[3];
          } else { // monolith: derive by scanning aya pages
            sura_from = 0; sura_to = 0; aya_from=0; aya_to=0;
            while(madina_data.suras[sura_from].ayas.slice(-1)[0].p < page) sura_from = sura_from + 1;
            sura_to = sura_from;
            while(sura_to < 114 && madina_data.suras[sura_to].ayas[0].p <= page) sura_to = sura_to + 1;
            sura_to = sura_to -1;
            while(madina_data.suras[sura_from].ayas[aya_from].p < page) aya_from = aya_from + 1;
            aya_to = madina_data.suras[sura_to].ayas.length-1;
            while (madina_data.suras[sura_to].ayas[aya_to].p > page) aya_to = aya_to - 1;
          }
          multiline = true;
          if(this.inline != null) print("Ignoring inline parameter with page!");
        } else{
          console.error(`${name}> Bad arguments: Not rendering!`);
          return 1;
        }
        if(this.words != null){
          if(!verse_mode){
            print("Ignoring words parameter with page!");
          } else {
            words_range = parseWordsRange(this.words);
            if(words_range == null){
              print(`Bad words parameter: ${this.words}`);
            } else {
              if(aya_to !== aya_from) print("Ignoring aya range end with words parameter!");
              if(words_range[1] - words_range[0] + 1 > 500){
                print("words selection capped at 500 words");
                words_range[1] = words_range[0] + 499;
              }
              highlight_range = clampedOrNull("highlight", highlight_range, words_range);
              error_range = clampedOrNull("error", error_range, words_range);
              // words= has its own renderer that spans pages and suras from the start aya.
              renderWordsSpan(tag, sura_from, aya_from, words_range, headless, noQuotes,
                              inlineOpt, notitle, highlight_range, error_range);
              return;
            }
          }
        }
        if(verse_mode && ayaLastPage(madina_data.suras[sura_to].ayas[aya_to]) != page){
          // The ayas run onto the next page(s). The line loop below draws one page, so this
          // goes through the words= renderer, which follows (page, line) across pages: every
          // word of the range selected. A walk anchored at a sura's first aya also counts its
          // basmala (collectWordParts), so the selection starts after those words.
          var skip = (aya_from === 2 && sura_from > 0) ?
            countAyaWords(madina_data.suras[sura_from].ayas[1]) : 0;
          var total = countVerseRangeWords(sura_from, aya_from, aya_to);
          var shift = function(r){ return r == null ? null : [r[0] + skip, r[1] + skip]; };
          tag._qmhLetterShift = skip;
          highlight_range = shift(clampedOrNull("highlight", highlight_range, [1, total]));
          error_range = shift(clampedOrNull("error", error_range, [1, total]));
          renderWordsSpan(tag, sura_from, aya_from, [skip + 1, skip + total], headless, noQuotes,
                          inlineOpt, false, highlight_range, error_range);
          return;
        }
        // No words= selection (absent, ignored with page=, or malformed and falling back
        // here): highlight=/error= are validated against the full verse/page instead, with
        // word 1 = first word of aya_from (verse mode) or of the page's first aya (page
        // mode never starts mid-aya, so this is always well-defined).
        var display_total = verse_mode ? countVerseRangeWords(sura_from, aya_from, aya_to)
          : countPageWords(sura_from, aya_from, sura_to, aya_to, parseInt(page, 10));
        highlight_range = clampedOrNull("highlight", highlight_range, [1, display_total]);
        error_range = clampedOrNull("error", error_range, [1, display_total]);
        // letters= needs numbered word spans too, so it takes the same word-by-word path
        var wordMarkMode = (highlight_range != null || error_range != null || tag._qmhLetters != null);
        if(wordMarkMode) applyMarkTextScheme(tag);
        closeAyaPopup(); // the body-level popup outlives tag.innerHTML="", close on re-render
        tag.innerHTML = ""; //Remove all pre-existing elements
        tag.removeAttribute('style'); // and styles.
        line_from = madina_data.suras[sura_from].ayas[aya_from].r[0].l;
        line_to = madina_data.suras[sura_to].ayas[aya_to].r.slice(-1)[0].l;
        if(line_from != line_to) multiline = true;
        multiline = applyInlineOverride(inlineOpt, multiline);
        // Inline (single-line) renders get quote marks around the verse instead of any chrome
        // (see the -inline CSS rule) - their only visual cue that this is a quoted excerpt,
        // now that they have no header and no lone copy button (removed; the per-aya click
        // popup covers them too). quotes="no" opts out of this.
        tag.classList.toggle(`${name}-inline`, !multiline && !noQuotes);
        if(multiline){
          styleMultilineTag(tag, page, headless);
          if(!headless){
            tag.appendChild(buildHeader(madina_data.suras[sura_from]));
          }
        }
        /** Loop on Ayas, lines, parts */
        var aya_current = aya_from;
        var sura_current = sura_from;
        var word_counter = 0; // only advanced/used when wordMarkMode is true
        for(let l = line_from; l <= line_to; l++) {
          const ll = l; //Const for inner loops to refer
          let line = document.createElement("quran-madina-html-line");
          tag.appendChild(line);
          if(multiline){
            line.style.setProperty('display','block','');
            if(isV2()) v2InitLine(line, parseInt(page, 10), l);
          } else {
            line.style.setProperty('font-family', madina_data.font_family, '');
            line.style.setProperty('font-size', madina_data.font_size+"px", '');
          }
          if(multiline && verse_mode && l === line_from){
            appendSpacers(line, lineContext(sura_from, page, line_from, aya_from, -1));
          }
          let look_ahead = (sura_from == sura_to)? aya_to: madina_data.suras[sura_current].ayas.length-1;
          for(let a = aya_current; a <= Math.min(aya_current+5, look_ahead) ; a++) {
            // Sharded DB: the +5 look-ahead (and the sura-jump peek below) can probe an aya
            // that belongs to a not-yet-loaded juz' — but any such aya is necessarily off
            // this page (every on-page aya lives in a loaded shard), so treat undefined as
            // "not on this page". In monolith mode all ayas are present, so these guards are
            // inert.
            let aya_a = madina_data.suras[sura_current].ayas[a];
            if(aya_a !== undefined && aya_a.p == page){
              let line_match = aya_a.r.filter(rr => rr.l == ll);
              if (line_match.length){
                if(multiline){
                  applyLineStyle(line, line_match[0].s);
                }
                let aya_part = document.createElement("div");
                let classes = getAyaClass(sura_current+1, a-1);
                DOMTokenList.prototype.add.apply(aya_part.classList, classes);
                if(wordMarkMode && isCountableAya(sura_current, a)){
                  // highlight=/error= is set: break this (countable) part into word spans
                  // instead of the plain text/ligature blob below, so individual words can
                  // be marked. Title parts (never countable) always keep the plain path -
                  // they're never selectable/markable, same as in the words= render path.
                  let basmalaWords = isBasmalaSlot(sura_current, a) ? countPartWords(line_match[0]) : 0;
                  let mode = (basmalaWords > 0) ?
                    basmalaRenderMode(word_counter, basmalaWords, null, highlight_range, error_range) :
                    {ligature: false};
                  if(mode.ligature){
                    let lig = document.createElement("span");
                    lig.classList.add(`${name}-word`, `${name}-basmala`);
                    if(mode.cls) lig.classList.add(`${name}-word-${mode.cls}`);
                    lig.textContent = BASMALA_LIGATURE;
                    aya_part.appendChild(lig);
                    word_counter = word_counter + basmalaWords;
                  } else {
                    word_counter = appendWords(aya_part, line_match[0].t, null, word_counter,
                                                highlight_range, error_range, line_match[0], line);
                  }
                } else if(isV2() && isCountableAya(sura_current, a)){
                  // v2: words keep their stretch features and the line its exact spaces.
                  v2AppendWords(aya_part, line, line_match[0]);
                } else {
                  // A page render always shows the complete basmala line, so it gets the
                  // traditional ligature instead of the DB's 4 word tokens (blank slots,
                  // e.g. At-Tawba's, stay blank).
                  aya_part.textContent = (!isV2() && isBasmalaSlot(sura_current, a) &&
                    line_match[0].t !== "") ? BASMALA_LIGATURE : line_match[0].t;
                }
                aya_part.style.cssText = 'display:inline';
                line.appendChild(aya_part);
                hoverByType(classes.slice(-1)[0]);
                wireAyaClick(tag, classes.slice(-1)[0], sura_current+1, a-1);
                aya_current = a;
                let next_sura_aya0 = (sura_current < 113) ?
                  madina_data.suras[sura_current+1].ayas[0] : undefined;
                if(aya_current >= look_ahead &&
                  next_sura_aya0 !== undefined &&
                  next_sura_aya0.p == page &&
                  next_sura_aya0.r[0].l == ll+1) {
                  //Jump to next Sura
                  sura_current = sura_current + 1;
                  aya_current = 0;
                }
              }
            }
          }
          if(multiline && verse_mode && l === line_to){
            appendSpacers(line, lineContext(sura_to, page, line_to, aya_to, 1));
          }
        }
      }
    }

    customElements.define(name, QuranMadinaHtml);
  }

  // ==========================================================================
  // Boot: an anchor font-size (16/24) loads its own DB - sharded manifest preferred, monolithic
  // fallback. Any other size boots through bootInterpolated (both anchors' headers -> interpolated
  // line_width + stretch_scale over the nearest anchor's DB). Last resort stays the default
  // size's DB if no DB was ever built for the requested/anchor size.
  // ==========================================================================

  function bootFromManifest(){
    // forceFresh: the manifest itself never changes when only render data (stretch factors, text)
    // is fixed/rebuilt - only its content_hash does, since that's hashed over the whole DB. Always
    // fetching it fresh (it's small) is what lets that comparison run on every load, so a stale
    // juz shard cached from before a DB update gets purged instead of served for the rest of the
    // browser session.
    loadJSON(shardBase + "manifest.json",
      function(m){
        if(m.content_hash){
          var hashKey = "quran-madina-html:hash:" + shardBase;
          var prevHash = null;
          try { prevHash = sessionStorage.getItem(hashKey); } catch(e) { /* ignore */ }
          if(prevHash !== null && prevHash !== m.content_hash) clearShardCache(shardBase);
          try { sessionStorage.setItem(hashKey, m.content_hash); } catch(e) { /* ignore */ }
        }
        madina_data = {
          title: m.title, published: m.published, font_family: m.font_family, font_url: m.font_url,
          font_size: m.font_size, line_width: m.line_width,
          suras: m.suras.map(function(e){ return {name: e[0], ayas: new Array(e[1]), nf: e[2]}; }),
          juz: m.juz, pages: m.pages
        };
        applySizeOverrides();
        initTag();
      },
      bootMonolith,
      true
    );
  }
  function bootMonolith(){
    loadJSON(`${cdn}assets/db/${dbstem}.json`,
      function(data){ madina_data = data; applySizeOverrides(); initTag(); },
      function(xhr){
        if(doc_font_sz != DEFAULT_FONT_SIZE){
          print(`no DB for font: ${doc_font} size: ${doc_font_sz}, falling back to size: ${DEFAULT_FONT_SIZE}`);
          sizeOverrides = null; // any pending overrides were fitted to the size that just failed
          setFontSize(DEFAULT_FONT_SIZE);
          bootFromManifest();
        } else {
          console.error(`${name}> no manifest and no monolithic DB`, xhr);
        }
      });
  }
  function dbHeader(size, success, error){
    // Header fields (line_width in particular) of one anchor size's DB: the small sharded
    // manifest when available, else the monolithic DB (large, but it lands in the same JSON
    // cache the render will read from anyway).
    var stem = `${doc_name}-${doc_font}-${size}px`;
    loadJSON(`${cdn}assets/db/${stem}/manifest.json`, success,
             function(){ loadJSON(`${cdn}assets/db/${stem}.json`, success, error); });
  }
  function bootInterpolated(){
    // The requested font-size has no pre-built DB. The per-size line_widths are hand-tuned, NOT
    // proportional to the size (e.g. Hafs is 270px@16 but 410px@24, where proportional would be
    // 405), so the width for size S is read off the line fitted through the two anchor points.
    // Render data (text incl. build-inserted kashidas, stretch factors) comes from the nearest
    // anchor's DB, whose scaleX factors are corrected by a single stretch_scale: glyph widths DO
    // grow proportionally with font-size while the fitted line_width does not, so
    //   natural width at S  = natural(anchor) * S/anchor
    //   needed stretch at S = lw(S)/natural(S) = stored_stretch * lw(S)*anchor / (lw(anchor)*S)
    var S = doc_font_sz, lo = ANCHOR_SIZES[0], hi = ANCHOR_SIZES[1];
    var nearest = (S - lo <= hi - S) ? lo : hi;
    var headers = {}, failed = false;
    var fail = function(xhr){
      if(failed) return; // both anchors missing: only the first error boots the fallback
      failed = true;
      console.error(`${name}> missing anchor DB for font-size interpolation`, xhr);
      print(`falling back to size: ${DEFAULT_FONT_SIZE}`);
      setFontSize(DEFAULT_FONT_SIZE);
      bootFromManifest();
    };
    var done = function(){
      if(failed || !(lo in headers) || !(hi in headers)) return;
      var lw = Math.round(headers[lo].line_width +
        (headers[hi].line_width - headers[lo].line_width) * (S - lo) / (hi - lo));
      sizeOverrides = {
        font_size: S,
        line_width: lw,
        stretch_scale: (lw * nearest) / (headers[nearest].line_width * S)
      };
      print(`font-size ${S}px interpolated from ${lo}px/${hi}px anchors: line_width ${lw}, render data from ${nearest}px`);
      setFontSize(nearest);
      bootFromManifest();
    };
    ANCHOR_SIZES.forEach(function(sz){
      dbHeader(sz, function(h){ headers[sz] = h; done(); }, fail);
    });
  }
  function bootV2(){
    // v2 DBs size everything in em: one DB serves every font-size, no anchors/interpolation.
    // Sharded like v1 (manifest + juz' shards carrying their pages' line rows), monolith fallback.
    var stem = V2_STEMS[doc_layout] || `Madina-${doc_layout}`;
    var ready = function(){
      madina_data.font_size = doc_font_sz;
      madina_data.line_width_em = madina_data.line_width;
      madina_data.line_width = madina_data.line_width * doc_font_sz; // px, for the tag's width
      initTag();
    };
    var monolith = function(){
      shardBase = null;
      loadJSON(`${cdn}assets/db/v2/${stem}.json`,
        function(data){ madina_data = data; ready(); },
        function(xhr){ console.error(`${name}> no v2 DB for layout ${doc_layout}`, xhr); });
    };
    shardBase = `${cdn}assets/db/v2/${stem}/`;
    loadJSON(shardBase + "manifest.json",
      function(m){
        if(m.content_hash){
          var hashKey = "quran-madina-html:hash:" + shardBase;
          var prevHash = null;
          try { prevHash = sessionStorage.getItem(hashKey); } catch(e) { /* ignore */ }
          if(prevHash !== null && prevHash !== m.content_hash) clearShardCache(shardBase);
          try { sessionStorage.setItem(hashKey, m.content_hash); } catch(e) { /* ignore */ }
        }
        madina_data = {};
        Object.keys(m).forEach(function(k){
          if(k !== "suras" && k !== "n_pages") madina_data[k] = m[k];
        });
        madina_data.suras = m.suras.map(function(e){ return {name: e[0], ayas: new Array(e[1]), nf: e[2]}; });
        madina_data.lines = new Array(m.n_pages);
        ready();
      },
      monolith,
      true
    );
  }
  if(use_v2){ bootV2(); }
  else if(ANCHOR_SIZES.indexOf(doc_font_sz) >= 0){ bootFromManifest(); } else { bootInterpolated(); }

})();
