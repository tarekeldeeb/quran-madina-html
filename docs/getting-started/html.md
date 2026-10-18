# HTML

## Add the script

Load the library once, in the page's `<head>`:

```html
<script src="https://unpkg.com/quran-madina-html@2"></script>
```

Or install it from npm and serve the files yourself
(see [Self-hosting and offline](../guide/self-hosting.md)):

```bash
npm install quran-madina-html
```

## Add a tag

Put a tag wherever the text should appear:

<div class="qmh-example">
<quran-madina-html sura="1" aya="1-7"></quran-madina-html>
</div>

```html
<quran-madina-html sura="1" aya="1-7"></quran-madina-html>
```

A selection that fits on one line renders inline, inside your text, between quote marks:
the verse <quran-madina-html sura="112" aya="1"></quran-madina-html> sits in this sentence.

```html
the verse <quran-madina-html sura="112" aya="1"></quran-madina-html> sits in this sentence.
```

## Choose the print and the size

Options for the whole page go on the script tag:

```html
<script src="https://unpkg.com/quran-madina-html@2" data-layout="1405H" data-font-size="22"></script>
```

See [Layouts and sizes](../guide/layouts.md) and [Script options](../reference/script.md).

## Upgrading from 1.x

Version 2 is a drop-in replacement: existing tags render unchanged. The 1.x font options
(`data-font`, `data-name`) are ignored, with a console warning. To keep the 1.x renderer, pin
`quran-madina-html@1`. The old documentation is under [Version 1.x](../v1.md).
