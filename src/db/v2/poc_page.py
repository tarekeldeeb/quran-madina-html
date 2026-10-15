"""Phase 1 proof of concept: render one Madina page twice, as SVG.

  top    : v1 — current DB text (with build-inserted tatweels) in the v1 font,
           justified with the stored scaleX, as the browser would show it
  bottom : v2 — DigitalKhatt Old Madina font, justified by stretching letters
           with HarfBuzz (src/db/v2/justify.py)

Usage:
  python src/db/v2/poc_page.py PAGE V1_DB.json V1_FONT V2_FONT DK_TEXT.ts OUT.svg
         [--line-width 16400] [--space-stretch 0.5] [--exhaustive]

DK_TEXT.ts is DigitalKhatt's quran_text_old_madinah.ts (same line breaks as
the 1405H print), used here because its encoding is the one the font expects.
"""
import argparse
import io
import json
import re
from collections import defaultdict

import uharfbuzz as hb
from fontTools.ttLib import TTFont

import justify
import render_svg

PANEL_PX = 900


def load_hb_font(path):
    tt = TTFont(path)
    tt.flavor = None                       # woff2 -> sfnt for HarfBuzz
    data = io.BytesIO()
    tt.save(data)
    return hb.Font(hb.Face(data.getvalue())), data


def v1_lines(db, page):
    lines = defaultdict(lambda: ["", None])
    for sura in db["suras"]:
        for aya in sura["ayas"]:
            if aya["p"] != page:
                continue
            for part in aya["r"]:
                entry = lines[part["l"]]
                entry[0] += part["t"]
                entry[1] = part["s"]
    return [lines[k] for k in sorted(lines)]


def dk_lines(path, page):
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    pages = re.findall(r"\[\s*((?:'[^']*',?\s*)+)\]", src)
    return re.findall(r"'([^']*)'", pages[page - 1])


def panel(title, rows, target, pitch, y_offset):
    scale = PANEL_PX / target
    body = "\n".join(rows)
    height = pitch * (len(rows) + 0.6)
    svg = (f'<text x="{PANEL_PX}" y="{y_offset + 22}" text-anchor="end" '
           f'font-family="sans-serif" font-size="18" fill="#666">{title}</text>\n'
           f'<g transform="translate(0 {y_offset + 30}) scale({scale:.6f})">'
           f'{body}</g>')
    return svg, height * scale + 40


def main(page, v1_db, v1_font_path, v2_font_path, dk_text, out,
         line_width=16400, space_stretch=0.5, exhaustive=True):
    with open(v1_db, encoding="utf-8") as fh:
        db = json.load(fh)
    # v1
    font1, data1 = load_hb_font(v1_font_path)
    paths1 = render_svg.GlyphPaths(io.BytesIO(data1.getvalue()))
    target1 = db["line_width"] / db["font_size"] * paths1.upem
    pitch1 = target1 / 13
    rows1 = []
    for n, (text, s) in enumerate(v1_lines(db, page), start=1):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(font1, buf)
        glyphs, w = render_svg.hb_glyphs(buf)
        center = s == -1
        rows1.append(render_svg.line_group(paths1, glyphs, w, target1, n * pitch1,
                                           1.0 if center else s, center))
    # v2
    with open(v2_font_path, "rb") as fh:
        font2 = hb.Font(hb.Face(fh.read()))
    paths2 = render_svg.GlyphPaths(v2_font_path)
    pitch2 = line_width / 13
    rows2, report = [], []
    for n, text in enumerate(dk_lines(dk_text, page), start=1):
        res = justify.justify_line(font2, text, line_width, space_stretch=space_stretch,
                                  exhaustive=exhaustive)
        glyphs, w = justify.line_glyphs(font2, text, res)
        rows2.append(render_svg.line_group(paths2, glyphs, w, line_width, n * pitch2,
                                           res.x_scale))
        report.append((n, res.natural_width, round(w * res.x_scale), len(res.features),
                       round(res.simple_spacing), round(res.x_scale, 3)))
    p1, h1 = panel(f"v1 — {db['font_family']}, tatweel + scaleX (page {page})",
                   rows1, target1, pitch1, 0)
    p2, h2 = panel("v2 — DigitalKhatt Old Madina, letters stretched with HarfBuzz",
                   rows2, line_width, pitch2, h1 + 10)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-20 -10 {PANEL_PX + 40} '
           f'{h1 + h2 + 30}" width="{PANEL_PX + 40}" height="{h1 + h2 + 30}">'
           f'<rect x="-20" y="-10" width="100%" height="100%" fill="#fffdf6"/>'
           f'{p1}{p2}</svg>')
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(svg)
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    for name in ("page", "v1_db", "v1_font", "v2_font", "dk_text", "out"):
        ap.add_argument(name)
    ap.add_argument("--line-width", type=int, default=16400,
                    help="v2 line width in font units (DigitalKhatt site: 15628)")
    ap.add_argument("--space-stretch", type=float, default=0.5,
                    help="max space growth before stretching letters (reference: 1.0)")
    ap.add_argument("--exhaustive", action=argparse.BooleanOptionalAction, default=True,
                    help="keep stretching other letters after an overflow")
    a = ap.parse_args()
    for row in main(int(a.page), a.v1_db, a.v1_font, a.v2_font, a.dk_text, a.out,
                    a.line_width, a.space_stretch, a.exhaustive):
        n, natural, final, stretched, space, xscale = row
        print(f"line {n:2d} natural={natural:5d} final={final:5d} "
              f"stretched_chars={stretched:2d} space={space:3d} xscale={xscale}")
