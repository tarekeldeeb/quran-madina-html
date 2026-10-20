# Quran Madina Html

[![npm](https://img.shields.io/npm/v/quran-madina-html.svg?label=npm)](https://www.npmjs.com/package/quran-madina-html)
[![Socket Badge](https://badge.socket.dev/npm/package/quran-madina-html)](https://socket.dev/npm/package/quran-madina-html)
[![React](https://img.shields.io/npm/v/@tarekeldeeb/quran-madina-react.svg?label=react)](https://www.npmjs.com/package/@tarekeldeeb/quran-madina-react)
[![React Native](https://img.shields.io/npm/v/@tarekeldeeb/quran-madina-react-native.svg?label=react%20native)](https://www.npmjs.com/package/@tarekeldeeb/quran-madina-react-native)
[![pub.dev](https://img.shields.io/pub/v/quran_madina_flutter.svg?label=flutter)](https://pub.dev/packages/quran_madina_flutter)
[![WordPress](https://img.shields.io/badge/wordpress-plugin-21759b.svg)](https://github.com/tarekeldeeb/quran-madina-html/releases/latest/download/quran-madina-html-wordpress.zip)
[![Docs](https://img.shields.io/badge/docs-online-00796b.svg)](https://tarekeldeeb.github.io/quran-madina-html/docs/)
[![License](https://img.shields.io/badge/license-Waqf%20GPL%202.0-blue.svg)](LICENSE.md)
[![build](https://github.com/tarekeldeeb/quran-madina-html/actions/workflows/npm-grunt.yml/badge.svg)](https://github.com/tarekeldeeb/quran-madina-html/actions/workflows/npm-grunt.yml)
[![tests](https://github.com/tarekeldeeb/quran-madina-html/actions/workflows/py_test.yml/badge.svg)](https://github.com/tarekeldeeb/quran-madina-html/actions/workflows/py_test.yml)
[![Flutter](https://github.com/tarekeldeeb/quran-madina-html/actions/workflows/flutter.yml/badge.svg)](https://github.com/tarekeldeeb/quran-madina-html/actions/workflows/flutter.yml)

Quran pages that look like the printed Madina Mushaf, as real text: selectable, searchable and
copyable, with no images. Lines are justified the way the print fills them, by stretching the
letters themselves. One tag renders a page, a verse range or a few words, with highlighted
words and emphasised letters, in the 1441H, 1405H or IndoPak print.

<p align="center">
  <img src="https://raw.githubusercontent.com/tarekeldeeb/quran-madina-html/main/docs/assets/img/showcase.gif" width="720" alt="quran-madina-html rendering a page, a verse, highlighted words, blinking letters, a selection across suras, and three prints">
</p>

<p align="center">
  <a href="https://tarekeldeeb.github.io/quran-madina-html/docs/"><b>Documentation</b></a> ·
  <a href="https://tarekeldeeb.github.io/quran-madina-html/reader/"><b>Quran reader</b></a> ·
  <a href="https://tarekeldeeb.github.io/quran-madina-html/demo/index.html"><b>Live demo</b></a>
</p>

## Getting started

### HTML

```html
<script src="https://unpkg.com/quran-madina-html@2"></script>

<quran-madina-html sura="2" aya="255"></quran-madina-html>
```

### React

```bash
npm install @tarekeldeeb/quran-madina-react react
```

```jsx
import QuranMadinaHtml from "@tarekeldeeb/quran-madina-react";

<QuranMadinaHtml sura={2} aya="255" />
```

### React Native

```bash
npm install @tarekeldeeb/quran-madina-react-native react-native-webview
```

```jsx
import QuranMadinaNative from "@tarekeldeeb/quran-madina-react-native";

<QuranMadinaNative sura={2} aya="255" />
```

### Flutter

```yaml
dependencies:
  quran_madina_flutter: ^2.1.3
```

```dart
import 'package:quran_madina_flutter/quran_madina_flutter.dart';

QuranMadinaFlutter(sura: 2, aya: '255')
```

### Vue, Angular, Svelte, Astro

The tag is a standard web component, so it works in any framework: load the script once and use
`<quran-madina-html>` in your templates. Each framework's setup is a few lines; see
[Vue](https://tarekeldeeb.github.io/quran-madina-html/docs/frameworks/vue/), [Angular](https://tarekeldeeb.github.io/quran-madina-html/docs/frameworks/angular/),
[Svelte](https://tarekeldeeb.github.io/quran-madina-html/docs/frameworks/svelte/) and [Astro](https://tarekeldeeb.github.io/quran-madina-html/docs/frameworks/astro/).

### WordPress

Download the [plugin zip](https://github.com/tarekeldeeb/quran-madina-html/releases/latest/download/quran-madina-html-wordpress.zip),
then **Plugins → Add New → Upload Plugin**. Add the **Quran** block in the editor, or use the
shortcode anywhere:

```text
[quran sura="2" aya="255"]
```

The plugin carries the library, so nothing loads from outside your site. See
[WordPress](https://tarekeldeeb.github.io/quran-madina-html/docs/getting-started/wordpress/).

Everything else (pages, word selection, highlighting, letters, layouts, styling, offline use,
and every option) is in the [documentation](https://tarekeldeeb.github.io/quran-madina-html/docs/).

## Credits

- Quran text: [Tanzil Project](https://tanzil.net) (Uthmani 1.1).
- Fonts and the 1405H and IndoPak layouts: [DigitalKhatt](https://github.com/DigitalKhatt/digitalkhatt.org)
  by Amine Anane, sponsored by Tarteel (fonts OFL 1.1, code MIT). The fonts in `assets/db/v2`
  are modified copies, with stretch features added, under the same license and renamed `QMH ...`.
- 1441H line breaks: King Fahd Glorious Quran Printing Complex page data, as published in the
  [`quran-qcf4`](https://www.npmjs.com/package/quran-qcf4) package (MIT); only the line
  boundaries are used.

## License

Code and assets are licensed under the ["Waqf" General Public License 2.0](https://github.com/ojuba-org/waqf/tree/master/2.0).
See [LICENSE.md](LICENSE.md). The WordPress plugin alone is dual licensed: GPLv2 or later, or
the Waqf General Public License 2.0.
