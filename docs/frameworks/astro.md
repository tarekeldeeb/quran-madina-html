# Astro

In Astro the tag is plain HTML: it works in `.astro` pages and layouts with no integration.

## 1. Load the library

In your layout's `<head>`. `is:inline` keeps Astro from bundling the script, which the library
needs, since it reads its options from its own `<script>` tag:

```astro
<script is:inline src="https://unpkg.com/quran-madina-html@2"></script>
```

Page-wide options (print, size, self-hosting) go on this tag:
see [Script options](../reference/script.md).

## 2. Use it

```astro
---
const verse = { sura: 2, aya: 255 };
---
<quran-madina-html sura={verse.sura} aya={verse.aya} highlight="5-8" headless></quran-madina-html>
```

Values in `{...}` are written as attributes when the page is built, so this works on static and
server-rendered pages alike. Every option is listed in [Tag attributes](../reference/attributes.md).

Inside a React, Vue or Svelte island, follow that framework's page.

## Offline

Copy the library into `public/` with the bundler that ships with the React wrapper, version 2.1.2 or
later (it doesn't need React):

```bash
npx -p @tarekeldeeb/quran-madina-react quran-madina-bundle --layouts 1441H
```

Then load it from there:

```astro
<script is:inline src="/quran-madina/dist/quran-madina-html.js" data-cdn="/quran-madina/"></script>
```

See [Self-hosting and offline](../guide/self-hosting.md).
