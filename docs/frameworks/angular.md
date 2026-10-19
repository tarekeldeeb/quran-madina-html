# Angular

Angular renders `<quran-madina-html>` once a component allows custom elements, and the page
loads the library's script.

## 1. Load the library

In `src/index.html`, inside `<head>`:

```html
<script src="https://unpkg.com/quran-madina-html@2"></script>
```

Page-wide options (print, size, self-hosting) go on this tag:
see [Script options](../reference/script.md).

## 2. Allow the custom element

Add `CUSTOM_ELEMENTS_SCHEMA` to each component that uses the tag (or to its `NgModule`):

```ts
import { Component, CUSTOM_ELEMENTS_SCHEMA } from "@angular/core";

@Component({
  selector: "app-verse",
  standalone: true,
  schemas: [CUSTOM_ELEMENTS_SCHEMA],
  template: `
    <quran-madina-html sura="2" [attr.aya]="aya" highlight="5-8" headless></quran-madina-html>
    <button (click)="aya = aya + 1">Next verse</button>
  `,
})
export class VerseComponent {
  aya = 255;
}
```

Without the schema, the template fails to compile: "'quran-madina-html' is not a known element".

## 3. Bind values

Bind with `[attr.name]`, which sets the attribute; the tag re-renders when it changes:

```html
<quran-madina-html [attr.sura]="sura" [attr.aya]="aya" [attr.letters]="letters"></quran-madina-html>
```

From library 2.1.2, plain property bindings (`[aya]="aya"`) work too. Every option is listed in
[Tag attributes](../reference/attributes.md).

## Offline

Copy the library into the app with the bundler that ships with the React wrapper, version 2.1.2 or
later (it doesn't need React), into a folder Angular serves, such as `public/` (Angular 17+) or `src/assets/`:

```bash
npx -p @tarekeldeeb/quran-madina-react quran-madina-bundle --layouts 1441H --out public/quran-madina
```

Then load it from there:

```html
<script src="/quran-madina/dist/quran-madina-html.min.js" data-cdn="/quran-madina/"></script>
```

See [Self-hosting and offline](../guide/self-hosting.md).
