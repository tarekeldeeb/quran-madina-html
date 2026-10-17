import 'dart:convert';

/// The library script loaded by default (latest 2.x on unpkg).
const String kDefaultSrc = 'https://unpkg.com/quran-madina-html@2';

/// Base URL the library fetches its CSS, databases and fonts from by default.
const String kDefaultCdn = 'https://unpkg.com/quran-madina-html@2/';

/// Where `dart run quran_madina_flutter:bundle` puts the library's files in the app (an asset
/// directory, declared in the app's pubspec).
const String kBundleDir = 'assets/quran_madina';

/// Placeholder base of a bundled loader; each platform swaps in where it serves [kBundleDir]
/// from (a local server in the WebView, the app's asset URL on the web).
const String kBundledCdn = 'qmh-bundle:/';

/// The library script inside the bundle.
const String kBundledSrc = '${kBundledCdn}dist/quran-madina-html.min.js';

/// The name of the JavaScript channel the page reports to the widget on.
const String kChannel = 'QMH';

/// Loader settings. They configure the library itself, so changing one reloads the page.
class QuranLoader {
  const QuranLoader({
    this.src = kDefaultSrc,
    this.cdn = kDefaultCdn,
    this.layout,
    this.fontSize,
    this.textColor,
    this.backgroundColor,
  });

  /// URL of the library script.
  final String src;

  /// Base URL for the CSS, databases and fonts (self-host it for offline apps).
  final String cdn;

  /// `data-layout`: "1441H" (default), "1405H" or "IndoPak".
  final String? layout;

  /// `data-font-size` in logical pixels (default 16). Any size works.
  final num? fontSize;

  /// CSS colour of the text (default near-black). A light colour makes the library pick its
  /// dark-page shades for highlight/error/letters.
  final String? textColor;

  /// CSS colour behind the text (default transparent, so the Flutter background shows).
  final String? backgroundColor;

  /// Whether this loader reads the app's bundled files (see [kBundleDir]).
  bool get bundled => cdn == kBundledCdn;

  /// This loader with the bundle placeholder replaced by [base], the URL [kBundleDir] is served
  /// at (ending in '/'). Loaders that don't use the bundle come back unchanged.
  QuranLoader resolveBundle(String base) {
    String swap(String url) =>
        url.startsWith(kBundledCdn) ? base + url.substring(kBundledCdn.length) : url;
    return QuranLoader(
      src: swap(src),
      cdn: swap(cdn),
      layout: layout,
      fontSize: fontSize,
      textColor: textColor,
      backgroundColor: backgroundColor,
    );
  }

  @override
  bool operator ==(Object other) =>
      other is QuranLoader &&
      other.src == src &&
      other.cdn == cdn &&
      other.layout == layout &&
      other.fontSize == fontSize &&
      other.textColor == textColor &&
      other.backgroundColor == backgroundColor;

  @override
  int get hashCode => Object.hash(src, cdn, layout, fontSize, textColor, backgroundColor);
}

/// The `<quran-madina-html>` attributes for the given options, exactly as the React wrapper sets
/// them: `page` wins over `sura`/`aya`, booleans become empty attributes, and a null, false or
/// empty value is left out. Values are the attribute strings; absent keys mean "no attribute".
Map<String, String> tagAttributes({
  Object? page,
  Object? sura,
  Object? aya,
  String? words,
  String? highlight,
  String? error,
  String? letters,
  bool? headless,
  String? quotes,
  String? inline,
  bool? notitle,
}) {
  final out = <String, String>{};
  void set(String key, Object? value) {
    if (value == null || value == false || value == '') return;
    out[key] = value == true ? '' : value.toString();
  }

  if (page != null && page != '') {
    set('page', page);
  } else {
    set('sura', sura);
    set('aya', aya);
  }
  set('words', words);
  set('highlight', highlight);
  set('error', error);
  set('letters', letters);
  set('headless', headless);
  set('quotes', quotes);
  set('inline', inline);
  set('notitle', notitle);
  return out;
}

/// The attribute changes that turn [from] into [to]: new or changed values, and null for each
/// attribute to remove. The page applies them with `qmhSet(...)` without reloading.
Map<String, String?> attributeUpdates(Map<String, String> from, Map<String, String> to) {
  final out = <String, String?>{};
  to.forEach((k, v) {
    if (from[k] != v) out[k] = v;
  });
  for (final k in from.keys) {
    if (!to.containsKey(k)) out[k] = null;
  }
  return out;
}

/// The JavaScript call that applies [updates] to the tag on the page.
String updateScript(Map<String, String?> updates) => 'qmhSet(${jsonEncode(updates)});';

String _escape(String s) => const HtmlEscape(HtmlEscapeMode.attribute).convert(s);

/// The page the WebView loads: the library script and one `<quran-madina-html>` tag. The page
/// reports its height (so the widget can size itself) and any link the library opens (the
/// translate buttons) on the [kChannel] JavaScript channel.
String buildPage(QuranLoader loader, Map<String, String> attributes) {
  final script = StringBuffer('<script src="${_escape(loader.src)}" data-cdn="${_escape(loader.cdn)}"');
  if (loader.layout != null) script.write(' data-layout="${_escape(loader.layout!)}"');
  if (loader.fontSize != null) script.write(' data-font-size="${loader.fontSize}"');
  script.write('></script>');
  final attrs = attributes.entries
      .map((e) => e.value.isEmpty ? ' ${e.key}' : ' ${e.key}="${_escape(e.value)}"')
      .join();
  final color = _escape(loader.textColor ?? '#20201d');
  final background = _escape(loader.backgroundColor ?? 'transparent');
  return '''<!DOCTYPE html>
<html dir="rtl" lang="ar"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
$script
<style>
  html, body { margin: 0; padding: 0; background: $background; color: $color; }
  body { display: flow-root; }
</style>
</head><body>
<quran-madina-html id="qmh"$attrs></quran-madina-html>
<script>
  function qmhPost(kind, value) {
    try { $kChannel.postMessage(JSON.stringify({kind: kind, value: value})); } catch (e) {}
  }
  function qmhSet(attrs) {
    var tag = document.getElementById("qmh");
    Object.keys(attrs).forEach(function (k) {
      if (attrs[k] === null) tag.removeAttribute(k); else tag.setAttribute(k, attrs[k]);
    });
  }
  function qmhReport() {
    qmhPost("height", Math.ceil(document.body.getBoundingClientRect().height));
  }
  window.open = function (url) { qmhPost("open", String(url)); return null; };
  new ResizeObserver(qmhReport).observe(document.body);
  window.addEventListener("load", qmhReport);
</script>
</body></html>''';
}
