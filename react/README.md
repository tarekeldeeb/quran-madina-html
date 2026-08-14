# @tarekeldeeb/quran-madina-react

[![Socket Badge](https://badge.socket.dev/npm/package/@tarekeldeeb/quran-madina-react)](https://socket.dev/npm/package/@tarekeldeeb/quran-madina-react)

A thin React component around the `<quran-madina-html>` custom element. The actual rendering is
still done by the [`quran-madina-html`](https://www.npmjs.com/package/quran-madina-html) library
(HTML/CSS, no images) — this just loads it and exposes the tag as a normal React component. The
**same** wrapper drives **web, iOS and Android** (mobile via a WebView container such as Capacitor;
see below).

The library is not bundled: the component injects its `<script>` at runtime (the library reads its
config from its own `<script>` tag, so a plain `import` of it would not work). `react` is a peer
dependency.

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
      {/* full page */}
      <QuranMadinaHtml page={106} font="Hafs" />

      {/* aya range */}
      <QuranMadinaHtml sura={2} aya="8-10" />

      {/* a word subsequence (1-based, inclusive) */}
      <QuranMadinaHtml sura={1} aya={1} words="1:2" />

      {/* highlight an error range */}
      <QuranMadinaHtml sura={1} aya={1} words="1-14" error="10-13" />

      {/* no header / copy chrome */}
      <QuranMadinaHtml sura={2} aya="13-14" headless />

      {/* inline (single-line) render without the quote marks around it */}
      <QuranMadinaHtml sura={1} aya={3} quotes="no" />

      {/* force the multiline/header layout even though this would normally fit one line */}
      <QuranMadinaHtml sura={1} aya={3} inline="no" />
    </div>
  );
}
```

### Props

| Prop        | Type                | Notes |
|-------------|---------------------|-------|
| `page`      | number \| string    | Full page 1–604. Mutually exclusive with `sura`/`aya` (page wins). |
| `sura`      | number \| string    | Sura 1–114, with `aya`. |
| `aya`       | number \| string    | Aya or range, e.g. `"8-10"`. |
| `words`     | string              | 1-based word range: `"1:2"`, `"3-10"`, or a single index. |
| `error`     | string              | 1-based word range to mark with built-in "error" highlight styling, e.g. `"10-13"`. |
| `headless`  | boolean             | Drop the header/copy chrome. |
| `quotes`    | string              | `"no"` (or `"false"`) drops the quote marks shown around inline (single-line) renders. |
| `inline`    | string              | `"no"` forces the multiline/header layout even for a selection that fits one line. `"auto"` (default) is fit-based. `"yes"` (force a single line for an overflowing selection) is not implemented yet. |
| `font`      | string              | `Hafs`, `Uthman`, `Amiri Quran`, `Amiri Quran Colored`, `me_quran`. |
| `name`      | string              | DB name, default `Madina05`. |
| `fontSize`  | number \| string    | px, default 16. Any size 6–100: 16 and 24 have pre-built DBs, every other size is interpolated between them at load time. |
| `src`       | string              | Library script URL. Default: unpkg latest. |
| `cdn`       | string              | Base URL for CSS + JSON assets. Default: unpkg package root. |

> **Global config caveat:** `font`, `name`, `fontSize`, `src` and `cdn` configure the single
> library instance for the whole page. Only the **first** mounted `<QuranMadinaHtml>` sets them;
> later values are ignored. Put your config on the first instance you render.

## Why `cdn` matters (localhost gotcha)

The library figures out where to fetch its CSS + JSON DB from based on the **page** host: on any
`localhost` host it assumes the assets live at `../` (that's how this repo's own demo works). A
React dev server (`localhost:3000`) and a Capacitor app (host is also `localhost`) do **not** have
the assets at `../`, so without help the DB fetch 404s.

The wrapper fixes this by setting `data-cdn` to the unpkg package root by default, so assets always
resolve. Override `cdn` if you self-host the assets:

```jsx
<QuranMadinaHtml page={1} cdn="https://my.cdn.example/quran-madina-html/" />
```

> `data-cdn` support requires a build of the library that includes it (the release that introduced
> this feature, or a local `npm run build` of this repo). When loading from a CDN, pin a version
> that supports it, e.g. `src="https://unpkg.com/quran-madina-html@X.Y.Z"`.

## Mobile: iOS + Android with Capacitor

Capacitor wraps your existing React web build in a native shell with a WebView, so the very same
component runs on device. Outline:

```bash
# in your React app
npm install @capacitor/core @capacitor/cli
npx cap init "My Quran App" com.example.quran --web-dir=dist   # or build/ for CRA
npm run build                 # produce the web bundle
npx cap add ios
npx cap add android
npx cap copy
npx cap open ios              # opens Xcode  → run on simulator/device
npx cap open android         # opens Android Studio
```

Notes for mobile:

- Capacitor serves the app from `localhost`, so keep the default `cdn` (unpkg) **or** self-host the
  assets and point `cdn` at them — see above. Do not rely on the library's `../` default.
- **Offline support:** bundle the library `dist/quran-madina-html.min.js`, `dist/*.min.css`, the
  `assets/db/*.json` you use and the `assets/fonts/*.woff2` into your web build, then set `src` to
  the bundled JS and `cdn` to the base path that contains `dist/` and `assets/`. Everything —
  including the font — resolves from `cdn`, so no network is needed (requires library >= 0.6,
  which stores font paths relative).
- This is the recommended mobile path: it reuses the battle-tested HTML/CSS renderer (fonts,
  per-line stretch, offsets) instead of reimplementing the layout natively in React Native.

## React Native (native, no WebView)

Not provided here. React Native has no DOM/HTML/CSS, so the custom element cannot run; it would
require porting the renderer to native `View`/`Text` + `transform: scaleX`. Use the Capacitor path
above unless you specifically need native (non-WebView) rendering.

## Developing this package

```bash
cd react
npm install
npm test                # vitest (jsdom) — wrapper + loader unit tests
npm run build           # esbuild → dist/index.mjs + dist/index.cjs, copies dist/index.d.ts
```

`dist/` is git-ignored and rebuilt automatically on publish (`prepublishOnly`). Source lives in
`src/`; the public API is hand-typed in `src/index.d.ts`.

## Releasing

This package is released **in lockstep with the core library** by the repo-root command:

```bash
npm run release         # release-it: builds + publishes quran-madina-html AND this wrapper
```

The root `release-it` config syncs this `package.json` to the core's new version before the release
commit, then publishes `@tarekeldeeb/quran-madina-react@<version>` (matching the core) after the
core lands on npm (see `scripts/sync-wrapper-version.mjs` and `scripts/publish-wrapper.mjs`). So the
wrapper version always equals the core version. A manual one-off publish is still possible with
`npm publish --access public` from this folder (scoped packages need `--access public`).
