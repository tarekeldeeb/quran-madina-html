"""Check a v2 DB against its patched font with HarfBuzz.

    python src/db/v2/check_v2_db.py assets/db/v2/Madina-1441H.json [--font path]

Checks:
  * structure: 604 pages; each sura has its 2 decoration slots; every aya ends
    with its own number; one feature entry per word
  * every justified line: words (shaped one by one with the patched font and
    their features, as the browser does) + spaces == line width
"""
import argparse
import io
import json
import os
import sys

import uharfbuzz as hb
from fontTools.ttLib import TTFont

sys.path.insert(0, os.path.dirname(__file__))
import tanzil_encoding as enc


def css_to_features(css):
    if not css:
        return {}
    return {k: int(v) for k, v in (item.split("=") for item in css.split(","))}


def width(font, text, feats):
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, feats)
    return sum(p.x_advance for p in buf.glyph_positions)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ap.add_argument("--font")
    a = ap.parse_args()
    with open(a.db, encoding="utf-8") as fh:
        db = json.load(fh)
    font_path = a.font or os.path.join(os.path.dirname(a.db), os.path.basename(db["font_url"]))
    tt = TTFont(font_path)          # HarfBuzz reads sfnt, not woff2
    tt.flavor = None
    data = io.BytesIO()
    tt.save(data)
    font = hb.Font(hb.Face(data.getvalue()))
    errors = []
    if len(db["lines"]) != 604:
        errors.append(f"{len(db['lines'])} pages")
    for si, sura in enumerate(db["suras"]):
        if len(sura["ayas"]) < 3:
            errors.append(f"sura {si + 1}: no ayas")
        for ai, aya in enumerate(sura["ayas"][2:], start=1):
            for part in aya["r"]:
                if len(part["t"].split()) != len(part["f"]):
                    errors.append(f"{si + 1}:{ai} words/features mismatch")
            last = aya["r"][-1]["t"].split()[-1]
            if last != enc.aya_number(ai):
                errors.append(f"{si + 1}:{ai} ends with {last!r}")
    # rebuild lines with pages (parts carry only the line; page changes go with "p")
    lines = {}
    for sura in db["suras"]:
        for ai, aya in enumerate(sura["ayas"][2:], start=2):
            page = aya["p"]
            prev_line = None
            for part in aya["r"]:
                if prev_line is not None and part["l"] < prev_line:
                    page += 1
                prev_line = part["l"]
                lines.setdefault((page, part["l"]), []).extend(zip(part["t"].split(), part["f"]))
    checked = worst = 0
    for (page, line), words in lines.items():
        row = db["lines"][page - 1][line - 1]
        if row["k"] != "text":
            continue
        spaces = row.get("s", [])
        if len(spaces) != len(words) - 1:
            errors.append(f"p{page} l{line}: {len(words)} words, {len(spaces)} spaces")
            continue
        total = sum(width(font, w, css_to_features(f)) for w, f in words) + sum(spaces) * 1000
        total *= row.get("x", 1) * row.get("z", 1)    # z: the line's font is z em
        diff = abs(total - row["w"] * 1000)
        worst = max(worst, diff)
        checked += 1
        if diff > 2:     # spaces are stored to 1e-4 em (0.1 font unit each)
            errors.append(f"p{page} l{line}: width {total:.1f} vs {row['w'] * 1000:.1f}")
    print(f"{a.db}: {checked} justified lines checked, worst width error {worst:.2f} font units")
    for e in errors[:20]:
        print("  ", e)
    print("FAIL" if errors else "PASS", f"({len(errors)} problems)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
