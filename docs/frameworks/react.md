# React

[![npm](https://img.shields.io/npm/v/@tarekeldeeb/quran-madina-react.svg)](https://www.npmjs.com/package/@tarekeldeeb/quran-madina-react)

`@tarekeldeeb/quran-madina-react` is a small component around the `<quran-madina-html>` tag.
The same component runs on the web and, inside a Capacitor app, on iOS and Android.

The library itself isn't bundled: the component adds its `<script>` when it first mounts,
because the library reads its options from its own script tag. `react` is a peer dependency.

## Install

```bash
npm install @tarekeldeeb/quran-madina-react react
```

## Usage

```jsx
import QuranMadinaHtml from "@tarekeldeeb/quran-madina-react";

export default function App() {
  return (
    <div dir="rtl">
      <QuranMadinaHtml page={106} layout="1441H" />                {/* a full page */}
      <QuranMadinaHtml sura={2} aya="8-10" />                      {/* verses */}
      <QuranMadinaHtml sura={1} aya={1} words="1:2" />             {/* some words */}
      <QuranMadinaHtml sura={1} aya={1} words="1-14" error="10-13" />
      <QuranMadinaHtml sura={1} aya="2-4" letters="1:3, 4:3-5 emerald blink" />
      <QuranMadinaHtml sura={2} aya="13-14" headless />            {/* no header */}
      <QuranMadinaHtml sura={1} aya={3} quotes="no" />             {/* inline, no quote marks */}
      <QuranMadinaHtml sura={1} aya={3} inline="no" />             {/* force the multiline layout */}
    </div>
  );
}
```

## Props

| Prop | Type | Notes |
|---|---|---|
| `page` | number \| string | Full page, 1–604 (IndoPak 1–610). Wins over `sura`/`aya`. |
| `sura` | number \| string | Sura 1–114, with `aya`. |
| `aya` | number \| string | Verse or range, e.g. `"8-10"`. |
| `words` | string | Word range: `"1:2"`, `"3-10"`, or one number. See [Selecting words](../guide/words.md). |
| `highlight` | string | Word range marked soft yellow, e.g. `"5-8"`. |
| `error` | string | Word range marked soft red. |
| `letters` | string | Letters to emphasise, e.g. `"1:3 crimson, 4:3-5 emerald blink"`. See [Emphasising letters](../guide/letters.md). |
| `headless` | boolean | Drop the header. |
| `notitle` | boolean | Hide the name of a sura a `words` selection crosses into. |
| `quotes` | string | `"no"` drops the quote marks around inline renders. |
| `inline` | string | `"no"` forces the multiline layout. |
| `layout` | string | `1441H` (default), `1405H` or `IndoPak`. |
| `fontSize` | number \| string | Size in px, default 16. |
| `src` | string | Library script URL. Default: unpkg, latest. |
| `cdn` | string | Base URL of the library's files. Default: unpkg. |
| `font`, `name` | string | Ignored since 2.0 (the library logs a warning). |

!!! warning "Page-wide options"
    `layout`, `fontSize`, `src` and `cdn` configure the one library instance on the page. Only
    the first `<QuranMadinaHtml>` to mount sets them; later values are ignored.

## Why `cdn` is set

Without `data-cdn`, the library loads its files from `../` on any `localhost` page (see
[the localhost rule](../guide/self-hosting.md#the-localhost-rule)). A React dev server and a
Capacitor app both run on `localhost`, so the component always sets `cdn`, to unpkg by default.
To use your own copy:

```jsx
<QuranMadinaHtml page={1} cdn="https://my.cdn.example/quran-madina-html/" />
```

## iOS and Android with Capacitor

Capacitor wraps your React web build in a native app with a WebView, so the same component runs
on the phone:

```bash
npm install @capacitor/core @capacitor/cli
npx cap init "My Quran App" com.example.quran --web-dir=dist
npm run build
npx cap add ios
npx cap add android
npx cap copy
npx cap open ios        # Xcode
npx cap open android    # Android Studio
```

## Offline

Bundle the library's files into your web build (see
[what to serve](../guide/self-hosting.md#what-to-serve)), then point the component at them:

```jsx
<QuranMadinaHtml page={1} src="/qmh/dist/quran-madina-html.min.js" cdn="/qmh/" />
```

## React Native

Not supported. React Native has no HTML or CSS, so the tag can't run there. Use Capacitor, or
a WebView component.
