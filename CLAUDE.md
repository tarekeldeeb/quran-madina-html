# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A browser library that renders Quran pages visually similar to the printed Madina Mushaf
**without images** — pure HTML/CSS driven by pre-computed JSON databases. It ships as a custom
element (`<quran-madina-html>`) built on the native Custom Elements v1 browser API, published to
npm and served via unpkg.

**Since 2.0 every tag renders through the v2 path** (see the v2 section at the end):
`data-font`/`data-name` are ignored with a console warning (`use_v2 = true` in the attribute
block). The v1 sections below describe code that is still in the runtime but unreachable, and
the 1.x DB builder; the npm `files` list ships only `assets/db/v2` (json + woff2) and `assets/img`.

There are two distinct halves:

1. **Runtime (JS/CSS)** — `src/quran-madina-html.js` + `src/quran-madina-html.css`. Loaded in a
   browser, registers the `<quran-madina-html>` custom tag, fetches a JSON DB, and renders lines.
2. **Build-time DB generator (Python)** — `src/db/`. A heavyweight offline pipeline that produces
   the JSON databases the runtime consumes. End users never run this; it regenerates `assets/db/*.json`.

## Commands

```bash
npm install              # install JS deps + the python deps are separate (see below)

# Python deps (DB generator + tests) — use a venv to avoid clobbering global packages,
# since requirements.txt pins exact versions that conflict with other globally-installed tools.
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
# thereafter run pytest as: .venv/bin/python -m pytest ...

npm run build            # grunt: jshint, clean, concat (unminified + license header), json-minify
npm run build-db         # regenerate ALL assets/db/*.json (slow: downloads + headless Chrome). See below.
npm run start            # http-server on localhost:8000 (required for render tests + demo)
npm test                 # python -m pytest (runs both test/db_test.py and test/render_test.py)
npm run release          # release-it (runs grunt via after:bump hook, so the header carries the new version)
```

Run a single test:
```bash
python -m pytest test/db_test.py                                   # JSON DB integrity (fast, no browser)
python -m pytest test/db_test.py::BasicDBTest::test_2_sura_count   # one test method
python -m pytest test/render_test.py                               # needs `npm run start` running first (uses Selenium against localhost:8000)
```

Lint: `npm run build` runs jshint on JS. Python uses `ruff` (in requirements.txt). CI runs pylint, pytest, CodeQL, and npm-grunt (see `.github/workflows/`).

## DB generation pipeline (`src/db/`)

`build_all.py` is the entry point — it fans out `build_db.py`'s `DbBuilder.run()` across a `Pool(4)`
for each font config (Hafs default, Amiri Quran, Amiri Quran Colored @16 & @24px, Uthman, me_quran).
Each run, in `DbBuilder.run()`:
1. Downloads the OCR glyph DB (SQLite) from murtraja's quran-android-images-helper and the Uthmani
   text from Tanzil.net into `tmp_download/` (skipped if `tmp_download/` already exists).
2. Spins up **headless Chrome via Selenium** and measures the rendered pixel width of every aya part
   in the target font (`HtmlHelper.get_width` against `template/part_width_test.html`).
