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
  function loadJSON(path, success, error, forceFresh){
    // forceFresh (used for manifest.json only): skip the cache read and always hit the network.
    // The manifest is small, so this costs nothing, and it's what lets bootFromManifest notice a
    // rebuilt/updated DB on every load rather than only once per session.
    var cached = !forceFresh && readJSONCache(path);
    // Deferred even on a cache hit: callers (the module boot sequence in particular) rely on
    // loadJSON always resolving asynchronously, since x-tag is concatenated after this file and
    // only becomes available once the current synchronous script execution finishes.
    if(cached){ if(success) setTimeout(function(){ success(cached); }, 0); return; }
    if(pendingRequests[path]){ pendingRequests[path].push({success: success, error: error}); return; }
    pendingRequests[path] = [{success: success, error: error}];
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function()
    {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            var waiters = pendingRequests[path];
            delete pendingRequests[path];
            if (xhr.status === 200) {
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
  function resolveUrl(url){
    // Resolve an asset URL from the DB against `cdn`. Absolute (http(s):// or //) URLs are used
    // as-is for backward compatibility with older DBs; relative paths (e.g. "assets/fonts/X.woff2")
    // are prefixed with `cdn`, so a `data-cdn` override redirects fonts too (self-host / offline).
    if(url == null) return url;
    if(/^(https?:)?\/\//.test(url)) return url;
    return cdn + String(url).replace(/^\//, "");
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

  // ==========================================================================
  // DOM building blocks (icons, hover, header/copy chrome, classes)
  // ==========================================================================

  function hoverByType(class_name, type="class", color_bg="lightgrey", color_out="transparent"){
    var elms = (type.toLowerCase() === "tag") ? document.getElementsByTagName(class_name)
                                              : document.getElementsByClassName(class_name);
    Array.from(elms).forEach(function(elm) {
      elm.onmouseover = function() {
        Array.from(elms).forEach(function(element) {
          element.style.backgroundColor = color_bg;
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
    if(aya == -1) classes.push("quran-madina-html-sura-start"); // Decorate Sura Name
    return classes;
  }
  function getCopyIcon(){
    let htmlString = '<svg viewBox="0 0 24 24" class="quran-madina-html-icon" width="20px">'+
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
    let htmlString = '<svg class="quran-madina-html-icon" viewBox="0 0 820 615" style="height:20px"><path d="M70 '+
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
  function buildHeader(sura_name){
    // The multiline chrome: sura name + copy + translate icons, shared by both render paths.
    var header = document.createElement("quran-madina-html-header");
    header.innerHTML = sura_name;
    var copy = getCopyIcon(); copy.addEventListener("click", copyToClipboard);
    var translation = getTranslateIcon(); translation.addEventListener("click", openTranslate);
    header.appendChild(copy);
    header.appendChild(translation);
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
      popup.appendChild(getCopyIcon());
      popup.appendChild(getTranslateIcon());
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
    return Array.from(tag.getElementsByClassName(class_name))
      .map(function(e){ return e.textContent; })
      .join(" ").replace(/\s+/g, " ").trim();
  }
  function positionAyaPopup(popup, elm){
    var rect = elm.getBoundingClientRect();
    popup.style.left = Math.max(4, rect.left) + "px";
    // Prefer floating above the aya; if that would run off the top of the viewport, place it below.
    var estHeight = 34;
    popup.style.top = (rect.top - estHeight - 6 > 0 ? rect.top - estHeight - 6 : rect.bottom + 6) + "px";
  }
  function showAyaPopup(tag, elm, class_name, sura, aya){
    closeAyaPopup(); // only one popup open at a time
    var popup = getOrCreateAyaPopup(tag);
    var copyBtn = popup.children[0], translateBtn = popup.children[1];
    copyBtn.onclick = function(e){
      e.stopPropagation();
      var text = "\u201C" + ayaFragmentsText(tag, class_name) + "\u201D" + "\n\n" +
        madina_data.suras[sura - 1].name;
      navigator.clipboard.writeText(text);
      alert("\u2398 تم نسخ:\n\n" + text);
      closeAyaPopup();
    };
    translateBtn.onclick = function(e){
      e.stopPropagation();
      window.open(`https://quran.com/${sura}/${aya}`, '_blank');
      closeAyaPopup();
    };
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
      elm.style.cursor = "pointer";
      // Overwrite (not addEventListener) so re-registering this aya's other line fragments doesn't
      // stack duplicate handlers - mirrors hoverByType's onmouseover/onmouseout assignment above.
      elm.onclick = function(e){
        e.stopPropagation();
        showAyaPopup(tag, elm, class_name, sura, aya);
      };
    });
  }

  // ==========================================================================
  // Line layout helpers (stretch/center, spacers, structural line starts)
  // ==========================================================================

  function styleMultilineTag(tag, page){
    // Apply the shared block-level chrome to the host tag for a multiline render: font, page-fitting
    // width, and the inset "gutter" shadow whose side depends on the page parity (odd = right page).
    tag.style = "display:block;";
    tag.style.setProperty('font-family', madina_data.font_family, '');
    tag.style.setProperty('font-size', madina_data.font_size+"px", '');
    if(madina_data.font_family === "me_quran"){
      tag.style.setProperty('line-height', madina_data.font_size*2+"px", '');
    }
    tag.style.width = (madina_data.line_width+10)+"px";
    tag.style.setProperty('box-shadow', 'inset '+(page%2==1?"":"-")+'8px 0 7px -7px #333', '');
  }
  function applyLineStyle(line, stretch){
    // A stretch >= 0 is a scaleX factor filling the line; -1 means center this line instead.
    if(stretch >= 0){
      line.style.setProperty("transform", `scaleX(${stretch})`, "");
    } else {
      line.style.setProperty("text-align", "center", "");
    }
  }
  function appendWords(parent, text, range, counter){
    // Render each whitespace-separated word as its own span so non-selected words can be
    // hidden in place (visibility:hidden) while keeping the original Madina line geometry.
    // `counter` is the running 1-based word index across the whole selection (spans ayas).
    text.split(/(\s+)/).forEach(function(token){
      if(token === "") return;
      if(/^\s+$/.test(token)){ parent.appendChild(document.createTextNode(token)); return; }
      var span = document.createElement("span");
      span.textContent = token;
      span.classList.add(`${name}-word`);
      if(!isWordToken(token)){
        // Marker/pause/ornament: never counted as a word itself, but it attaches to the word it
        // follows (e.g. the aya-end marker is appended to that aya's last word at build time), so
        // show it exactly when that preceding word is visible.
        if(counter < range[0] || counter > range[1]) span.classList.add(`${name}-word-hidden`);
      } else {
        counter = counter + 1;
        if(counter < range[0] || counter > range[1]) span.classList.add(`${name}-word-hidden`);
      }
      parent.appendChild(span);
    });
    return counter;
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
      spacer.textContent = parts[i].t;
      spacer.style.cssText = 'display:inline;visibility:hidden';
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
    // index is covered. The title slot (aya index 0) is only ever entered when the walk crosses
    // into a *following* sura, and stays uncounted decoration (under notitle its name text is
    // hidden at render time, keeping the decorated line — see renderWordsSpan). The basmala
    // slot (index 1) is real Quran text and counts like any other words (4 in current DBs —
    // matching the flat Tanzil word indexing that consumers count against; in pre-0.9 DBs it
    // was the "﷽" ligature, which carries no Arabic letter and so still counts 0 there). The
    // walk enters it both when crossing into a following sura and when anchored at a sura's
    // first real aya (internal index 2, see parseAyaRange) — word 1 of an aya-1 anchor is بسم,
    // the same Tanzil indexing as everywhere else. Al-Fatiha is exempt from the anchor rewind:
    // its slot 1 holds its *title* (its basmala is real aya 1) and titles never count.
    var groups = [];
    var current = null;
    var counted = 0;
    // Anchor at a sura's first real aya ⇒ rewind to its basmala slot (Al-Fatiha exempt).
    var anchor_begin = (aya_start === 2 && sura_start > 0) ? 1 : aya_start;
    for(var s = sura_start; s < madina_data.suras.length; s++){
      var ayas = madina_data.suras[s].ayas;
      var aya_begin = (s === sura_start) ? anchor_begin : 0;
      var reached = false;
      for(var a = aya_begin; a < ayas.length; a++){
        var countable = (a >= 1); // title (slot 0) never counts; basmala (slot 1) does
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
  function renderWordsSpan(tag, sura_start, aya_start, range, headless, noQuotes, inlineOpt, notitle){
    // Dedicated render path for the words= selection. Unlike the page/aya loop it is not bound
    // to a single page or sura, so a word range can span both.
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
      styleMultilineTag(tag, start_page);
      if(!headless){
        tag.appendChild(buildHeader(madina_data.suras[groups[0].parts[0].sura].name));
      }
    }
    groups.forEach(function(group, gi){
      var line = document.createElement("quran-madina-html-line");
      if(multiline){
        line.style.setProperty('display', 'block', '');
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
          if(basmalaWords > 0 && counter + 1 >= range[0] && counter + basmalaWords <= range[1]){
            // The whole basmala falls inside the selection: render the traditional ligature
            // instead of its individual tokens (it still advances the word counter by all 4
            // words, so following word indices are unchanged). A partial overlap falls through
            // to appendWords so exactly the selected basmala words show.
            var lig = document.createElement("span");
            lig.classList.add(`${name}-word`, `${name}-basmala`);
            lig.textContent = BASMALA_LIGATURE;
            aya_part.appendChild(lig);
            counter = counter + basmalaWords;
          } else {
            counter = appendWords(aya_part, item.part.t, range, counter);
          }
        } else if(notitle && item.ayaIdx === 0){
          // notitle: keep the title's line and its decorative frame (the sura_border SVG is
          // painted on the line via :has(.quran-madina-html-sura-start), so the div and its
          // class must stay) but hide the name text itself. visibility:hidden preserves the
          // line's height/centering and excludes the name from copy (visibleClone strips it).
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
  var this_script = document.currentScript || document.querySelector(`script[src*="${name}"]`);
  var doc_name    = this_script.getAttribute('data-name') || "Madina05";
  var doc_font    = (this_script.getAttribute('data-font') || "me_quran").replaceAll(" ","_");
  var doc_font_sz = parseInt(this_script.getAttribute('data-font-size'), 10) || DEFAULT_FONT_SIZE;
  var doc_cdn     = this_script.getAttribute('data-cdn');
  if (doc_cdn) cdn = doc_cdn.replace(/\/?$/, "/"); // honor explicit base, ensure trailing slash
  print(`${doc_name} with font: ${doc_font} size: ${doc_font_sz}`);
  const name_css = cdn+"dist/"+name+".min.css?v=1.1";
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
        var j = suraAyaToJuz(sura0, ar[0]); return [j, j + 1]; // words spill forward < one juz'
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

  function attrAccessor(attr){
    // Every public attribute is a plain string mirror: reads pull straight from the DOM attribute,
    // writes stash into xtag.data. Generated for each name below to kill the boilerplate.
    return {
      attribute: {},
      set: function(value){ this.xtag.data[attr] = value; },
      get: function(){ return this.getAttribute(attr); }
    };
  }
  function initTag(){
          const myFont = new FontFace(madina_data.font_family, 'url('+encodeURI(resolveUrl(madina_data.font_url))+')');
          myFont.load().then( () => {document.fonts.add(myFont);});
          var accessors = {};
          ["page", "page_param", "aya", "sura", "words", "headless", "quotes", "inline", "notitle"]
          .forEach(function(attr){
            accessors[attr] = attrAccessor(attr);
          });
          xtag.register(name, {
            lifecycle: {
              created: function() {
                this.render(this);
              },
              inserted: function() {},
              removed: function() {},
              attributeChanged: function() {
                this.render(this);
              }
            },
            events: {},
            accessors: accessors,
            methods: {
               render: function(tag){
                // Re-entrancy guard. While building we mutate the element's style attribute, and
                // x-tag re-invokes render() on any attribute change — that nested render would clear
                // and rebuild mid-build, duplicating the output. The guard drops such re-entrant
                // calls; genuine user-driven renders run when no render is in progress.
                if(this.xtag.data.rendering){ return; }
                var self = this;
                // Sharded DB: ensure the juz' shard(s) this render will read are loaded, then render
                // synchronously. Monolith mode: ensureJuz invokes the callback immediately.
                ensureJuz(neededJuz(this), function(){
                  if(self.xtag.data.rendering){ return; }
                  self.xtag.data.rendering = true;
                  try {
                    self.doRender(tag);
                  } finally {
                    self.xtag.data.rendering = false;
                  }
                });
               },
               doRender: function(tag){
                var sura_from, sura_to, aya_from, aya_to, line_from, line_to;
                var multiline;
                var words_range = null;
                // `page` is the page to render, derived locally. We deliberately never write derived
                // state (sura/aya/page) back onto the element: those are x-tag accessor attributes,
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
                      // words= has its own renderer that spans pages and suras from the start aya.
                      renderWordsSpan(tag, sura_from, aya_from, words_range, headless, noQuotes,
                                      inlineOpt, notitle);
                      return;
                    }
                  }
                }
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
                  styleMultilineTag(tag, page);
                  if(!headless){
                    tag.appendChild(buildHeader(madina_data.suras[sura_from].name));
                  }
                }
                /** Loop on Ayas, lines, parts */
                var aya_current = aya_from;
                var sura_current = sura_from;
                for(let l = line_from; l <= line_to; l++) {
                  const ll = l; //Const for inner loops to refer
                  let line = document.createElement("quran-madina-html-line");
                  tag.appendChild(line);
                  if(multiline){
                    line.style.setProperty('display','block','');
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
                        // A page render always shows the complete basmala line, so it gets the
                        // traditional ligature instead of the DB's 4 word tokens (blank slots,
                        // e.g. At-Tawba's, stay blank).
                        aya_part.textContent = (isBasmalaSlot(sura_current, a) && line_match[0].t !== "") ?
                          BASMALA_LIGATURE : line_match[0].t;
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
          });
  }

  // ==========================================================================
  // Boot: prefer the sharded manifest, fall back to the monolithic DB, fall back to the default
  // font-size's DB if no DB was ever built for the requested size (e.g. a font only shipped at 16px).
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
          suras: m.suras.map(function(e){ return {name: e[0], ayas: new Array(e[1])}; }),
          juz: m.juz, pages: m.pages
        };
        initTag();
      },
      bootMonolith,
      true
    );
  }
  function bootMonolith(){
    loadJSON(`${cdn}assets/db/${dbstem}.json`,
      function(data){ madina_data = data; initTag(); },
      function(xhr){
        if(doc_font_sz != DEFAULT_FONT_SIZE){
          print(`no DB for font: ${doc_font} size: ${doc_font_sz}, falling back to size: ${DEFAULT_FONT_SIZE}`);
          setFontSize(DEFAULT_FONT_SIZE);
          bootFromManifest();
        } else {
          console.error(`${name}> no manifest and no monolithic DB`, xhr);
        }
      });
  }
  bootFromManifest();

})();
