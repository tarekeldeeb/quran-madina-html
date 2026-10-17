/// Render Quran pages like the printed Madina Mushaf in Flutter: a WebView wrapper around the
/// quran-madina-html web component.
library;

export 'src/page.dart'
    show QuranLoader, kDefaultCdn, kDefaultSrc, tagAttributes, attributeUpdates, buildPage;
export 'src/widget.dart' show QuranMadinaHtml;
