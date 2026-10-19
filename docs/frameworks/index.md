# Frameworks

`<quran-madina-html>` is a standard web component, so it works in any framework that renders
HTML. Two frameworks get a dedicated package, because they can't use the tag directly or gain a
lot from one:

- [React](react.md): `@tarekeldeeb/quran-madina-react`, a component that loads the library for
  you, for React on the web and, through Capacitor, on iOS and Android.
- [Flutter](flutter.md): `quran_madina_flutter`, a widget for Android, iOS, macOS and the web.

The others use the tag as it is, with a line or two of setup:

| Framework | Setup | Page |
|---|---|---|
| Vue, Nuxt | mark the tag as a custom element in the compiler options | [Vue](vue.md) |
| Angular | `CUSTOM_ELEMENTS_SCHEMA` on the component | [Angular](angular.md) |
| Svelte, SvelteKit | none | [Svelte](svelte.md) |
| Astro | load the script with `is:inline` | [Astro](astro.md) |
| SolidJS, Preact, Lit, Alpine, plain JavaScript | none: write the tag, or create it with `document.createElement` | [HTML](../getting-started/html.md) |

Next.js is React: use the [React](react.md) component in a client component (`"use client"`).

## Setting values from code

Every attribute is also a property: `tag.aya = 256` is the same as
`tag.setAttribute("aya", "256")`, and either re-renders the tag. `true` sets an empty attribute,
and `null` or `false` removes it. Frameworks that pass values as properties (Vue, Svelte,
Angular's `[aya]`) rely on this, which needs library 2.1.2 or later.
