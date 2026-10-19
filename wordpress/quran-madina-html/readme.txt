=== Quran Madina Html ===
Contributors: tarekeldeeb
Tags: quran, islam, arabic, mushaf, shortcode
Requires at least: 6.3
Tested up to: 7.1
Requires PHP: 7.4
Stable tag: 2.1.1
License: Waqf General Public License 2.0
License URI: https://github.com/ojuba-org/waqf/tree/master/2.0

Quran pages that look like the printed Madina Mushaf, as real text: a Quran block and a [quran] shortcode.

== Description ==

Show Quran text that looks like the printed Madina Mushaf, with the same line breaks and lines justified by stretching the letters, as real text that can be selected, copied and searched. No images.

* **A Quran block**: pick a sura and verses, or a whole page, in the block settings; the text shows live in the editor.
* **A shortcode** for any post, page or widget: `[quran sura="2" aya="255"]`.
* **Highlight words** in yellow, **mark mistakes** in red, and **emphasise single letters** in a colour, optionally blinking. Useful for teaching and for memorisation.
* **Three prints**: the 1441H and 1405H Madina Mushaf and the 15-line IndoPak, at any size.
* **Light and dark** themes are detected automatically.
* **Private by choice**: load the library from unpkg.com, or copy it to your own site once and load nothing from outside.

Built on [quran-madina-html](https://github.com/tarekeldeeb/quran-madina-html). [Documentation](https://tarekeldeeb.github.io/quran-madina-html/docs/getting-started/wordpress/) · [Live demo](https://tarekeldeeb.github.io/quran-madina-html/demo/index.html).

= Shortcode examples =

* `[quran sura="2" aya="255"]` a verse
* `[quran sura="2" aya="8-10"]` a range of verses
* `[quran page="1"]` a whole page
* `[quran sura="1" aya="1" words="1-2"]` only some words
* `[quran sura="2" aya="255" highlight="5-8" error="1"]` highlighted words and a mistake
* `[quran sura="1" aya="2-4" letters="1:3, 4:3-5 emerald blink"]` emphasised letters
* `[quran sura="5" aya="1-2" headless="true"]` without the header

A verse that fits on one line shows inline, inside your sentence.

== Installation ==

1. Install the plugin from Plugins → Add New, or upload the zip from the [GitHub releases](https://github.com/tarekeldeeb/quran-madina-html/releases).
2. Activate it.
3. Add a Quran block to a post, or type a shortcode.
4. Optionally, under Settings → Quran Madina, choose the print and the font size, and copy the library to your site.

== Frequently Asked Questions ==

= Does it load anything from outside my site? =

By default the library and its texts load from unpkg.com, a public CDN. Under Settings → Quran Madina, "Copy to this site" downloads them once (about 11 MB) into your uploads folder; choose "This site" and nothing loads from outside.

= Which Quran text does it use? =

The Uthmani text from the Tanzil Project, laid out like the printed Madina Mushaf, with DigitalKhatt fonts.

= Can I use different prints on one page? =

No: the print and the size are set once for the whole site, under Settings → Quran Madina.

== Screenshots ==

1. The Quran block in the editor, with its settings.
2. Verses with highlighted words and emphasised letters on a post.

== Changelog ==

= 2.1.1 =
* First release: the Quran block, the [quran] shortcode, settings for the print and size, and an optional copy of the library on your site.
