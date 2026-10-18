## 2.1.1

- Follows quran-madina-html 2.1.1.

## 2.1.0

- First release: `QuranMadinaFlutter` widget for the quran-madina-html web component, with the
  same options as the React wrapper (`page`, `sura`/`aya`, `words`, `highlight`, `error`,
  `letters`, `headless`, `quotes`, `inline`, `notitle`, `layout`, `fontSize`). Released in
  step with quran-madina-html.
- Android, iOS and macOS: renders in the platform's WebView. Web: renders straight in the page.
- Offline: `dart run quran_madina_flutter:bundle` copies the library into the app's assets;
  `bundled: true` loads it from there.
