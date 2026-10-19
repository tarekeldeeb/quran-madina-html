# @tarekeldeeb/quran-madina-react-native

**[Documentation](https://tarekeldeeb.github.io/quran-madina-html/docs/frameworks/react-native/)** · [Live demo](https://tarekeldeeb.github.io/quran-madina-html/demo/index.html)

Quran pages that look like the printed Madina Mushaf, as real text, in React Native on iOS and
Android: the [quran-madina-html](https://github.com/tarekeldeeb/quran-madina-html) tag in a
[react-native-webview](https://github.com/react-native-webview/react-native-webview) WebView,
sized to the text. Same options as the React component and the Flutter widget, released in
step with the library. Works offline.

## Install

```bash
npm install @tarekeldeeb/quran-madina-react-native react-native-webview
cd ios && pod install    # bare React Native on iOS
```

With Expo: `npx expo install @tarekeldeeb/quran-madina-react-native react-native-webview`.

## Usage

```jsx
import QuranMadinaNative from "@tarekeldeeb/quran-madina-react-native";

<QuranMadinaNative sura={2} aya="255" />
<QuranMadinaNative page={106} headless />
<QuranMadinaNative sura={2} aya="255" highlight="5-8" error="1" />
<QuranMadinaNative sura={1} aya="2-4" letters="1:3, 4:3-5 emerald blink" />
<QuranMadinaNative page={50} layout="IndoPak" fontSize={22} textColor="#ece6d6" />
```

Props: `page`, `sura`, `aya`, `words`, `highlight`, `error`, `letters`, `headless`, `notitle`,
`quotes`, `inline`, `layout`, `fontSize`, `textColor`, `backgroundColor`, `height`, `bundled`,
`onOpenUrl`, `src`, `cdn`, `style`, `webViewProps`. See the
[documentation](https://tarekeldeeb.github.io/quran-madina-html/docs/frameworks/react-native/#props).

## Offline

```bash
npx quran-madina-native-bundle --layouts 1441H,IndoPak
```

copies the library, its texts and fonts into `android/app/src/main/assets/quran-madina/` and
`ios/quran-madina/`. On iOS, add that folder to the Xcode project once, as a folder reference
(blue folder). Then:

```jsx
<QuranMadinaNative page={106} bundled />
```

With Expo, use a development build (`npx expo prebuild` first).

## License

[Waqf General Public License 2.0](LICENSE.md).
