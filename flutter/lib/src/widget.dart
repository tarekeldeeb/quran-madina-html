import 'package:flutter/widgets.dart';

import 'page.dart';
import 'view_io.dart' if (dart.library.js_interop) 'view_web.dart';

/// Renders Quran text like the printed Madina Mushaf: one `<quran-madina-html>` tag, in the
/// platform's own WebView on Android, iOS and macOS, and straight in the page on the web. Same
/// options as the React wrapper.
///
/// ```dart
/// QuranMadinaFlutter(page: 106)
/// QuranMadinaFlutter(sura: 2, aya: '255', highlight: '5-8', error: '1')
/// QuranMadinaFlutter(sura: 1, aya: '2-4', letters: '1:3, 4:3-5 emerald blink')
/// ```
///
/// `page` and `sura`/`aya` are mutually exclusive (`page` wins if both are given). Changing a
/// tag option re-renders in place; changing a loader option ([layout], [fontSize], [src], [cdn],
/// [textColor], [backgroundColor]) reloads the WebView (on the web,
/// the first widget's loader options apply to the whole page). The widget takes the height of the
/// rendered text unless [height] is given.
class QuranMadinaFlutter extends StatefulWidget {
  const QuranMadinaFlutter({
    super.key,
    this.page,
    this.sura,
    this.aya,
    this.words,
    this.highlight,
    this.error,
    this.letters,
    this.headless,
    this.quotes,
    this.inline,
    this.notitle,
    this.layout,
    this.fontSize,
    this.src = kDefaultSrc,
    this.cdn = kDefaultCdn,
    this.textColor,
    this.backgroundColor,
    this.height,
    this.onOpenUrl,
    this.bundled = false,
  });

  /// Full Mushaf page (1-604; IndoPak 1-610).
  final int? page;

  /// Sura number (1-114), with [aya].
  final int? sura;

  /// Aya number or range, e.g. '255' or '8-10'.
  final String? aya;

  /// Restrict to a 1-based word range, e.g. '1:2', '3-10' or '5'.
  final String? words;

  /// 1-based word range to mark soft yellow (same format as [words]).
  final String? highlight;

  /// 1-based word range to mark soft red; wins over [highlight] on overlap.
  final String? error;

  /// Letters to emphasise inside words: "word:letters colour blink" groups, e.g.
  /// '1:3, 4:3-5 emerald blink'. Colour optional (crimson by default), blink optional.
  final String? letters;

  /// Drop the header (sura name, copy/translate icons) and render only the text.
  final bool? headless;

  /// 'no' drops the quote marks of inline (single-line) renders.
  final String? quotes;

  /// 'no' forces the multiline layout even when the selection fits one line.
  final String? inline;

  /// With [words] crossing into a new sura: hide its name, keep the decorated line.
  final bool? notitle;

  /// Layout: '1441H' (default), '1405H' or 'IndoPak'.
  final String? layout;

  /// Font size in logical pixels (default 16). Any size works.
  final num? fontSize;

  /// URL of the library script (default: latest 2.x on unpkg).
  final String src;

  /// Base URL for the library's CSS, databases and fonts (self-host for offline use).
  final String cdn;

  /// CSS colour of the text, e.g. '#ece6d6' on a dark page (default near-black).
  final String? textColor;

  /// CSS colour behind the text (default transparent).
  final String? backgroundColor;

  /// Fixed height; by default the widget takes the height of the rendered text.
  final double? height;

  /// Called with links the library opens (the translate buttons, to quran.com). Open them with
  /// url_launcher, for example; by default they are ignored. Not used on the web, where the
  /// browser opens them in a new tab.
  final void Function(String url)? onOpenUrl;

  /// Load the library, its databases and fonts from the app's own assets instead of unpkg, so
  /// the text renders offline. Copy them in once with `dart run quran_madina_flutter:bundle` (see
  /// the README); [src] and [cdn] are then ignored.
  final bool bundled;

  Map<String, String> get _attributes => tagAttributes(
        page: page,
        sura: sura,
        aya: aya,
        words: words,
        highlight: highlight,
        error: error,
        letters: letters,
        headless: headless,
        quotes: quotes,
        inline: inline,
        notitle: notitle,
      );

  QuranLoader get _loader => QuranLoader(
        src: bundled ? kBundledSrc : src,
        cdn: bundled ? kBundledCdn : cdn,
        layout: layout,
        fontSize: fontSize,
        textColor: textColor,
        backgroundColor: backgroundColor,
      );

  @override
  State<QuranMadinaFlutter> createState() => createQuranState();
}

/// The tag attributes of [w] (for the platform views; not exported).
Map<String, String> attributesOf(QuranMadinaFlutter w) => w._attributes;

/// The loader settings of [w] (for the platform views; not exported).
QuranLoader loaderOf(QuranMadinaFlutter w) => w._loader;
