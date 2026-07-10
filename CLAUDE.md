# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A browser library that renders Quran pages visually similar to the printed Madina Mushaf
**without images** — pure HTML/CSS driven by pre-computed JSON databases. It ships as a custom
element (`<quran-madina-html>`) built on the X-Tag library, published to npm and served via unpkg.

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

npm run build            # grunt: jshint, clean, concat (src + x-tag) into dist/, uglify, cssmin, json-minify
npm run build-db         # regenerate ALL assets/db/*.json (slow: downloads + headless Chrome). See below.
npm run start            # http-server on localhost:8000 (required for render tests + demo)
npm test                 # python -m pytest (runs both test/db_test.py and test/render_test.py)
npm run release          # release-it (runs grunt via after:init hook)
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
  `quotes="no"` attribute opts a tag out of this. (Note: an attribute name used as an x-tag accessor
  key must not contain a hyphen — `this['no-quotes']`-style hyphenated keys silently fail to register,
  leaving the accessor permanently `undefined`; read hyphenated attributes via `getAttribute()`
  directly instead, or avoid the hyphen as done here.)
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

## Conventions

- `src/db/test*.html` files are temp scratch files written/removed during DB builds — don't commit them.
- `tmp_download/` caches the downloaded SQLite + Tanzil text; delete it to force a fresh download on
  the next `build-db`.
- Distributables in `dist/` are generated by grunt — edit `src/`, never `dist/` directly.
- `data-name` (default `Madina05`), `data-font` (default per README; runtime default `me_quran`),
  and `data-font-size` (default 16) on the `<script>` tag select which `assets/db/*.json` is fetched.
  A non-anchor font-size (anything other than 16/24) fetches the nearest anchor's DB and
  interpolates its geometry — see the arbitrary-font-size bullet above.
