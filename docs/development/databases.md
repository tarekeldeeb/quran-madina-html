# Building the databases

The runtime reads one database per print from `assets/db/v2/`. Each holds the text, the
line breaks, each word's stretch, and the spacing of every line, all in em so that one database
serves every font size.

## Inputs

- The Quran text from [Tanzil](https://tanzil.net/download/): **Uthmani**, with pause marks,
  sajda signs and rub-el-hizb signs.
- A checkout of [digitalkhatt.org](https://github.com/DigitalKhatt/digitalkhatt.org), for the
  fonts and the 1405H and IndoPak layouts.

## Build

```bash
python src/db/v2/build_v2.py --layout 1441H --tanzil quran-uthmani.txt --dk-src ../digitalkhatt.org/ClientApp/src
python src/db/v2/build_v2.py --layout 1405H --tanzil quran-uthmani.txt --dk-src ../digitalkhatt.org/ClientApp/src
python src/db/v2/build_v2.py --layout IndoPak --dk-src ../digitalkhatt.org/ClientApp/src

# split each database per juz', as the runtime loads it
for db in Madina-1441H Madina-1405H IndoPak-15; do
  python src/db/shard_db.py assets/db/v2/$db.json assets/db/v2
done

# check every line's width with the font
python src/db/v2/check_v2_db.py assets/db/v2/Madina-1441H.json
```

## How it works

- **Fonts:** DigitalKhatt's fonts, patched with features that pick a stretched form of the
  letter at a given position in a word. HarfBuzz decides each word's stretch at build time; the
  browser only applies one `font-feature-settings` per word. Apple's text engine ignores
  feature values, so the fonts also carry an on/off feature per stretched form, which is what
  the browser actually gets.
- **Line breaks:** the 1441H print's, from the King Fahd Complex page data; DigitalKhatt's
  layouts for 1405H and IndoPak.
- **Fitting a line:** the gaps between words are kept within the print's measured range.
  Loose lines stretch letters; dense lines narrow their words slightly; scaling the whole line
  is a last resort.

The [design decisions](../v2/design-decisions.md) record the measurements behind each choice.

## Version 1 databases

`npm run build-db` still rebuilds the 1.x databases in `assets/db/`. The 2.x runtime doesn't
read them, and they are no longer published.
