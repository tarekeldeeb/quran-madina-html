"""Phase 0 probe: report a font's stretch mechanisms (axes / cvXX alternates)
and measure how feature values change word widths with HarfBuzz.

Usage:
    python src/db/v2/probe_font.py path/to/madina.otf

Requires: fonttools, uharfbuzz
"""
import sys

import uharfbuzz as hb
from fontTools.ttLib import TTFont

SAMPLE_WORDS = ["ٱلْحَمْدُ", "لِلَّهِ", "رَبِّ", "ٱلْعَٰلَمِينَ", "بِسْمِ"]
LEVELS = (0, 2, 4, 6, 9, 12)


def describe(path):
    font = TTFont(path, lazy=True)
    name = font["name"]
    print(f"{name.getDebugName(4)} | {name.getDebugName(5)}")
    print(f"license: {(name.getDebugName(13) or '')[:80]}")
    if "fvar" in font:
        for axis in font["fvar"].axes:
            print(f"axis {axis.axisTag}: {axis.minValue}..{axis.maxValue} "
                  f"(default {axis.defaultValue})")
    else:
        print("no variation axes (fvar)")
    gsub = font["GSUB"].table
    for rec in gsub.FeatureList.FeatureRecord:
        if rec.FeatureTag.startswith(("cv", "jalt", "shr", "ss")):
            print(f"GSUB feature {rec.FeatureTag}")


def shape_width(hb_font, text, features=None):
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hb_font, buf, features or {})
    missing = sum(1 for info in buf.glyph_infos if info.codepoint == 0)
    return sum(pos.x_advance for pos in buf.glyph_positions), missing


def measure(path):
    with open(path, "rb") as fh:
        hb_font = hb.Font(hb.Face(fh.read()))
    for word in SAMPLE_WORDS:
        width, missing = shape_width(hb_font, word)
        print(f"{word}: natural={width} notdef={missing}")
        for feat in ("cv01", "cv02"):
            widths = [shape_width(hb_font, word, {feat: v})[0] for v in LEVELS]
            print(f"   {feat} {LEVELS}: {widths}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    describe(sys.argv[1])
    measure(sys.argv[1])
