# v2.0 — Phase 0 audit: DigitalKhatt New Madina

Goal of v2.0: replace build-time tatweel insertion with real glyph stretching
(HarfBuzz shaping + the font's own stretch features), to look closer to the
printed Madina Mushaf.

> **Update (Phase 1):** the pilot font is now *DigitalKhatt Old Madina*, which
> matches our 1405H layout and has whole-word stretch features that work in
> the browser. See `phase1-poc.md`.

## Font first considered for the pilot

| | |
|---|---|
| Font | **DigitalKhatt New Madina** (`hb/madina.otf`, CFF2) |
| Source | `github.com/DigitalKhatt/digitalkhatt.org` @ `4213fab` (2026-01-14), `ClientApp/src/assets/fonts/hb/madina.otf` |
| Copyright | © 2020-2024 Amine Anane, © 2024 Tarteel Inc. |
| License | **SIL OFL 1.1** — fine to bundle in this repo/npm package (keep the license text next to it) |
| Units/em | 1000, 3735 glyphs |

A sibling build, `coretext/DigitalKhattV2.ttf` (TrueType, 1219 glyphs, same
OFL license), is published for Apple CoreText. It lacks `cv01`–`cv18` and only
offers `jalt` with fixed `.expa` alternates, so Safari will need a fallback.

### Not chosen

`digitalkhatt.otf` ("DigitalKhatt Madina Quranic", V1) is the one with
**variable axes `LTAT` / `RTAT` (−20…20)**, which the TUGboat paper uses.
It is **AGPL-3.0 with a font-embedding exception**, and its design follows the
older layout. Usable for experiments, but a licensing question for an ISC
library, so it is not the pilot font.

## Key finding: New Madina stretches through *features*, not axes

The New Madina font has **no `fvar` table**. Stretching is done with GSUB
alternate lookups selected by an integer feature value:

| Feature | Role (observed) | Max value |
|---|---|---|
| `cv01` | kashida-like elongation of a joined letter pair | 12 |
| `cv02` | secondary elongation (finals / the left side) | 12 |
| `cv03`, `cv10`–`cv18` | single alternates (special forms) | 1 |
| `jalt` | justification alternates (wide final forms) | 1 |
| `shr1`, `shr2` / GPOS `shrr` | shrinking | — |

Measured with uharfbuzz (font units, feature applied to the whole word):

| Word | natural | cv01=2 | cv01=4 | cv01=6 | cv02=6 | cv02=12 |
|---|---|---|---|---|---|---|
| ٱلْحَمْدُ | 1755 | 2390 | 2928 | 3464 | 2495 | 3233 |
| رَبِّ | 1120 | 1360 | 1606 | 1853 | 1120 | 1120 |
| ٱلْعَٰلَمِينَ | 2473 | 4222 | 5746 | 7144 | 3951 | 5430 |
| لِلَّهِ | 780 | 780 | 780 | 780 | 780 | 780 |

Takeaways:
- Stretch is **discrete but fine-grained** (≈ 120–250 units per step), so
  lines can be fitted closely.
- Applying a value to a whole word stretches *every* eligible pair and is not
  monotonic past some levels — values must target specific characters, as the
  reference algorithm does.
- No `.notdef` for standard Uthmani Unicode text (Tanzil-style) in the samples.

## Reference algorithm (MIT)

`digitalkhatt.org` (MIT license) ships a complete TypeScript justifier for this
font: `ClientApp/src/app/components/hbmedina/just.service.ts` (~1.1k lines).
It runs on HarfBuzz-WASM and outputs, per line, a map of
**character index → list of `{feature, value}`**, using prioritized rules
(final alternates, hah/kashida pairs, beh-beh, reh, kaf, then generic pairs)
with level caps. That is exactly the shape a precomputed JSON DB needs. Plan:
port it to Python in `src/db/` instead of reinventing it.

## Current repo pipeline (v1.0.1) — what changes

- `src/db/build_db.py` measures widths in headless Chrome, computes per-line
  `s` (scaleX), and inserts tatweels (`kashidas_needed` / `place_kashidas`).
- JSON contract: `suras[].ayas[].r[] = {l, t, s}`; runtime applies `scaleX`.
- v2 adds a new, optional per-part field for feature runs; `s` remains as a
  small residual correction and as the v1 fallback.

## Risks confirmed

1. **Safari/CoreText** cannot use `cv01`/`cv02` from the CoreText build →
   fallback (tatweel DB, or SVG paths) on WebKit.
2. **Per-character features in the browser**: CSS `font-feature-settings` is
   per element. Applying it to a sub-word `<span>` may break Arabic joining in
   some engines. Must be tested in Chrome and Firefox before committing to the
   DOM approach (Phase 4). Fallback: HarfBuzz-WASM → SVG.
3. Width parity: the build shapes with uharfbuzz, the browser shapes with its
   own HarfBuzz build; small differences are absorbed by the residual `s`.
