/// Render Quran pages like the printed Madina Mushaf in Flutter: the quran-madina-html web
/// component in the platform's WebView (Android, iOS, macOS) or straight in the page (web),
/// online from unpkg or offline from the app's bundled assets.
library;

export 'src/page.dart'
    show
        QuranLoader,
        QuranAyaAction,
        QuranAyaSelection,
        kBundleDir,
        kBundledCdn,
        kBundledSrc,
        kDefaultCdn,
        kDefaultSrc,
        tagAttributes,
        attributeUpdates,
        buildPage;
export 'src/version.dart' show kLibraryVersion;
export 'src/widget.dart' show QuranMadinaFlutter;
