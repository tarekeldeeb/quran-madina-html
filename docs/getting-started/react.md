# React

```bash
npm install @tarekeldeeb/quran-madina-react react
```

```jsx
import QuranMadinaHtml from "@tarekeldeeb/quran-madina-react";

export default function App() {
  return <QuranMadinaHtml sura={2} aya="255" />;
}
```

The component loads the library for you, so there is no script tag to add. Props take the same
names as the tag's attributes, plus `layout` and `fontSize` for the page-wide options.

The same component runs on iOS and Android inside a Capacitor app. See [React](../frameworks/react.md)
for every prop and the mobile guide.
