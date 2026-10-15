# v2.0 — design decisions

## Layouts

| | 1441H (default) | 1405H (option) |
|---|---|---|
| Font | DigitalKhatt New Madina (`hb/madina.otf`) | DigitalKhatt Old Madina (`hb/oldmadina.otf`) |
| License | OFL 1.1, no Reserved Font Name | OFL 1.1, no Reserved Font Name |
| Line breaks | DigitalKhatt `quran_text_madina.ts` (MIT) | DigitalKhatt `quran_text_old_madinah.ts` (MIT); same breaks as the v1 `Madina05` DB |
| Line width | 16200 font units | 16400 font units |

The two layouts break lines differently on ~37% of lines (5658 of 9046 lines
have the same word count).

## Text: Tanzil is the source

Tanzil stays the authoritative text. The DigitalKhatt texts are used **only
for line breaks**. Tanzil words are converted at build time to the encoding the
fonts expect (decomposed hamza with U+034F, no tatweel before dagger alef,
`۝` + digits for aya numbers, open tanween ࣰ ࣱ ࣲ derived from the next letter,
etc. — 55 patterns over the whole text, see the converter).

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
