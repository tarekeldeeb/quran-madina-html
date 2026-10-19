# Emphasising letters

`letters` colours single letters inside words, with a soft halo, for teaching a letter or
pointing at a mistake. Nothing moves or changes size.

<div class="qmh-example">
<quran-madina-html sura="1" aya="2-4" highlight="1" error="4" letters="1:3, 4:3+5 lapis blink, 6:4 emerald"></quran-madina-html>
</div>

=== "HTML"

    ```html
    <quran-madina-html sura="1" aya="2-4" highlight="1" error="4"
      letters="1:3, 4:3+5 lapis blink, 6:4 emerald"></quran-madina-html>
    ```

=== "React"

    ```jsx
    <QuranMadinaHtml
      sura={1}
      aya="2-4"
      highlight="1"
      error="4"
      letters="1:3, 4:3+5 lapis blink, 6:4 emerald"
    />
    ```

=== "React Native"

    ```jsx
    <QuranMadinaNative
      sura={1}
      aya="2-4"
      highlight="1"
      error="4"
      letters="1:3, 4:3+5 lapis blink, 6:4 emerald"
    />
    ```

=== "Flutter"

    ```dart
    QuranMadinaFlutter(
      sura: 1,
      aya: '2-4',
      highlight: '1',
      error: '4',
      letters: '1:3, 4:3+5 lapis blink, 6:4 emerald',
    )
    ```

## Format

A comma-separated list of groups, each `word:letters`, then an optional colour, then an
optional `blink`:

| Part | Values |
|---|---|
| word | a word number, counted like [`highlight`](highlighting.md) |
| letters | `3` (one letter), `3-5` (letters 3 to 5) or `3+5` (letters 3 and 5) |
| colour | `crimson` (default), `emerald`, `lapis`, `gold`, `violet`, or any CSS colour |
| `blink` | makes the halo pulse gently; no animation without it |

Examples: `1:3`, `4:2-3 emerald`, `6:1+4 #8a2be2 blink`.

## How it looks

- The letter takes the colour, with a halo of the same colour that sits behind the surrounding
  ink, never over it.
- With `blink`, only the halo pulses. The letter keeps its colour in every frame, so a
  screenshot always shows it. Blinking stops when printing and when the reader's system asks
  for reduced motion.
- It works inside `highlight` and `error` words, and gets a lighter shade on dark pages.

## What counts as a letter

Letters are counted as written. Diacritics and other marks, and tatweel, belong to the letter
before them. Lam-alef (لا) is drawn as one shape, so marking either of its two letters colours
both.
