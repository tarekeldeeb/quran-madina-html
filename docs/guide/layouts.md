# Layouts and sizes

## Three prints

The script tag's `data-layout` picks the print. It applies to every tag on the page.

<div class="qmh-gallery">
<figure><img src="../../assets/img/v2-p50-1441H.png" alt="page 50, 1441H"><figcaption><code>1441H</code> (default)<br>New Madina Mushaf</figcaption></figure>
<figure><img src="../../assets/img/v2-p50-1405H.png" alt="page 50, 1405H"><figcaption><code>1405H</code><br>Old Madina Mushaf</figcaption></figure>
<figure><img src="../../assets/img/v2-p50-IndoPak.png" alt="page 50, IndoPak"><figcaption><code>IndoPak</code><br>15-line IndoPak</figcaption></figure>
</div>

=== "HTML"

    ```html
    <script src="https://unpkg.com/quran-madina-html@2" data-layout="IndoPak"></script>
    ```

=== "React"

    ```jsx
    {/* layout and fontSize apply to the whole page: set them on the first component */}
    <QuranMadinaHtml layout="IndoPak" sura={2} aya="255" />
    ```

=== "Flutter"

    ```dart
    // per widget on Android, iOS and macOS; on the web, the first widget's apply page-wide
    QuranMadinaFlutter(layout: 'IndoPak', sura: 2, aya: '255')
    ```

| | `1441H` | `1405H` | `IndoPak` |
|---|---|---|---|
| Font | DigitalKhatt New Madina | DigitalKhatt Old Madina | DigitalKhatt IndoPak |
| Text | [Tanzil](https://tanzil.net) Uthmani, with the 1441H print's pause marks | Tanzil Uthmani | DigitalKhatt's IndoPak text (IndoPak spelling) |
| Line breaks | the 1441H print (King Fahd Complex page data) | the 1405H print | DigitalKhatt's IndoPak layout |
| Pages | 604 | 604 | 610 |

The value is not case sensitive. An unknown value logs a warning and falls back to `1441H`.

## How lines are justified

Lines are filled the way the print fills them: by stretching the letters themselves, with
kashida strokes and wider letter forms, rather than adding tatweel characters or squashing
whole lines. Words keep the print's gaps between them; loose lines stretch letters, and dense
lines narrow their words slightly (never the verse numbers). The text stays real text.

This uses the [DigitalKhatt](https://github.com/DigitalKhatt/digitalkhatt.org) fonts by Amine
Anane. The stretch of every word is decided when the databases are built, so the browser only
needs the font. The [design notes](../v2/design-decisions.md) explain how it was measured
against the print.

## Any size

`data-font-size` sets the size in pixels (default 16; anything from 6 to 100, decimals
allowed). The whole page scales with it, line width included:

=== "HTML"

    ```html
    <script src="https://unpkg.com/quran-madina-html@2" data-font-size="24"></script>
    ```

=== "React"

    ```jsx
    {/* layout and fontSize apply to the whole page: set them on the first component */}
    <QuranMadinaHtml fontSize={24} sura={2} aya="255" />
    ```

=== "Flutter"

    ```dart
    // per widget on Android, iOS and macOS; on the web, the first widget's apply page-wide
    QuranMadinaFlutter(fontSize: 24, sura: 2, aya: '255')
    ```
