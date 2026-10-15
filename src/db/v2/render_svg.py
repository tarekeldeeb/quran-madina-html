"""Render justified lines to SVG with real glyph outlines (no browser needed).

Used by the v2 proof of concept to compare the v1 output (tatweel + scaleX)
with v2 glyph stretching, line by line, at the same visual width.
"""
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont


class GlyphPaths:
    """Caches SVG path data for glyph ids of one font (y axis flipped)."""

    def __init__(self, font_path):
        self.font = TTFont(font_path)
        self.glyph_set = self.font.getGlyphSet()
        self.order = self.font.getGlyphOrder()
        self.upem = self.font["head"].unitsPerEm
        self.cache = {}

    def path(self, gid):
        if gid not in self.cache:
            pen = SVGPathPen(self.glyph_set)
            self.glyph_set[self.order[gid]].draw(TransformPen(pen, (1, 0, 0, -1, 0, 0)))
            self.cache[gid] = pen.getCommands()
        return self.cache[gid]


def line_group(paths, glyphs, line_width, target_width, y, x_scale=1.0,
               center=False, color="currentColor"):
    """SVG <g> for one RTL line. `glyphs` are (gid, x, y) in visual LTR order
    as HarfBuzz returns them, `line_width` their total advance (font units),
    drawn right-aligned into `target_width` (font units) at baseline `y`."""
    drawn = line_width * x_scale
    x0 = target_width - drawn
    if center:
        x0 = (target_width - drawn) / 2
    parts = [f'<g transform="translate({x0:.1f} {y:.1f}) scale({x_scale:.5f} 1)" fill="{color}">']
    for gid, gx, gy in glyphs:
        d = paths.path(gid)
        if d:
            parts.append(f'<path transform="translate({gx:.1f} {-gy:.1f})" d="{d}"/>')
    parts.append("</g>")
    return "\n".join(parts)


def hb_glyphs(buf):
    """HarfBuzz RTL buffers are in visual order (left to right) already."""
    out, x = [], 0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        out.append((info.codepoint, x + pos.x_offset, pos.y_offset))
        x += pos.x_advance
    return out, x
