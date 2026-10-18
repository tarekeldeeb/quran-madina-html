# Flutter

[![pub package](https://img.shields.io/pub/v/quran_madina_flutter.svg)](https://pub.dev/packages/quran_madina_flutter)

[`quran_madina_flutter`](https://pub.dev/packages/quran_madina_flutter) is a widget that wraps
the `<quran-madina-html>` tag. It has the same options as the tag and the React component, and
is released together with the library, under the same version number.

!!! tip "Try it"
    The [example app](https://github.com/tarekeldeeb/quran-madina-html/tree/main/flutter/example),
    built for the web, runs live at <https://tarekeldeeb.github.io/quran-madina-html/flutter/>.

```dart
import 'package:quran_madina_flutter/quran_madina_flutter.dart';

QuranMadinaFlutter(page: 106)                                  // a full page
QuranMadinaFlutter(sura: 2, aya: '255')                        // a verse
QuranMadinaFlutter(sura: 1, aya: '1', words: '1:2')            // some words
QuranMadinaFlutter(sura: 2, aya: '255', highlight: '5-8', error: '1')
QuranMadinaFlutter(sura: 1, aya: '2-4', letters: '1:3, 4:3-5 emerald blink')
QuranMadinaFlutter(page: 50, layout: 'IndoPak', fontSize: 22)
QuranMadinaFlutter(page: 106, bundled: true)                   // offline, from the app's assets
```

The widget sizes itself to the rendered text, so it fits in a `ListView` or `Column`. You can
also pass `height` to fix it.

## Install

```yaml
dependencies:
  quran_madina_flutter: ^2.1.0
```

## Platforms

| Platform | How it renders |
|---|---|
| Android | The system WebView (via [webview_flutter](https://pub.dev/packages/webview_flutter)) |
| iOS, macOS | WKWebView, the engine Safari uses (via webview_flutter) |
| Web | No WebView: the `<quran-madina-html>` tag goes straight into the page |

Each widget on Android, iOS and macOS is its own WebView, so use one or a few per screen. For a
long passage, render it in one widget (`sura: 2, aya: '1-20'`) rather than one widget per verse.

On the web, the library reads `layout`, `fontSize` and its URLs once for the whole page, so the
first widget's values apply to every widget. The translate links open in a new browser tab.
If your `web/index.html` already loads the library script, the widget uses it.

## Online or offline

By default the library, its databases and fonts load from unpkg, so the app needs internet
access. On Android, the release build needs the `INTERNET` permission.

To work offline, copy the library into your app once, from the app's folder:

```bash
dart run quran_madina_flutter:bundle                     # the 1441H layout (about 4 MB)
dart run quran_madina_flutter:bundle --layouts 1441H,IndoPak   # about 4 MB per layout
```

The command writes `assets/quran_madina/` and prints the asset folders to add to your
`pubspec.yaml`:

```yaml
flutter:
  assets:
    - assets/quran_madina/assets/db/v2/
    - assets/quran_madina/assets/db/v2/Madina-1441H/
    - assets/quran_madina/assets/img/
    - assets/quran_madina/dist/
```

Then pass `bundled: true`:

```dart
QuranMadinaFlutter(page: 106, bundled: true)
```

Run the command again after upgrading this package, so the files match its version. It
downloads the matching library version from npm. `--version` picks another version, and
`--from <folder>` copies from a built checkout of quran-madina-html instead.

On the web, the bundled files are served with the app's own assets, with no other setup.

On Android, iOS and macOS, a WebView can't read Flutter assets directly, so the widget serves
them to it from a small local server on `127.0.0.1`. Allow that connection once per platform:

**Android:** add `android/app/src/main/res/xml/network_security_config.xml`:

```xml
<network-security-config>
  <domain-config cleartextTrafficPermitted="true">
    <domain includeSubdomains="false">127.0.0.1</domain>
  </domain-config>
</network-security-config>
```

Point to it in `AndroidManifest.xml`, and keep the `INTERNET` permission. The local server
needs it, even offline.

```xml
<uses-permission android:name="android.permission.INTERNET"/>
<application android:networkSecurityConfig="@xml/network_security_config" ...>
```

**iOS and macOS:** in `Info.plist`:

```xml
<key>NSAppTransportSecurity</key>
<dict>
  <key>NSAllowsLocalNetworking</key>
  <true/>
</dict>
```

On macOS, also add `com.apple.security.network.server` and `com.apple.security.network.client`
to `macos/Runner/DebugProfile.entitlements` and `Release.entitlements`.

## Options

| Option | Type | Description |
|---|---|---|
| `page` | `int` | Full Mushaf page (1–604; IndoPak 1–610). Wins over `sura`/`aya`. |
| `sura`, `aya` | `int`, `String` | Sura (1–114) and aya or range, e.g. `'255'`, `'8-10'`. |
| `words` | `String` | 1-based word range, e.g. `'1:2'`, `'3-10'`, `'5'`. |
| `highlight` | `String` | Word range marked soft yellow. |
| `error` | `String` | Word range marked soft red (wins over `highlight`). |
| `letters` | `String` | Letters to emphasise inside words: `'1:3 crimson, 4:3-5 emerald blink'`. Each group is word:letters, then an optional colour (crimson by default), then an optional `blink`. |
| `headless` | `bool` | Drop the header (sura name, copy/translate) and show only the text. |
| `quotes` | `String` | `'no'` drops the quote marks around inline renders. |
| `inline` | `String` | `'no'` forces the multiline layout. |
| `notitle` | `bool` | With `words` crossing into a new sura: hide its name, keep the frame. |
| `layout` | `String` | `'1441H'` (default), `'1405H'` or `'IndoPak'`. |
| `fontSize` | `num` | Font size in logical pixels (default 16). |
| `textColor` | `String` | CSS colour of the text, e.g. `'#ece6d6'` for a dark theme. Highlight, error and letter colours adapt to it. |
| `backgroundColor` | `String` | CSS colour behind the text (default transparent). |
| `height` | `double` | Fixed height instead of sizing to the text. |
| `bundled` | `bool` | Load everything from the app's assets (see above) instead of unpkg. |
| `onOpenUrl` | `void Function(String)` | Called with links the library opens: the translate buttons, to quran.com. Open them with `url_launcher`. By default they are ignored. On the web, the browser opens them. |
| `src`, `cdn` | `String` | Library script URL and asset base URL (default: unpkg, latest 2.x). Use these to load the library from your own server. |

Changing `page`, `sura`, `aya`, `words`, `highlight`, `error`, `letters` or the other tag
options re-renders in place. Changing `layout`, `fontSize`, `textColor`, `backgroundColor`,
`bundled`, `src` or `cdn` reloads the WebView.

## Example

The [example app](https://github.com/tarekeldeeb/quran-madina-html/tree/main/flutter/example)
has an online/offline switch. Its web build runs live at
<https://tarekeldeeb.github.io/quran-madina-html/flutter/>.
