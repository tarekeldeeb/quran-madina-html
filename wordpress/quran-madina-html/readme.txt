=== Quran Madina Html ===
Contributors: tarekeldeeb
Tags: quran, islam, arabic, mushaf, shortcode
Requires at least: 6.3
Tested up to: 7.1
Requires PHP: 7.4
Stable tag: 2.1.4
License: GPLv2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html

Quran pages that look like the printed Madina Mushaf, as real text: a Quran block and a [quran] shortcode.

== Description ==

Show Quran text that looks like the printed Madina Mushaf, with the same line breaks and lines justified by stretching the letters, as real text that can be selected, copied and searched. No images.

* **A Quran block**: pick a sura and verses, or a whole page, in the block settings; the text shows live in the editor.
* **A shortcode** for any post, page or widget: `[quran sura="2" aya="255"]`.
* **Highlight words** in yellow, **mark mistakes** in red, and **emphasise single letters** in a colour, optionally blinking. Useful for teaching and for memorisation.
* **Three prints**: the 1441H and 1405H Madina Mushaf and the 15-line IndoPak, at any size.
* **Light and dark** themes are detected automatically.
* **Nothing from outside**: the library, the Quran text and the fonts all come with the plugin. No CDN, no tracking.

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

= License =

The plugin, including its copy of the quran-madina-html library, is dual licensed: GPLv2 or later, or the ["Waqf" General Public License 2.0](https://github.com/ojuba-org/waqf/tree/master/2.0), at your choice. Third-party parts, listed in LICENSE.txt:

* Fonts: modified [DigitalKhatt](https://github.com/DigitalKhatt/digitalkhatt.org) fonts by Amine Anane, SIL Open Font License 1.1.
* Quran text: [Tanzil Project](https://tanzil.net) (Uthmani 1.1), Creative Commons Attribution 3.0, distributed verbatim as its terms require.
* 1441H line breaks: King Fahd Glorious Quran Printing Complex page data, from the quran-qcf4 package (MIT).

= Source code =

The plugin and the library are developed in the open at [github.com/tarekeldeeb/quran-madina-html](https://github.com/tarekeldeeb/quran-madina-html): the plugin in `wordpress/quran-madina-html`, the library script in `src/`, and the page data's generator in `src/db/`. The script in `library/dist/` is the readable, unminified build of `src/`; `wordpress/build.sh` assembles the plugin.

= External links =

The plugin sends no requests to other sites. Two links open other sites only when a visitor clicks them: the translate button above a verse opens that verse on [quran.com](https://quran.com) ([privacy policy](https://quran.com/privacy)), and the settings page links to this plugin's documentation on GitHub Pages.

== Installation ==

1. Install the plugin from Plugins → Add New, or upload the zip from the [GitHub releases](https://github.com/tarekeldeeb/quran-madina-html/releases).
2. Activate it.
3. Add a Quran block to a post, or type a shortcode.
4. Optionally, under Settings → Quran Madina, choose the print and the font size.

== Frequently Asked Questions ==

= Does it load anything from outside my site? =

No. The library, the Quran text and the fonts for all three prints come with the plugin and load from your site, only on pages that show Quran text.

= Which Quran text does it use? =

The Uthmani text from the Tanzil Project, laid out like the printed Madina Mushaf, with DigitalKhatt fonts.

= Can I use different prints on one page? =

No: the print and the size are set once for the whole site, under Settings → Quran Madina.

== Screenshots ==

1. The Quran block in the editor, with its settings.
2. Verses with highlighted words and emphasised letters on a post.

== Changelog ==

= 2.1.4 =
* The library now comes with the plugin, so nothing loads from unpkg.com. The "Copy to this site" setting is gone; uninstalling removes a copy an earlier version saved in the uploads folder.
* The plugin, including its library copy, is dual licensed: GPLv2 or later, or Waqf GPL 2.0.

= 2.1.3 =
* Follows quran-madina-html 2.1.3.

= 2.1.1 =
* First release on GitHub: the Quran block, the [quran] shortcode, and settings for the print and size.
