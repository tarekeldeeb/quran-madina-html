# Svelte

Svelte renders `<quran-madina-html>` as it is; there's nothing to configure. The page only
needs the library's script.

## 1. Load the library

Inside `<head>` of `src/app.html` (SvelteKit) or `index.html` (Vite):

```html
<script src="https://unpkg.com/quran-madina-html@2"></script>
```

Page-wide options (print, size, self-hosting) go on this tag:
see [Script options](../reference/script.md).

## 2. Use it

```svelte
<script>
  let aya = $state(255);
</script>

<quran-madina-html sura="2" aya={aya} highlight="5-8" headless></quran-madina-html>
<button onclick={() => aya++}>Next verse</button>
```

Bound values update the render when they change. With SvelteKit, the tag is rendered on the
server as plain HTML and comes to life in the browser. Every option is listed in
[Tag attributes](../reference/attributes.md).

!!! note "Library 2.1.2 and later"
    In the browser, Svelte passes `{...}` values to custom elements as properties, which the tag
    turns into attributes from 2.1.2. Older versions only see values written as plain text
    (`aya="255"`).

## Offline

Copy the library into `static/` (SvelteKit) or `public/` (Vite) with the bundler that ships with
the React wrapper, version 2.1.2 or later (it doesn't need React):

```bash
npx -p @tarekeldeeb/quran-madina-react quran-madina-bundle --layouts 1441H --out static/quran-madina
```

Then load it from there:

```html
<script src="/quran-madina/dist/quran-madina-html.min.js" data-cdn="/quran-madina/"></script>
```

See [Self-hosting and offline](../guide/self-hosting.md).
