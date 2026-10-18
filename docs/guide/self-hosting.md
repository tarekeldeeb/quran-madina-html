# Self-hosting and offline

By default the script and everything it loads come from unpkg. You can serve them yourself,
from your own server or from inside an app, so pages render without unpkg or without any
internet connection.

## What to serve

From the npm package (`npm install quran-madina-html`), keep this folder structure:

| Path | What |
|---|---|
| `dist/quran-madina-html.min.js` | the script |
| `dist/quran-madina-html.min.css` | its styles (loaded by the script) |
| `assets/img/` | the sura frame |
| `assets/db/v2/<stem>/` | the text and layout of one print, split per juz' |
| `assets/db/v2/<font>-qmh.woff2` | that print's font |

The stems and fonts by layout:

| Layout | Database folder | Font |
|---|---|---|
| `1441H` | `Madina-1441H/` | `madina-qmh.woff2` |
| `1405H` | `Madina-1405H/` | `oldmadina-qmh.woff2` |
| `IndoPak` | `IndoPak-15/` | `indopak-qmh.woff2` |

Each print takes about 4 MB. Serve only the ones you use.

## Point the script at your copy

`data-cdn` is the base URL that holds `dist/` and `assets/`:

```html
<script src="/static/qmh/dist/quran-madina-html.min.js" data-cdn="/static/qmh/"></script>
```

Everything, the font included, then loads from there.

## The localhost rule

Without `data-cdn`, the script loads its files from unpkg, except on a page served from
`localhost`, where it assumes the files are one folder up (`../`). That is how this repository's
own demo works locally. A dev server or an app shell that also runs on `localhost` (a React dev
server, Capacitor) does not have the files there, so set `data-cdn` in those cases. The React
and Flutter wrappers do it for you.

## Apps

- **React with Capacitor:** bundle the files above into the web build and set the component's
  `src` and `cdn` props. See [React](../frameworks/react.md#offline).
- **Flutter:** one command copies the files into the app's assets. See
  [Flutter](../frameworks/flutter.md#online-or-offline).
