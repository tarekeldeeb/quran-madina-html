# Styling and dark mode

## Text colour

The text takes the colour of the surrounding page, like any text. To change it, style the tag:

```css
quran-madina-html { color: #3b2f2f; }
```

## Colours you can change

Set these CSS custom properties on `quran-madina-html`, for all tags or for one:

| Property | Default | Used for |
|---|---|---|
| `--qmh-background` | `#F5F5DC` | the frame's tint (shown at 10%) |
| `--qmh-header` | `black` | the header bar's tint |
| `--qmh-highlight` | `#fff3b0` | `highlight` background |
| `--qmh-highlight-text` | `#1a1a1a` | `highlight` text |
| `--qmh-error` | `#f5c6cb` | `error` background |
| `--qmh-error-text` | `#1a1a1a` | `error` text |
| `--qmh-letter` | `#a3263a` | default `letters` colour |

```css
quran-madina-html {
  --qmh-highlight: #d7f5dd;
  --qmh-error: #ffd8a8;
}
```

Change colours only, never padding, margins or borders on the word spans: each word's width
is part of the line's justification.

## Dark pages

The library checks the tag's actual text colour. When it is light (a dark page), it switches
the `highlight` and `error` pairs to darker backgrounds with white text, and gives emphasised
letters a lighter shade. This follows your page's own colours, however your dark mode is built
(a class toggle, a theme, or the system setting), so there is nothing to configure.

The tag carries `data-qmh-text-scheme="dark"` or `"light"`, which you can use in your own CSS:

```css
quran-madina-html[data-qmh-text-scheme="dark"] { --qmh-highlight: #4a3b00; }
```

The check runs when a tag renders. If your page switches between light and dark without
reloading, re-render the tags afterwards: setting any attribute again does it.

```js
document.querySelectorAll("quran-madina-html").forEach(tag => {
  const key = tag.hasAttribute("page") ? "page" : "sura";
  tag.setAttribute(key, tag.getAttribute(key));
});
```

These docs do that: switch to dark mode (the moon icon in the header) to see the examples change.

## Printing and screenshots

- `highlight` and `error` backgrounds print, even where the browser skips backgrounds by default.
- Blinking letters stop blinking when printed, and keep their colour in every frame for
  screenshots.

## CSS classes

The generated elements have stable class names you can style; see [CSS reference](../reference/css.md).
