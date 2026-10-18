# Highlighting words

`highlight` marks words in soft yellow, and `error` in soft red, on top of whatever is shown.
They take the same range format as [`words`](words.md).

<div class="qmh-example">
<quran-madina-html sura="2" aya="255" highlight="5-8" error="1"></quran-madina-html>
</div>

```html
<quran-madina-html sura="2" aya="255" highlight="5-8" error="1"></quran-madina-html>
```

## What the numbers count

They work in every kind of render:

| Render | Word 1 is |
|---|---|
| `sura` + `aya` | the verse's first word |
| with `words` | the same word as in `words` (the selection's own numbering) |
| a full `page` | the first word of the page's first verse |

```html
<quran-madina-html sura="1" aya="7" words="1-14" highlight="10-13" error="1-2"></quran-madina-html>
<quran-madina-html page="2" error="1-4"></quran-madina-html>
```

A range must fall inside what is shown. One that doesn't, or that is malformed, is ignored with
a console message; the text still renders. Where `highlight` and `error` overlap, `error` wins.

A basmala shown as the ﷽ ligature is split into its four words when a range marks only some
of them.

## Colours

The colours come from CSS custom properties, and switch to darker pairs with white text on dark
pages automatically. See [Styling and dark mode](styling.md).
