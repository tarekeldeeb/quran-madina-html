# Pages and verses

## A full page

`page` renders a whole Mushaf page, 1 to 604 (IndoPak: 1 to 610):

<div class="qmh-example">
<quran-madina-html page="1"></quran-madina-html>
</div>

=== "HTML"

    ```html
    <quran-madina-html page="1"></quran-madina-html>
    ```

=== "React"

    ```jsx
    <QuranMadinaHtml page={1} />
    ```

=== "React Native"

    ```jsx
    <QuranMadinaNative page={1} />
    ```

=== "Flutter"

    ```dart
    QuranMadinaFlutter(page: 1)
    ```

## A verse or a range

`sura` (1 to 114) and `aya` (one number, or a range like `8-10`) render just those verses,
laid out exactly as they sit on the page:

<div class="qmh-example">
<quran-madina-html sura="2" aya="8-10"></quran-madina-html>
</div>

=== "HTML"

    ```html
    <quran-madina-html sura="2" aya="8-10"></quran-madina-html>
    ```

=== "React"

    ```jsx
    <QuranMadinaHtml sura={2} aya="8-10" />
    ```

=== "React Native"

    ```jsx
    <QuranMadinaNative sura={2} aya="8-10" />
    ```

=== "Flutter"

    ```dart
    QuranMadinaFlutter(sura: 2, aya: '8-10')
    ```

Verses are numbered the Kufan way in every layout, so the same `sura` and `aya` show the same
verse whichever print you choose. A range may run onto the next page.

## Header or no header

A multiline render has a header with the sura name and two buttons: copy the text, and open
the translation on quran.com. `headless="true"` keeps only the Quran text:

<div class="qmh-example">
<quran-madina-html sura="5" aya="1-2" headless="true"></quran-madina-html>
</div>

=== "HTML"

    ```html
    <quran-madina-html sura="5" aya="1-2" headless="true"></quran-madina-html>
    ```

=== "React"

    ```jsx
    <QuranMadinaHtml sura={5} aya="1-2" headless />
    ```

=== "React Native"

    ```jsx
    <QuranMadinaNative sura={5} aya="1-2" headless />
    ```

=== "Flutter"

    ```dart
    QuranMadinaFlutter(sura: 5, aya: '1-2', headless: true)
    ```

Clicking a verse opens a small copy/translate menu for that verse alone. It works on inline
renders too, which have no header.

## Inline renders

A selection that fits on one line renders inline, inside the surrounding text, between quote
marks: <quran-madina-html sura="1" aya="2"></quran-madina-html>.

- `quotes="no"` drops the quote marks.
- `inline="no"` forces the multiline layout, with its header, even for a short selection.

=== "HTML"

    ```html
    <quran-madina-html sura="1" aya="2" quotes="no"></quran-madina-html>
    <quran-madina-html sura="1" aya="2" inline="no"></quran-madina-html>
    ```

=== "React"

    ```jsx
    <QuranMadinaHtml sura={1} aya="2" quotes="no" />
    <QuranMadinaHtml sura={1} aya="2" inline="no" />
    ```

=== "React Native"

    ```jsx
    <QuranMadinaNative sura={1} aya="2" quotes="no" />
    <QuranMadinaNative sura={1} aya="2" inline="no" />
    ```

=== "Flutter"

    ```dart
    QuranMadinaFlutter(sura: 1, aya: '2', quotes: 'no'),
    QuranMadinaFlutter(sura: 1, aya: '2', inline: 'no'),
    ```
