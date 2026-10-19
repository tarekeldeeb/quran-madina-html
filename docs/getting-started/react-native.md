# React Native

```bash
npm install @tarekeldeeb/quran-madina-react-native react-native-webview
```

```jsx
import QuranMadinaNative from "@tarekeldeeb/quran-madina-react-native";

<QuranMadinaNative sura={2} aya="255" />
```

It shows the text in a WebView on iOS and Android, sized to the text, with the same options as
the React component. For offline use, `npx quran-madina-native-bundle` copies the library into
the app and `bundled` loads it from there.

See [React Native](../frameworks/react-native.md) for every prop, the offline setup and Expo.
