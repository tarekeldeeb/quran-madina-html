# Tag attributes

Attributes of `<quran-madina-html>`. Changing one after the page loads re-renders the tag.

| Attribute | Value | Default | Description |
|---|---|---|---|
| `page` | 1–604 (IndoPak 1–610) | | A full Mushaf page. Takes priority over `sura`/`aya`. [Guide](../guide/pages-and-verses.md#a-full-page) |
| `sura` | 1–114 | | The sura, with `aya`. |
| `aya` | `255` or `8-10` | | A verse or a range of verses. [Guide](../guide/pages-and-verses.md#a-verse-or-a-range) |
| `words` | `5`, `3-10` or `3:10` | | Show only these words, counted from the start of `aya`. Ignored with `page`. [Guide](../guide/words.md) |
| `highlight` | a word range | | Mark words soft yellow. Works with `page` too. [Guide](../guide/highlighting.md) |
| `error` | a word range | | Mark words soft red. Wins over `highlight`. [Guide](../guide/highlighting.md) |
| `letters` | `"1:3, 4:3-5 emerald blink"` | | Colour single letters inside words. [Guide](../guide/letters.md) |
| `headless` | `true` | off | Drop the header (sura name, copy and translate). |
| `notitle` | `true` | off | With `words`: hide the name of a sura the selection crosses into, keeping its frame. |
| `quotes` | `no` | quote marks | Drop the quote marks around an inline render. |
| `inline` | `no` | `auto` | Force the multiline layout even when the selection fits on one line. |

Word ranges are 1-based and include both ends. A malformed `words` value is ignored and the
verse renders whole; a malformed or out-of-range `highlight`, `error` or `letters` value is
ignored on its own. Each logs a console message.
