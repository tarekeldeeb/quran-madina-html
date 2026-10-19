# Vue

Vue renders `<quran-madina-html>` like any element. It only needs to know the tag isn't a Vue
component, and the page needs the library's script.

## 1. Load the library

In `index.html`, inside `<head>`:

```html
<script src="https://unpkg.com/quran-madina-html@2"></script>
```

Page-wide options (print, size, self-hosting) go on this tag:
see [Script options](../reference/script.md).

## 2. Tell Vue it's a custom element

With Vite, in `vite.config.js`:

```js
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [
    vue({
      template: {
        compilerOptions: { isCustomElement: (tag) => tag === "quran-madina-html" },
      },
    }),
  ],
});
```

Without this, Vue logs "Failed to resolve component: quran-madina-html" and still renders it.
Nuxt takes the same option under `vue.compilerOptions` in `nuxt.config.ts`.

## 3. Use it

```vue
<script setup>
import { ref } from "vue";
const aya = ref(255);
</script>

<template>
  <quran-madina-html sura="2" :aya="aya" highlight="5-8" headless></quran-madina-html>
  <button @click="aya++">Next verse</button>
</template>
```

Bound values update the render when they change. Every option is listed in
[Tag attributes](../reference/attributes.md).

!!! note "Library 2.1.2 and later"
    Vue passes bound values to custom elements as properties. The tag turns those into
    attributes from 2.1.2. With an older version, bind them as attributes instead:
    `:aya.attr="aya"`.

## Offline

Copy the library into `public/` with the bundler that ships with the React wrapper, version 2.1.2 or
later (it doesn't need React):

```bash
npx -p @tarekeldeeb/quran-madina-react quran-madina-bundle --layouts 1441H
```

Then load it from there:

```html
<script src="/quran-madina/dist/quran-madina-html.js" data-cdn="/quran-madina/"></script>
```

See [Self-hosting and offline](../guide/self-hosting.md).
