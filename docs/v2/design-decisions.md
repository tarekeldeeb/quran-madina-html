# v2.0 — design decisions

## Layouts

| | 1441H (default) | 1405H (option) | IndoPak 15-line (option) |
|---|---|---|---|
| Font | DigitalKhatt New Madina (`hb/madina.otf`) | DigitalKhatt Old Madina (`hb/oldmadina.otf`) | DigitalKhatt IndoPak (`hb/indopak.otf`) |
| License | OFL 1.1, no Reserved Font Name | OFL 1.1, no Reserved Font Name | OFL 1.1, no Reserved Font Name |
| Line breaks | DigitalKhatt `quran_text_madina.ts` (MIT) | DigitalKhatt `quran_text_old_madinah.ts` (MIT); same breaks as the v1 `Madina05` DB | DigitalKhatt `quran_text_indopak_15.ts` (MIT) |
| Line width | 16200 font units | 16400 font units | 16400 font units |

IndoPak was added at the user's request; its text and pause marks will need
their own check against Tanzil (IndoPak spelling conventions differ).

The two layouts break lines differently on ~37% of lines (5658 of 9046 lines
have the same word count).

## Text: Tanzil is the source

Tanzil stays the authoritative text. The DigitalKhatt texts are used **only
for line breaks**. Tanzil words are converted at build time to the encoding the
fonts expect (`src/db/v2/tanzil_encoding.py`): decomposed hamza with U+034F,
no tatweel before dagger alef, ى → ي where it carries a vowel or follows kasra,
`۝` + digits for aya numbers, ۞/۩ attached to their word, and the open tanween
ࣰ ࣱ ࣲ derived by the tajweed rule (open before idgham/ikhfa letters, stacked
before throat letters and hamzat wasl, plain vowel before the iqlab meem).

Checked over the whole Quran (`src/db/v2/validate_encoding.py`):

| Reference | Identical tokens | Pause marks only | Other |
|---|---|---|---|
| 1405H text | 84,112 / 84,116 | 1 | 3 (DigitalKhatt spacing quirks around ۞ ۩, v1 bug below) |
| 1441H text | 83,764 / 84,116 | **352** | 1 (v1 bug below) |

- Every *letter* of Tanzil matches both prints. The 1441H print revised 352
  **pause marks (waqf)**; Tanzil keeps the earlier ones. **Decision:** the
  1441H layout uses the 1441H print's pause marks
  (`tanzil_encoding.apply_pause_marks`, aligned on text without marks; letters
  and vowels always stay Tanzil's). Result: 84,116 / 84,116 tokens identical.
- **v1 bug found:** page 254 (13:37) — the v1 DB has no ﴿٣٧﴾ marker and puts
  "مَا" on line 7 instead of line 6.

## Stretching letters in browser text: position features in the font

Per-letter stretching (DigitalKhatt's `cv01`/`cv02`/`cv10`–`cv18`) cannot be
done with nested spans: joining breaks (`img/page3-per-letter-spans-broken.png`),
and even with ZWJ at span edges kerning and cursive attachment are lost
(words drift up to 12px at 40px).

So the fonts are extended (`src/db/v2/font_patch.py`):

1. At build time HarfBuzz justifies each line with per-letter features
   (`justify.justify_line`), exactly like DigitalKhatt's own justifier.
2. Stretching never changes a word's glyph count (verified on all 19,482
   stretched words of 1441H and 25,204 of 1405H), so each stretched word is
   recorded as "glyph at position k becomes glyph g′".
3. The font gets one AlternateSubst lookup (g → its stretched variants) and
   features `jp01`…`jpNN`: `jpKK` swaps the glyph at position KK of the word,
   the CSS value picking the variant. These lookups run after all others, so
   GPOS (kerning, cursive, marks) sees exactly HarfBuzz's glyphs.
4. Each word is one span: `<span style='font-feature-settings: "jp04" 3'>…</span>`.

Results (Chromium, 40px): every word within **0.015px** of HarfBuzz, every
line within **0.08px** of its target, on 1441H pages 3, 50, 300 and 1405H page 3.
See `img/1441h-page3-jp-chromium.png`.

Shrinking (lines wider than the target) uses the fonts' own `shr1`/`shrr`
as plain per-word CSS features, after tightening spaces.

The patched fonts are renamed (OFL good practice) and rebuilt with the DB,
since the alternate lists depend on the corpus.

## Open

- Firefox (not installable in this workspace) and Safari/CoreText: untested
  with custom `jpNN` features. A tatweel DB remains the fallback.
- Aya marker collides with the next word on tight lines (1441H p3 l8):
  give aya spaces a higher minimum when shrinking.
- Pages 1-2, sura titles, basmala lines.

## Runtime (Phase 4)

`<script src=".../quran-madina-html.js" data-layout="1441H">` (default `1441H`,
or `1405H`) loads `assets/db/v2/Madina-<layout>.json` and its woff2 font. A page
that sets `data-font` without `data-layout` keeps the v1 DBs.

- Every v2 line gets its row from `lines[page][line]`: width (em), centering for
  titles/basmala/narrow lines, `scaleX` for the few shrunk lines.
- Words are spans with their `font-feature-settings`; spaces are inline-block
  spans of the exact width. The words=, highlight=, error= and spacer paths all
  use the same builder (`v2AppendWords`), so selections keep the page geometry.
- Copy/paste maps the font encoding back to standard Uthmani (CGJ removed,
  hamza recomposed, open tanween → regular).
- No font-size anchors or interpolation: everything is in em.

Screenshot: `img/v2-runtime-chromium.png` (page 3, highlight/error, words=,
inline quote, page 1).

The v2 DBs in `assets/db/v2` are currently built from the Tanzil text recovered
from the v1 DB (tanzil.net is unreachable from the build sandbox); rebuild with
`--tanzil` from the real download before release.

## Fitting overfull lines (hybrid)

With DigitalKhatt's line width, a third of 1441H lines (a fifth of 1405H) are
wider than the line, mostly on the later pages where short ayas bring many
markers. Options considered: squeeze lines (DigitalKhatt site: down to ~75%),
per-page font size, wider lines, or a hybrid. **Decision: hybrid.**

- The text is set 8% smaller than the line's nominal em (`z = 0.92`, one factor
  for the whole mushaf so the size never jumps between pages; `--page-scale page`
  gives per-page factors instead), and line height compensates so the page keeps
  its proportions.
- Overfull lines then use the fonts' shrink features (`shr1`, and `shrr` away
  from aya numbers), and only the remainder is squeezed with scaleX.

| | lines squeezed | squeezed below 95% | worst |
|---|---|---|---|
| 1441H before | 2907 (33%) | 1616 | 74% |
| 1441H hybrid | 993 (11%) | 389 | 81% |
| 1405H hybrid | 575 (6.5%) | 206 | 82% |
