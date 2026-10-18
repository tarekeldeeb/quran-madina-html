# Selecting words

`words` shows only some words, counted from the start of the given verse. The rest of the text
stays in place but invisible, so the line keeps exactly the shape it has in the print.

<div class="qmh-example">
<quran-madina-html sura="1" aya="1" words="1:2"></quran-madina-html>
</div>

=== "HTML"

    ```html
    <quran-madina-html sura="1" aya="1" words="1:2"></quran-madina-html>
    ```

=== "React"

    ```jsx
    <QuranMadinaHtml sura={1} aya="1" words="1:2" />
    ```

=== "Flutter"

    ```dart
    QuranMadinaFlutter(sura: 1, aya: '1', words: '1:2')
    ```

## Range format

Words are numbered from 1, and both ends are included:

| Value | Means |
|---|---|
| `5` | word 5 only |
| `3-10` or `3:10` | words 3 to 10 |

Verse-number ornaments are not counted. `words` works with `sura` and `aya`; it is ignored on a
full `page`. With an `aya` range, only the first verse sets where counting starts.

## Across verses, pages and suras

Counting carries on past the end of the verse, so a selection can cross verses, pages and even
suras. After An-Nas it wraps around to Al-Fatiha.

<div class="qmh-example">
<quran-madina-html sura="1" aya="7" words="1-14"></quran-madina-html>
</div>

=== "HTML"

    ```html
    <!-- Al-Fatiha's last verse (9 words), Al-Baqara's basmala (4 words), then الٓمٓ -->
    <quran-madina-html sura="1" aya="7" words="1-14"></quran-madina-html>
    ```

=== "React"

    ```jsx
    {/* Al-Fatiha's last verse (9 words), Al-Baqara's basmala (4 words), then الٓمٓ */}
    <QuranMadinaHtml sura={1} aya="7" words="1-14" />
    ```

=== "Flutter"

    ```dart
    // Al-Fatiha's last verse (9 words), Al-Baqara's basmala (4 words), then الٓمٓ
    QuranMadinaFlutter(sura: 1, aya: '7', words: '1-14')
    ```

## The basmala counts as four words

The basmala at the top of a sura counts as its four words, matching the flat word numbering of
the Tanzil text that most apps count with. This holds when a selection crosses into a new sura,
and when it starts at a sura's first verse: word 1 is then بسم and word 5 is the verse's
first word.

- When all four words are selected, they show as the ﷽ ligature, as in the print. A partial
  selection shows the separate words. Either way the basmala takes four word numbers.
- At-Tawba has no basmala, so it adds no words. Al-Fatiha's basmala is its real first verse.
- The sura name above it is decoration and is never counted.

## Hiding the sura name

When you show a selection inside your own layout (a quiz that already names the sura, say),
`notitle="true"` hides the name of a sura the selection crosses into. Its decorated frame stays,
empty, and the basmala still shows:

=== "HTML"

    ```html
    <quran-madina-html sura="1" aya="7" words="1-14" notitle="true"></quran-madina-html>
    ```

=== "React"

    ```jsx
    <QuranMadinaHtml sura={1} aya="7" words="1-14" notitle />
    ```

=== "Flutter"

    ```dart
    QuranMadinaFlutter(sura: 1, aya: '7', words: '1-14', notitle: true)
    ```

## Limits and errors

- A selection is capped at 500 words.
- A malformed or reversed range (`10-3`, `0`) is ignored with a console message, and the
  verse renders whole.

!!! note "Changes in older versions"
    - 0.9.0: the basmala started counting as four words (before, it was never counted).
    - 0.9.3: a selection starting at a sura's first verse counts that sura's own basmala.
    - 0.9.5: a selection running past An-Nas wraps around to Al-Fatiha instead of stopping.