3. Computes a per-line `stretch` (scaleX factor, clamped roughly 0.5–2.0) so each line fills
   `line_width`, then writes `assets/db/Madina05-<font>-<size>px.json`. Any justified line that
   would need scaleX > 1.0 (`QuranLine.KASHIDA_TARGET_STRETCH`) is first widened with real
   kashidas — the print stretches short lines with kashida strokes, not wider glyphs:
   `kashidas_needed()` converts the missing pixels into a count via a per-font tatweel advance
   measured in-context (`DbBuilder.kashida_unit_width()`, cached per run), estimating in a single
   pass (no iterative remeasure-and-correct loop) how many tatweels bring the line as close to
   scaleX 1.0 as that one estimate can land it, and `place_kashidas()` gives each eligible word one
   elongation run at its last legal connection (`_word_kashida_point`: after a forward-joining
   letter only, never splitting lam-alef, never before a bare hamza, never a connection already
   carrying Tanzil's dagger-alef tatweel), spreading the count evenly across the line's words;
   modified parts are re-measured once so the residual scaleX reflects real widths. So stored `t`
   text may contain build-inserted tatweels beyond the
   dagger-alef carriers Tanzil itself ships (`tatweel=true` download) — the runtime treats both
   as plain text. (No per-part pixel offset is
   stored — text that starts mid-line is positioned at render time by re-flowing the preceding text
   invisibly; see below.) A surah's actual last line only gets `stretch=-1` (unjustified/centered)
   when it's naturally no wider than `line_width` — a last aya isn't always short (in Hafs-16px,
   ~78% of the 114 surah-end lines measure wider than line_width), so unconditionally leaving them
   unstretched let most of them overflow the frame; a line that's naturally too wide instead falls
   through to normal compression (`stretch<1`, clamped like any other line).

Class roles: `Mushaf` → `Surah` → `Ayah` → `QuranLine`/`Part` model the document tree.
`DbReader` reads the OCR SQLite for page/line geometry. `JsonHelper` writes the final JSON
(header fields: `title, published, font_family, font_url, font_size, line_width, suras`).
`LineCursor` tracks the current page/line position while laying out ayas.

## JSON DB shape (the contract between the two halves)

`suras[].ayas[]` each have `p` (page) and `r[]` (render parts). Each part: `l` (line 1–15),
`t` (text), `s` (stretch/scaleX; **`-1` means center this line instead of stretching**). The runtime
in `src/quran-madina-html.js` reads exactly these keys — if you change field names in `build_db.py`,
update `render()` in the JS too. **There is no per-part pixel offset** (`o` was removed): a part that
begins mid-line is positioned by rendering the preceding text on that line invisibly (spacers /
`lineContext`), so the line's own stretch/centering places it exactly as on the full page. Line
starts are detected structurally via `isLineStartPart()` (a part is a line start iff the previous
aya doesn't also sit on that page-line) rather than a stored `o === 0` sentinel. Hindi (Arabic-Indic) aya numbers and
font-specific text tweaks (Amiri uses `۝`, others use ornate parens; Uthman replaces `ٱ`→`ا`, via
`Ayah.apply_font_tweaks`) are baked in at build time in `Ayah.__init__`. Every sura carries **2
decoration slots** before its real ayas (index 0 = title, 1 = basmala; real aya A is at index A+1 —
the invariant `parseAyaRange`/`shard_db.py` depend on). Since 0.9.0 the basmala slot stores the
**4 real word tokens** from the Tanzil text (built by `Surah.get_basmala()`, same font tweaks as
ordinary text; it also strips the idgham shadda Tanzil puts on the basmala's ب in suras 95 & 97,
whose preceding suras end in ب — the slot renders standalone) rather than the `﷽` ligature, so
the runtime can count/select them individually;
exceptions: Al-Fatiha has inverted `[blank, title]` slots (its basmala IS real aya 1), and At-Tawba's
slot 1 is blank (no basmala in the real text). Decoration slots are always centered (`s:-1`).

## Runtime rendering notes (`src/quran-madina-html.js`)

- Single IIFE, no build-time module system. `cdn` auto-switches to `../` on localhost so local dev
  and the demo resolve assets from the repo root.
- The tag accepts either `page="N"` (full page, multiline) **or** `sura="N" aya="A-B"` (range). Note
  the off-by-one handling: sura is 0-based internally, and aya ranges add an offset of 1 for the
  hidden Title + Basmala "ayas" (`parseSuraRange`/`parseAyaRange`).
- The optional `words` attribute (1-based, inclusive; `start-end`, `start:end`, or single `index`;
  works with `sura`+`aya`, ignored with `page`) restricts output to a word subsequence. It has its
  own render path, `renderWordsSpan()`, **separate from the page/aya loop** because it is not bound to
  a single page or sura: word indices are counted from the given `sura`/`aya` and may run past it,
  crossing page **and** sura boundaries. `collectWordParts()` walks ayas in reading order, grouping
  parts into visual lines keyed by `(page, line)`, until the end index is covered (`countAyaWords()`
  does the counting); when it crosses into a new sura, that sura's **title** (aya index 0) is rendered
  for context but never counted, while its **basmala** (index 1) **counts as 4 real, individually
  selectable words** (since 0.9.0 — matches the flat Tanzil word indexing consumers count against;
  At-Tawba's blank slot contributes none). Display rule: if **all 4** basmala words fall inside the
  selection they render as the single `﷽` ligature (`BASMALA_LIGATURE`/`isBasmalaSlot()`, still
  advancing the counter by 4); a partial overlap renders the individual word spans. Full-`page`
  renders always show the ligature. The `notitle` boolean attribute hides crossed-into sura **name
  text** while keeping the decorated title line (the sura_border SVG frame hangs off
  `:has(.quran-madina-html-sura-start)`, so the div/class stay; the name renders in a
  `visibility:hidden` span that still sizes the line) — words= path only; page/aya renders ignore it.
  Decoration slots stay non-clickable in `wireAyaClick` (deliberate: no quran.com verse to link).
  Rendering does **not** re-layout: every
  word becomes its own `<span>` and non-selected words get class `quran-madina-html-word-hidden`
  (`visibility:hidden`), so the Madina stretch/offset geometry is preserved and only the chosen words
  are visible. A selection that fits one line renders inline; otherwise it gets the multiline block +
  header. Aya-number ornaments (`AYA_MARKER`) are never counted. See `appendWords()`.
  Validation/limits in this path: `parseWordsRange()` rejects a malformed, zero/negative, or reversed
  range (`start > end`) by returning `null`, and `doRender()` then **falls back to the normal verse
  render** (logs `Bad words parameter`). The span is **capped at 500 words** (`doRender` clamps
  `range[1]`). Because counting is per-word, `collectWordParts()` returns `{groups, counterStart}` and
  **trims fully-hidden lines** off both ends — leading lines before `range[0]` and trailing lines after
  `range[1]` (the latter occur because collection grabs whole ayas that spill onto further lines), so
  the block always starts and ends on a line that shows a selected word; `counterStart` carries the
  skipped leading words so visibility still lines up. `countPartWords()` counts a single part (and
  `countAyaWords()` sums it over an aya). Combining `words` with an `aya` **range** ignores the range
  end (only the start aya seeds the walk) and logs a warning. The copy button (`copyToClipboard()` via
  `visibleClone()`) copies only visible text — it strips the header, `quran-madina-html-word-hidden`
  spans, and `visibility:hidden` spacers from a detached clone rather than trusting `innerText`.
- `highlight`/`error` (same 1-based range format as `words`, parsed by the same `parseWordsRange()`)
  overlay a visual mark — `quran-madina-html-word-highlight` (soft yellow) / `-word-error` (soft red,
  wins on overlap) — on top of whatever is being shown, applied per-word in `appendWords()` via
  `applyMarkClass()`. Unlike `words`, they work in **every** render mode, not just alongside a
  `words` selection: a plain `sura`+`aya` verse with no `words` at all, and even a full `page` (a
  page never starts mid-aya, so "word 1" is always its first real aya's first word — see
  `countVerseRangeWords()`/`countPageWords()`). When neither is set, `doRender()`'s plain page/aya
  loop keeps its original single `textContent` assignment untouched (`wordMarkMode` gate); when
  either is set, that loop instead calls `appendWords()` per part (skipping title parts, which are
  never countable/markable) the same way `renderWordsSpan()` already does, threading a running
  `word_counter` across the whole loop. Each range is validated against whatever is actually
  displayed — the (possibly 500-capped) `words` range if one is active, otherwise the full
  verse/page word count — via `clampedOrNull()`; a malformed or out-of-bounds range is dropped
  (console warning) rather than aborting the render, unlike a malformed `words`. A fully-in-selection
  basmala normally collapses to the `﷽` ligature; `basmalaRenderMode()` forces the 4 individual
  tokens instead whenever a `highlight`/`error` range cuts into only *some* of its 4 words (a range
  that covers all 4, or none, still gets the ligature — with the mark class on that single span).
  CSS custom properties `--qmh-highlight`/`--qmh-error` set the colors; the two class rules carry
  `background-color` only (no padding/margin/border), since every word span's measured width feeds
  the line's pre-computed stretch/kashida geometry.
- `letters` ("1:3 crimson, 4:3-5 emerald blink, 6:2+4": word numbers counted like `highlight`,
  letter numbers, optional colour from `LETTER_COLORS` or any CSS colour, crimson by default,
  optional trailing `blink` → `.quran-madina-html-letter-blink`, no animation otherwise) marks single
  letters. It takes the numbered word path like `highlight` (`wordMarkMode`; every counted word span
  carries `data-qmh-w`), then `applyLetters()` runs after every render path (`render()`), shifting by
  `tag._qmhLetterShift` in the cross-page verse path. `wrapLetters()` splits the word's text into
  letters (`LETTER_RIDER`: marks, CGJ/ZWJ, tatweel ride on the letter before) and wraps the chosen
  ones in `.quran-madina-html-letter` spans, the rest in `.quran-madina-html-ink`. Colour and
  text-shadow only, so the browser shapes the word as before (render test 40 checks nothing moves).
  The halo must sit *behind* other ink: the tag gets `quran-madina-html-lettered` and all other ink
  (other words, `-ink` pieces) is lifted to `position:relative; z-index:1`, the letter stays in flow.
  Do not use the CSS Highlight API (it clips glyphs whose ink overhangs their advance, common in
  this script) nor a negative z-index/inline-block on the word (paints under the word's background
  or changes its box). `blink` only pulses the halo; off in print and with reduced motion.
- A range that fits on one line renders as an inline `<span>`; otherwise a multiline `<div>` with a
  header (sura name + copy/translate icons). Generated child tags: `<quran-madina-html-line>`,
  `<quran-madina-html-header>`, and per-aya `<div>`s classed `quran-madina-html-NNN-NNN` for hover
  highlighting and the "translate" deep-link to quran.com. Clicking one of those per-aya divs
  (`wireAyaClick`/`showAyaPopup`) shows a `<quran-madina-html-aya-popup>` positioned over it with its
  own copy/translate buttons scoped to *that* aya alone (vs. the header's, which act on the whole
  frame/its first aya) — this is the only copy/translate affordance for inline (single-line) renders,
  which have no header of their own. Inline renders also get opening/closing quote marks (CSS
  `::before`/`::after` on `quran-madina-html-line`, gated by a `quran-madina-html-inline` class the
  render loop toggles) as their only visual cue that the text is a quoted excerpt; the optional
  `quotes="no"` attribute opts a tag out of this. (Note: a hyphenated attribute name can't be a
  plain JS identifier/property name for a class getter/setter, so hyphenated attributes are read
  via `getAttribute()` directly instead of via a same-named class getter, or avoid the hyphen as
  done here.)
- Properties reflect to attributes (`reflectAttribute`; since 2.1.2): `tag.aya = 3` sets
  `aya="3"`, true -> empty attribute, null/false -> removed. Vue, Svelte and Angular property
  bindings depend on it (render test 44). `attributeChangedCallback` renders only when the tag is
  connected, so a framework setting attributes one by one before insertion renders once.
  `this._data` holds only the render re-entry guard.
- Stretch is applied as a CSS `scaleX()` transform on the line. There is no stored offset; a
  selection/line that starts mid-line reflows the preceding text invisibly (spacers) so the line's
  own stretch/centering positions the first visible word.
- **Arbitrary font sizes** (any `data-font-size` in 6–100, floats allowed): only the two
  `ANCHOR_SIZES` (16/24) have pre-built DBs; any other size S boots via `bootInterpolated()`,
  which fetches both anchors' headers (manifest preferred, monolith fallback), reads `line_width`
  off the line fitted through the two anchor points (the per-size widths are hand-tuned, NOT
  proportional — Hafs is 270@16 / 410@24), and renders the **nearest** anchor's DB (text incl.
  its kashidas, stretch factors) at size S. Because glyph widths DO scale ∝ S while the fitted
  width doesn't, every justified line's scaleX is corrected by one global factor
  `stretch_scale = lw(S)·anchor / (lw(anchor)·S)`, stored on `madina_data` and applied in
  `applyLineStyle`. The overrides ride in module-level `sizeOverrides`, applied by both boot
  paths just before `initTag`; a missing anchor DB falls back to the default size like before.

## v2 (letter stretching, `assets/db/v2`, `src/db/v2/`)

Selected with `data-layout` on the script tag: `1441H` (default), `1405H`, `IndoPak` (case
insensitive; an unknown value warns and falls back to 1441H). `data-font`/`data-name` are ignored
(console warning) — 2.0 is a drop-in upgrade. Design notes and measurements: `docs/v2/design-decisions.md`.

- **Fonts:** DigitalKhatt's `madina.otf` / `oldmadina.otf` / `indopak.otf` (OFL), patched by
  `font_patch.py` with an AlternateSubst lookup + position features `jp01..jpNN` (`jpKK` swaps
  the glyph at position KK of the word, the value picks the variant). HarfBuzz decides each
  word's stretch at build time; the DOM gets one `font-feature-settings` per word span.
  **The browser never gets `jpKK` values:** Apple's CoreText (every iOS browser) ignores a
  feature's value inside the nested AlternateSubst and always takes alternate 1. So the font
  also carries one on/off feature per (position, alternate) pair the DB uses, `qKKv` (v in base
  36; `add_boolean_features`), and `v2FeatureSettings` turns the DB's `jp04=3` into `"q043"`.
  The DB keeps the `jp` form (HarfBuzz/build/checks use it). `demo/diag.html` measures every
  word of page 6 on a device against `demo/diag-expected.json` (Chrome's widths).
- **Text:** Tanzil (`--tanzil`), converted to the fonts' encoding by `tanzil_encoding.py`
  (1441H takes pause marks from the print; a Tanzil file without marks gets marks + ۞/۩ from the
  layout text). IndoPak uses DigitalKhatt's own IndoPak text (`layout_lines.layout_tokens`),
  numbered with the Kufan count so sura/aya address the same verse in every layout.
- **Line breaks:** 1441H from the KFGQPC print (`src/db/v2/data/print-1441H-lines.json`, made by
  `extract_print_lines.py`); 1405H and IndoPak from DigitalKhatt's layout texts.
- **Fitting** (`justify.fit_line_print`): ink-to-ink gaps between words (band profiles,
  `ink.py`) kept in the print's measured range; loose lines stretch letters (Madina:
  `_Justifier.run`, a port of DigitalKhatt's experimental justifier; IndoPak:
  `run_simple`, its applySimpleJust), dense lines narrow words (`c`, never aya numbers), the
  whole line is scaled (`x`) only as a last resort. Never use `shr1`/`shrr` (they overlap letters).
- **DB schema (version 2):** header + `lines[page][line] = {k, w, z, s[], x?, c?}` (em) +
  `suras` (v1 shape, parts carry `f` = per-word feature strings). Spaces `s` may be negative.
  `shard_db.py` splits v2 DBs too: line rows travel with the juz' shards of their pages.
  Stems: `Madina-1441H`, `Madina-1405H`, `IndoPak-15` (`V2_STEMS` in the runtime).
- **Runtime:** `isV2()` branches; `v2InitLine` (row geometry), `v2AppendWords` (word spans,
  spaces, narrowing with transform-origin right/left for the line's first/last word). A
  `sura`+`aya` range that runs onto another page renders through `renderWordsSpan`.
- **Checks:** `check_v2_db.py <db>` (widths with the patched font), `test/v2_encoding_test.py`,
  `test/v2_layout_test.py` (print line breaks, gaps). `render_test.py` runs against the
  default 1441H layout (its template sets no attributes; `FontSizeTest` checks em scaling).

## Wrappers

- `react/` — `@tarekeldeeb/quran-madina-react` (npm), published by `scripts/publish-wrapper.mjs`.
  Offline like Flutter: `bin/bundle.mjs` (`npx quran-madina-bundle`, bin in package.json; pure
  helpers in `bin/lib.mjs`, same rules as `flutter/lib/src/bundle.dart`) copies the library from
  npm (or `--from` a checkout) into `public/quran-madina/`; the `bundled` prop (`bundleUrls()`)
  sets src/cdn to `/quran-madina/` or a given base.
- `react-native/` — `@tarekeldeeb/quran-madina-react-native` (npm, published with the React one by
  `publish-wrapper.mjs`; no build, plain JS with React.createElement). `QuranMadinaNative` wraps
  react-native-webview like the Flutter widget: `src/page.js` (pure, tested) builds one host
  page; online it's an HTML string with the config inlined (baseUrl = cdn), bundled it's the
  same page written as `index.html` by `bin/bundle.mjs` (`npx quran-madina-native-bundle`) into
  `android/app/src/main/assets/quran-madina/` and `ios/quran-madina/` (iOS: Xcode folder
  reference), loaded as `file:///android_asset/quran-madina/index.html` or the bundle-relative
  `quran-madina/index.html`, its config via `injectedJavaScriptBeforeContentLoaded` (+ onLoadEnd
  fallback). The library accepts status-0 XHR for non-http URLs (`localFileLoaded`) for this.
  Messages via `window.ReactNativeWebView.postMessage` (height, open, error). `bin/lib.mjs` is
  a copy of react/bin/lib.mjs (a test keeps them equal). Dev installs need `legacy-peer-deps`
  (`react-native/.npmrc`). Not run on a device in CI: tests mock React Native and the WebView.
- `flutter/` — `quran_madina_flutter` (pub.dev; Dart forbids hyphens in package names).
  `QuranMadinaFlutter` (`lib/src/widget.dart`) picks its State by conditional import:
  `view_io.dart` (Android/iOS/macOS: a `WebViewWidget` loading `buildPage()` from
  `lib/src/page.dart`, pure and unit-tested; height and `window.open` come back over the `QMH`
  JavaScript channel; tag changes via `qmhSet()` in place, loader changes reload) or
  `view_web.dart` (web: the tag in an `HtmlElementView`, the script added to the document once,
  so the first widget's layout/size/URLs are page-wide; height from a ResizeObserver).
  Offline: `bin/bundle.dart` (`dart run quran_madina_flutter:bundle --layouts ...`) pulls the
  npm tarball and copies script, CSS, images and each layout's shards + font
  (`lib/src/bundle.dart`, pure) into the app's `assets/quran_madina/`. `bundled: true` swaps the
  `qmh-bundle:/` placeholder for a loopback HTTP server (`bundle_server.dart`, serving
  rootBundle; apps must allow cleartext to 127.0.0.1 / NSAllowsLocalNetworking) or, on the web,
  the app's asset URL. CI (`.github/workflows/flutter.yml`): publish dry run, analyze, test,
  the bundler for real, a web build and an Android build of `example/` (made with
  `flutter create .`). No local SDK is assumed.
- `wordpress/quran-madina-html/` — WordPress plugin (Quran block + `[quran]`/`[quran_madina]`
  shortcode, Settings → Quran Madina: print + size). Written for the WordPress.org guidelines:
  no CDN (guideline 8), so the plugin carries the library in `library/` (gitignored, made by
  `wordpress/build.sh [--zip out.zip]` from `dist/` after grunt + every layout's shards, fonts,
  images; ~3 MB zipped, the directory's limit is 10 MB). Prefix `qmhtml_`/`QMHTML_` (the
  review team asks for long prefixes); `qmhtml_settings()` still reads the 2.1.1-2.1.3 option
  `qmh_settings`. `includes/render.php`: `qmhtml_tag()` builds the tag (attributes whitelisted;
  `qmhtml_clean_value()` validates each: ranges, quotes/inline words, letters chars; page wins
  over sura/aya), enqueues the library in the footer only where used, `script_loader_tag` adds
  data-cdn (the plugin's library/ URL)/layout/font-size. `block/editor.js` is plain JS (no
  build); the editor loads the library through `enqueue_block_assets` for the live preview.
  `tests/run.sh` runs it in real WordPress (GitHub clone + SQLite drop-in + `php -S`, needs
  library/ built) and checks the HTML and served files. CI (`.github/workflows/wordpress.yml`):
  build, tests, `WordPress/plugin-check-action` on the zip's contents; on a release tag it
  attaches `quran-madina-html-wordpress.zip` to the GitHub release ("latest/download" link).
  License: the plugin folder, its library/ copy included, is dual GPL-2.0-or-later / Waqf GPL
  2.0 (`LICENSE.txt` lists the third-party parts: OFL fonts, Tanzil text CC BY 3.0 verbatim,
  quran-qcf4 MIT); header and readme say `GPLv2 or later` (Plugin Check requires them to
  match); everything outside the plugin stays Waqf only.
- `scripts/sync-wrapper-version.mjs` (release-it `after:bump`) keeps all of them at the core version,
  including the WordPress plugin header, QMHTML_VERSION and readme Stable tag, `flutter/pubspec.yaml`, `kLibraryVersion` (`lib/src/version.dart`, the bundler's
  default) and a `flutter/CHANGELOG.md` entry. pub.dev: the release tag (e.g. `2.1.1`) starts
  `.github/workflows/flutter-publish.yml` (OIDC, no stored secret; pub.dev Admin -> Automated
  publishing, tag pattern `{{version}}`). Tags pushed with GITHUB_TOKEN start no workflows, so
  release.yml checks out with the `RELEASE_PAT` secret when it is set.

## Docs and README

- `README.md` is a short showcase only (badges, description, `docs/assets/img/showcase.gif`,
  getting started for HTML/React/React Native/Flutter, a pointer to the Vue/Angular/Svelte/Astro pages, WordPress, credits, license). Everything else lives in the docs
  site: MkDocs Material, `mkdocs.yml` + `docs/` + `overrides/main.html` (which loads the library
  from unpkg `@2`, so raw `<quran-madina-html>` tags in the Markdown render live).
  `mkdocs serve` to preview; `.github/workflows/docs.yml` builds with `--strict` and publishes
  to `gh-pages/docs/`, plus the site root's `index.html`: the README rendered by
  `scripts/readme_page.py` (gh-pages has `.nojekyll`, so nothing renders README.md for us).
  Pin `mkdocs<2`.
- New attributes/options go in the guide page for the topic AND `docs/reference/`.
- `scripts/readme_gif.py` re-renders the README GIF (needs `npm run start`); the blink scene
  pauses the CSS animation at fixed times. `scripts/readme_screenshots.py` makes the stills.
- gh-pages holds the demo (root), `flutter/` (Flutter web example, published from main by
  `.github/workflows/flutter-web-example.yml`) and `docs/` (this site, by `docs.yml`): when
  redeploying the demo by hand, keep `flutter/` and `docs/`. The branch's `.gitignore` excludes
  `dist`, so anything that ships a `dist/` folder must be added with `git add -f`.
- The 1.x docs are `docs/v1.md` (was README_v1.md).

## Conventions

- `src/db/test*.html` files are temp scratch files written/removed during DB builds — don't commit them.
- `tmp_download/` caches the downloaded SQLite + Tanzil text; delete it to force a fresh download on
  the next `build-db`.
- Distributables in `dist/` are generated by grunt — edit `src/`, never `dist/` directly. Since
  2.1.2 they are `dist/quran-madina-html.js` / `.css` (readable, with a license banner; `main`
  points at the .js); grunt also writes identical `.min.js` / `.min.css` copies for 2.x pages
  that link those names (remove the `*_min` concat targets in 3.0). Everything in the repo uses
  the new names; the bundlers (react/bin/lib.mjs, flutter bundle.dart, WordPress local-copy)
  take whichever exist and alias an old package's `.min.js` to the new name.
- `data-layout` (default `1441H`) and `data-font-size` (default 16, any size) on the `<script>`
  tag select which `assets/db/v2/` DB is fetched and how it is scaled.
