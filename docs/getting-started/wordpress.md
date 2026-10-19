# WordPress

The **Quran Madina Html** plugin adds a Quran block and a `[quran]` shortcode to any WordPress
site. No code needed.

![The Quran block in the editor, with its settings](../assets/img/wordpress-block.png)

## Install

1. Download the plugin:
   [quran-madina-html-wordpress.zip](https://github.com/tarekeldeeb/quran-madina-html/releases/latest/download/quran-madina-html-wordpress.zip)
   (from the latest GitHub release).
2. In WordPress, go to **Plugins → Add New Plugin → Upload Plugin**, choose the zip, and
   **Install Now**.
3. **Activate** it.

It needs WordPress 6.3 or later and PHP 7.4 or later.

## The Quran block

Add a **Quran** block (search for "Quran" or "قرآن" in the block inserter). Set it in the
block sidebar:

| Setting | Example | Shows |
|---|---|---|
| Page | `50` | a whole page; leave empty to show verses |
| Sura and Verses | `2` and `255`, or `2` and `8-10` | those verses |
| Only these words | `1-5` | only some words, counted from the first verse |
| Highlight | `5-8` | words marked yellow |
| Mistake | `3` | words marked red |
| Letters | `1:3, 4:3-5 emerald blink` | emphasised letters ([format](../guide/letters.md)) |
| Hide the header | on | only the Quran text, without the sura name, copy and translate |

The text shows live in the editor as you change them.

## The shortcode

In any post, page or text widget:

```text
[quran sura="2" aya="255"]
[quran page="1"]
[quran sura="2" aya="255" highlight="5-8" error="1"]
[quran sura="1" aya="2-4" letters="1:3, 4:3-5 emerald blink"]
[quran sura="1" aya="1" words="1-2"]
[quran sura="5" aya="1-2" headless="true"]
```

It takes every [tag attribute](../reference/attributes.md): `page`, `sura`, `aya`, `words`,
`highlight`, `error`, `letters`, `headless`, `notitle`, `quotes`, `inline`. A verse that fits
on one line shows inline, inside the sentence:

![Shortcodes on a post: an inline verse, highlighted words, emphasised letters](../assets/img/wordpress-post.png)

`[quran_madina ...]` works too, in case another plugin already uses `[quran]`.

## Settings

Under **Settings → Quran Madina**:

- **Print:** the 1441H or 1405H Madina Mushaf, or the 15-line IndoPak. One print for the
  whole site.
- **Font size:** in pixels, 16 by default.
- **Load the library from:** unpkg.com (the default, nothing to set up), or **this site**.

### Without outside requests

To load nothing from unpkg.com (for privacy, or a site that must work on a closed network):

1. Under **Settings → Quran Madina**, click **Copy to this site**. It downloads the library,
   its texts and fonts for all three prints (about 11 MB) into your uploads folder, once.
2. Choose **This site** under "Load the library from", and **Save**.

After a plugin update, copy it again: each plugin version loads its own library version. Until
you do, pages load from unpkg.com, and the settings page says so.

## Notes

- The library loads only on pages that show Quran text.
- Light and dark themes are detected from your theme's text colour; see
  [Styling and dark mode](../guide/styling.md). Your theme's CSS can change the colours with the
  [custom properties](../reference/css.md).
- Caching and optimisation plugins: exclude the `quran-madina-html` script from "combine" or
  "defer" options if the text doesn't appear. The library reads its settings from its own
  script tag.
- Uninstalling the plugin removes its settings and the copied library.
