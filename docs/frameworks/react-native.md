# React Native

[![npm](https://img.shields.io/npm/v/@tarekeldeeb/quran-madina-react-native.svg)](https://www.npmjs.com/package/@tarekeldeeb/quran-madina-react-native)

`@tarekeldeeb/quran-madina-react-native` shows the `<quran-madina-html>` tag in a
[react-native-webview](https://github.com/react-native-webview/react-native-webview) WebView,
sized to the text, on iOS and Android. It takes the same options as the React component and the
Flutter widget, and can work offline.

## Install

```bash
npm install @tarekeldeeb/quran-madina-react-native react-native-webview
cd ios && pod install    # bare React Native on iOS
```

With Expo: `npx expo install @tarekeldeeb/quran-madina-react-native react-native-webview`. It
works in Expo Go online; offline needs a development build (see [Offline](#offline)).

## Usage

```jsx
import QuranMadinaNative from "@tarekeldeeb/quran-madina-react-native";

<QuranMadinaNative sura={2} aya="255" />                          {/* a verse */}
<QuranMadinaNative page={106} headless />                         {/* a full page */}
<QuranMadinaNative sura={1} aya={1} words="1:2" />                {/* some words */}
<QuranMadinaNative sura={2} aya="255" highlight="5-8" error="1" />
<QuranMadinaNative sura={1} aya="2-4" letters="1:3, 4:3-5 emerald blink" />
<QuranMadinaNative page={50} layout="IndoPak" fontSize={22} />
<QuranMadinaNative page={106} bundled />                          {/* offline */}
```

The component takes the height of the rendered text, so it fits in a `ScrollView` or
`FlatList`. Each one is its own WebView: for a long passage, render it in one component
(`sura={2} aya="1-20"`) rather than one per verse.

## Props

| Prop | Type | Description |
|---|---|---|
| `page` | number \| string | A full page, 1–604 (IndoPak 1–610). Wins over `sura`/`aya`. |
| `sura`, `aya` | number \| string | Sura 1–114, and a verse or range: `255`, `"8-10"`. |
| `words` | string | Only these words: `"1:2"`, `"3-10"`. See [Selecting words](../guide/words.md). |
| `highlight` | string | Words marked soft yellow, e.g. `"5-8"`. |
| `error` | string | Words marked soft red; wins over `highlight`. |
| `letters` | string | Letters to emphasise, e.g. `"1:3, 4:3-5 emerald blink"`. See [Emphasising letters](../guide/letters.md). |
| `headless` | boolean | Only the Quran text, without the header. |
| `notitle` | boolean | Hide the name of a sura a `words` selection crosses into. |
| `quotes` | string | `"no"` drops the quote marks around inline renders. |
| `inline` | string | `"no"` forces the multiline layout. |
| `layout` | string | `"1441H"` (default), `"1405H"` or `"IndoPak"`. Per component. |
| `fontSize` | number | Size in points, default 16. |
| `textColor` | string | CSS colour of the text, e.g. `"#ece6d6"` on a dark screen. Mark colours adapt to it. |
| `backgroundColor` | string | CSS colour behind the text (default transparent). |
| `height` | number | A fixed height instead of the text's. |
| `bundled` | boolean \| string | Load the library from the app instead of unpkg (see [Offline](#offline)). |
| `onOpenUrl` | `(url) => void` | Links the library opens: the translate buttons, to quran.com. Default: `Linking.openURL`. |
| `src`, `cdn` | string | Library script URL and file base URL (default: unpkg, latest 2.x). |
| `style` | ViewStyle | Style of the outer view. |
| `webViewProps` | object | Extra props for the WebView. |

Changing `page`, `sura`, `aya`, `words`, `highlight`, `error`, `letters` or the other tag
options updates the text in place. Changing `layout`, `fontSize`, the colours, `bundled`, `src`
or `cdn` reloads the WebView.

## Offline

By default the library, its texts and fonts load from unpkg. To work offline, copy them into the
app once, from the app's folder:

```bash
npx quran-madina-native-bundle                            # the 1441H layout (about 4 MB)
npx quran-madina-native-bundle --layouts 1441H,IndoPak    # about 4 MB per layout
```

It writes `android/app/src/main/assets/quran-madina/` and `ios/quran-madina/`, for the
platform folders your app has, with the library and the page the WebView opens.

**iOS, once:** in Xcode, drag the `ios/quran-madina` folder onto the project, choose **Create
folder references** (it shows as a blue folder), and tick your app target. Android needs
nothing more.

Then pass `bundled`:

```jsx
<QuranMadinaNative page={106} bundled />
```

| Option | Default | Description |
|---|---|---|
| `--layouts` | `1441H` | The prints to include: `1441H`, `1405H`, `IndoPak`, comma-separated. |
| `--version` | this package's version | The quran-madina-html version to copy from npm. |
| `--from` | | Copy from a built checkout of quran-madina-html instead of npm. |
| `--android`, `--ios` | the folders above | Write somewhere else; then pass that folder's URL as `bundled`. |

Run the command again after upgrading this package, so the files match its version.

**Expo:** offline needs native folders, so use a development build: run `npx expo prebuild`,
then the command above (and the iOS step). Expo Go can't include them; use the online mode there.

## Notes

- The library loads in the WebView, so the app needs internet access unless it's `bundled`.
- Text colour: the WebView doesn't inherit your app's styles. Pass `textColor` (and
  `backgroundColor`) for dark screens; the library then picks its dark-screen shades for marks
  and letters.
- React Native for Web isn't supported (the WebView doesn't run there); on the web, use the
  [React](react.md) component.
