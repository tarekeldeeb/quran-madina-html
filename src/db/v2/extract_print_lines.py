"""Extract the 1441H print's line breaks from King Fahd Complex page data.

Source: the `quran-qcf4` npm package (JSON data MIT, (c) Mohamad Hajj Rabee),
which lists, for each of the 604 pages of the 1441H Madina Mushaf, the words of
every line as KFGQPC's QCF4 font draws them (each word glyph is traced from the
print). Only *where lines break* is kept here — no glyphs, no text:

    npm pack quran-qcf4@1.1.0 && tar xzf quran-qcf4-1.1.0.tgz
    python src/db/v2/extract_print_lines.py package/ src/db/v2/data/print-1441H-lines.json

Output: {"source", "pages": [[line, ...15] x 604]} where a line is
  {"k": "sura"|"bism"|"text", "a": "s:a:i", "b": "s:a:i", "w": <width ratio>}
  a/b: first/last token of the line as sura:aya:index, index counting the
       aya's words from 1 and its number marker last, like Tanzil tokens
       (the print's separate sajda sign ۩ belongs to the previous word);
  w:   only for text lines narrower than a full line (pages 1-2, sura ends),
       measured from the glyphs' advances.
"""
import json
import os
import statistics
import sys

from fontTools.ttLib import TTFont


def main(pkg, out):
    fonts = {}

    def advance(font, code):
        if font not in fonts:
            t = TTFont(os.path.join(pkg, "fonts-woff2", f"{font}_W.woff2"))
            fonts[font] = (t.getBestCmap(), t["hmtx"])
        cmap, hmtx = fonts[font]
        return hmtx[cmap[code]][0]

    pages, widths = [], []
    for p in range(1, 605):
        with open(os.path.join(pkg, "pages", f"{p:03d}.json"), encoding="utf-8") as fh:
            data = json.load(fh)
        lines = []
        for line in data["lines"]:
            words = line["words"]
            kinds = {w["type"] for w in words}
            if "surah_header" in kinds:
                lines.append({"k": "sura"})
                continue
            if "bismillah" in kinds:
                lines.append({"k": "bism"})
                continue
            toks, shift = [], {}
            for w in words:
                if w["type"] not in ("word", "end"):
                    continue          # ۞ is drawn on its own; Tanzil attaches it to the next word
                key = w["verse_key"]
                if w["text"].startswith("#"):          # sajda sign: part of the previous word
                    shift[key] = shift.get(key, 0) + 1
                    continue
                toks.append(f"{key}:{w['position'] - shift.get(key, 0)}")
            adv = sum(advance(w["font"], w["code"]) for w in words if w["type"] in ("word", "end"))
            widths.append(adv)
            lines.append({"k": "text", "a": toks[0], "b": toks[-1], "_adv": adv})
        pages.append(lines)
    full = statistics.median(widths)
    for lines in pages:
        for line in lines:
            adv = line.pop("_adv", None)
            if adv is not None and adv / full < 0.9:
                line["w"] = round(adv / full, 4)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"source": "KFGQPC 1441H Madina Mushaf line breaks, via quran-qcf4 1.1.0 (MIT)",
                   "pages": pages}, fh, separators=(",", ":"))
    narrow = sum(1 for p in pages for l in p if "w" in l)
    print(f"{sum(len(p) for p in pages)} lines, {narrow} narrower than full; full width {full}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
