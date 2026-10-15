# v2.0 — Phase 1: proof of concept (page 3)

## Decision: pilot font is **DigitalKhatt Old Madina**, not New Madina

The repo's layout is the 1405H Madina print (`Madina05`). DigitalKhatt ships a
HarfBuzz build for exactly that layout:

| | |
|---|---|
| Font | DigitalKhatt Old Madina (`ClientApp/src/assets/fonts/hb/oldmadina.otf`, CFF2) |
| License | SIL OFL 1.1 — © 2023-2024 Amine Anane, © 2024 Tarteel Inc. |
| Text | DigitalKhatt `quran_text_old_madinah.ts` (MIT) — 604 pages × 15 lines, **same line breaks as our DB** (checked on pages 1-3) and the encoding the font expects (e.g. hamza written with U+034F joiners) |

Besides the per-letter `cv01`–`cv18` features (Phase 0), this font has
**whole-word stretch features**: `jt01`–`jt05`, `dc01`–`dc03`, `kt01`–`kt05`.
Switching one on for a word lets the font itself pick which letters to stretch.

## Results

### 1. Per-letter features in the DOM: rejected

`justify.justify_line()` (port of DigitalKhatt's HarfBuzz justifier) sets
`cvNN` values on single letters. Wrapping those letters in their own
`<span style="font-feature-settings: …">` **breaks letter joining in Chromium**
(see `img/page3-per-letter-spans-broken.png`): كفر و، يؤ منون، عذابـ…
Per-letter control can only be shown as SVG paths, not as browser text.

### 2. Per-word features in the DOM: works, pixel-exact

`justify.justify_words()` (port of DigitalKhatt's `oldmedina` DOM justifier)
assigns `jt`/`dc`/`kt` levels per word, computed at build time with HarfBuzz.
Each word is one span with one `font-feature-settings`, so joining is intact.

Chromium vs HarfBuzz, page 3, 15 lines at 40px:

- every word's width matches within **0.015px**
- every line lands within **0.06px** of the 656px target

Side by side with the real v1 runtime (Hafs, 24px): `img/page3-v1-vs-v2-chromium.png`.

### 3. Geometry

- Line width: **16400 font units** (= the DigitalKhatt page width). Their site
  uses 15628, but then ~37% of lines are wider than the line and have to shrink.
  At 16400, page 3 needs no shrinking and spaces stay near normal.
- Spaces may grow to 1.5× before letters stretch (`space_stretch=0.5`).
- Lines wider than the target: spaces tighten to 60%, then the font's
  `shr1`/`shrr` features per word, then a residual `scaleX` (rare).

## Not covered yet

- **Firefox**: Playwright's Firefox download is blocked in this workspace, so
  only Chromium was measured. Firefox also shapes with HarfBuzz, so similar
  results are expected, but it must be checked.
- **Safari**: CoreText ignores these custom features → fallback needed.
- Pages 1-2 (narrow centered lines), sura headers, basmala lines.
- Word count: the DigitalKhatt text joins some tokens differently from Tanzil
  (e.g. aya markers `۝١٣`); word indexes must still match the `words=` API.

## Files

- `src/db/v2/justify.py` — `justify_words()` (DOM), `justify_line()` (per-letter, for SVG), shrink step
- `src/db/v2/poc_page.py` — renders v1 vs v2 for a page as SVG (no browser)
- `src/db/v2/browser_check.py` — builds the HTML, measures it in Playwright (`--mode word|char`)
- `src/db/v2/render_svg.py` — glyph outlines → SVG
