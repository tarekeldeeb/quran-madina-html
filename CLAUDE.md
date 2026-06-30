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
3. Computes per-line `stretch` (scaleX factor, clamped roughly 0.5–2.0) and `offset` so each line
   fills `line_width`, then writes `assets/db/Madina05-<font>-<size>px.json`.

Class roles: `Mushaf` → `Surah` → `Ayah` → `QuranLine`/`Part` model the document tree.
`DbReader` reads the OCR SQLite for page/line geometry. `JsonHelper` writes the final JSON
(header fields: `title, published, font_family, font_url, font_size, line_width, suras`).
`LineCursor` tracks the current page/line position while laying out ayas.

## JSON DB shape (the contract between the two halves)

`suras[].ayas[]` each have `p` (page) and `r[]` (render parts). Each part: `l` (line 1–15),
`t` (text), `o` (left offset px), `s` (stretch/scaleX; **`-1` means center this line instead of
stretching**). The runtime in `src/quran-madina-html.js` reads exactly these keys — if you change
field names in `build_db.py`, update `render()` in the JS too. Hindi (Arabic-Indic) aya numbers and
font-specific text tweaks (Amiri uses `۝`, others use ornate parens; Uthman replaces `ٱ`→`ا`)
are baked in at build time in `Ayah.__init__`.

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
  does the counting); when it crosses into a new sura, that sura's name/basmala entries (aya indices
  0/1) are rendered for context but **not** counted as words. Rendering does **not** re-layout: every
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
  `<quran-madina-html-header>`, `<quran-madina-html-copy>`, and per-aya `<div>`s classed
  `quran-madina-html-NNN-NNN` for hover highlighting and the "translate" deep-link to quran.com.
- Stretch is applied as a CSS `scaleX()` transform on the line; offset as `padding-right`.

## Conventions

- `src/db/test*.html` files are temp scratch files written/removed during DB builds — don't commit them.
- `tmp_download/` caches the downloaded SQLite + Tanzil text; delete it to force a fresh download on
  the next `build-db`.
- Distributables in `dist/` are generated by grunt — edit `src/`, never `dist/` directly.
- `data-name` (default `Madina05`), `data-font` (default per README; runtime default `me_quran`),
  and `data-font-size` (default 16) on the `<script>` tag select which `assets/db/*.json` is fetched.
