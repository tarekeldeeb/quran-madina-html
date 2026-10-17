# quran_madina_flutter

Render Quran pages in Flutter that look like the printed Madina Mushaf — real, selectable text
with letters stretched like the print, no images. A thin WebView wrapper around the
[quran-madina-html](https://github.com/tarekeldeeb/quran-madina-html) web component, with the same
options as its React wrapper, released in lockstep with it.

```dart
import 'package:quran_madina_flutter/quran_madina_flutter.dart';

QuranMadinaHtml(page: 106)                                  // a full page
QuranMadinaHtml(sura: 2, aya: '255')                        // a verse
QuranMadinaHtml(sura: 1, aya: '1', words: '1:2')            // some words
QuranMadinaHtml(sura: 2, aya: '255', highlight: '5-8', error: '1')
QuranMadinaHtml(sura: 1, aya: '2-4', letters: '1:3, 4:3-5 emerald blink')
QuranMadinaHtml(page: 50, layout: 'IndoPak', fontSize: 22)
```

The widget sizes itself to the rendered text (or pass `height`), so it fits in a `ListView` or
`Column`.

## Install

From pub.dev:

```yaml
dependencies:
  quran_madina_flutter: ^2.1.0
```

Or straight from GitHub:

```yaml
dependencies:
  quran_madina_flutter:
    git:
      url: https://github.com/tarekeldeeb/quran-madina-html
      path: flutter
```

It uses [webview_flutter](https://pub.dev/packages/webview_flutter), so it runs on Android, iOS
and macOS. The library, its databases and fonts load from unpkg, so the app needs internet
access (on Android, the `INTERNET` permission) unless you self-host them (see `cdn`).

## Options

| Option | Type | Description |
|---|---|---|
| `page` | `int` | Full Mushaf page (1–604; IndoPak 1–610). Wins over `sura`/`aya`. |
| `sura`, `aya` | `int`, `String` | Sura (1–114) and aya or range, e.g. `'255'`, `'8-10'`. |
| `words` | `String` | 1-based word range, e.g. `'1:2'`, `'3-10'`, `'5'`. |
| `highlight` | `String` | Word range marked soft yellow. |
| `error` | `String` | Word range marked soft red (wins over `highlight`). |
| `letters` | `String` | Letters to emphasise inside words: `'1:3 crimson, 4:3-5 emerald blink'` (word:letters, optional colour — crimson by default — and optional `blink`). |
| `headless` | `bool` | Drop the header (sura name, copy/translate) and show only the text. |
| `quotes` | `String` | `'no'` drops the quote marks around inline renders. |
| `inline` | `String` | `'no'` forces the multiline layout. |
| `notitle` | `bool` | With `words` crossing into a new sura: hide its name, keep the frame. |
| `layout` | `String` | `'1441H'` (default), `'1405H'` or `'IndoPak'`. |
| `fontSize` | `num` | Font size in logical pixels (default 16). |
| `textColor` | `String` | CSS colour of the text, e.g. `'#ece6d6'` for a dark theme. Highlight, error and letter colours adapt to it. |
| `backgroundColor` | `String` | CSS colour behind the text (default transparent). |
| `height` | `double` | Fixed height instead of sizing to the text. |
| `onOpenUrl` | `void Function(String)` | Links the library opens (the translate buttons, to quran.com). Open them with `url_launcher`; ignored by default. |
| `src`, `cdn` | `String` | Library script URL and asset base URL (default: unpkg, latest 2.x). |

Changing `page`, `sura`, `aya`, `words`, `highlight`, `error`, `letters` and the other tag options
re-renders in place. Changing `layout`, `fontSize`, `textColor`, `backgroundColor`, `src` or
`cdn` reloads the WebView.

## Example

See [`example/lib/main.dart`](example/lib/main.dart).
