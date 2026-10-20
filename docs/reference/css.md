# CSS

## Custom properties

Set on `quran-madina-html`. See [Styling and dark mode](../guide/styling.md) for examples.

| Property | Default | Dark page | Used for |
|---|---|---|---|
| `--qmh-background` | `#F5F5DC` | | the frame's tint (10%) |
| `--qmh-header` | `black` | | the header bar's tint |
| `--qmh-highlight` | `#fff3b0` | `#5c4600` | `highlight` background |
| `--qmh-highlight-text` | `#1a1a1a` | `#ffffff` | `highlight` text |
| `--qmh-error` | `#f5c6cb` | `#6b1a24` | `error` background |
| `--qmh-error-text` | `#1a1a1a` | `#ffffff` | `error` text |
| `--qmh-letter` | `#a3263a` | lighter shade | `letters` colour (set per group from the attribute) |

## Generated elements and classes

| Element or class | What it is |
|---|---|
| `quran-madina-html-header` | the header bar (sura name, copy, translate) |
| `.quran-madina-html-sura-name` | the sura name in the header |
| `.quran-madina-html-icon-copy`, `.quran-madina-html-icon-translate` | the header's copy and translate icons |
| `.quran-madina-html-interactive` | on the tag when it has at least one [verse action](../guide/actions.md) |
| `.quran-madina-html-action`, `.quran-madina-html-action-ID` | a button in the verse popup, e.g. `.quran-madina-html-action-bookmark` |
| `quran-madina-html-line` | one line of text |
| `quran-madina-html-aya-popup` | the copy/translate menu opened by clicking a verse |
| `.quran-madina-html-NNN-NNN` | the parts of one verse (sura and verse, three digits each), e.g. `.quran-madina-html-002-255` |
| `.quran-madina-html-inline` | on the tag when it renders inline with quote marks |
| `.quran-madina-html-word-hidden` | a word outside a `words` selection (invisible, kept in place) |
| `.quran-madina-html-word-highlight` | a `highlight` word |
| `.quran-madina-html-word-error` | an `error` word |
| `.quran-madina-html-letter` | an emphasised letter |
| `.quran-madina-html-letter-blink` | an emphasised letter that blinks |
| `[data-qmh-text-scheme="dark"]` | on the tag when its text colour is light (a dark page) |

!!! warning
    Style colours only. Padding, margins, borders or a different font size on the words or
    lines would break the justification, which is computed from each word's width.
