"""Ink profiles of words: where each word's ink starts and ends, row by row.

Two neighbouring words in a line don't collide where their *bounding boxes*
meet — tails, descenders and marks interleave — but where their ink meets in
the same horizontal band. A profile keeps, for every band of `ROW` font units,
the leftmost and rightmost ink (x from the word's box origin), so the space
needed for a given ink-to-ink clearance is exact to one band, like the print.
"""
import numpy as np
from fontTools.misc.transform import Transform
from fontTools.pens.freetypePen import FreeTypePen
from fontTools.pens.transformPen import TransformPen

ROW = 20                 # font units per band / per column
Y_MIN, Y_MAX = -1400, 2200


class Profile:
    __slots__ = ("advance", "left", "right")

    def __init__(self, advance, left, right):
        self.advance = advance      # font units
        self.left = left            # per band: leftmost ink x (nan: no ink)
        self.right = right          # per band: rightmost ink x


def from_pen(pen, advance, scale=1.0):
    """Profile of what was drawn into `pen`, in the pen's units; `scale` = units
    per em / 1000, so bands stay ROW thousandths of an em."""
    s = 1.0 / (ROW * scale)
    pad = 400 * scale
    width = int((advance + 2 * pad) * s) + 2
    height = int((Y_MAX - Y_MIN) * scale * s)
    arr = pen.array(width=width, height=height,
                    transform=Transform(s, 0, 0, s, pad * s, -Y_MIN * scale * s),
                    contain=False) > 0.25
    has = arr.any(axis=1)
    cols = np.arange(width)
    left = np.where(has, np.where(arr, cols, width).min(axis=1), np.nan)
    right = np.where(has, np.where(arr, cols, -1).max(axis=1) + 1, np.nan)
    to_units = lambda c: c / s - pad
    return Profile(advance, to_units(left), to_units(right))


def shaped_profile(font, buf):
    """Profile of a shaped HarfBuzz buffer (one word)."""
    pen = FreeTypePen(None)
    x = 0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        font.draw_glyph_with_pen(info.codepoint,
                                 TransformPen(pen, (1, 0, 0, 1, x + pos.x_offset, pos.y_offset)))
        x += pos.x_advance
    return from_pen(pen, x)


def clearance_offset(right_word, left_word, c_right=1.0, c_left=1.0):
    """Smallest ink-to-ink distance between two words placed box to box (no
    space), the right one scaled c_right, the left one c_left, horizontally.
    Adding a space s makes the clearance offset + s."""
    lk = right_word.left * c_right
    rg = (left_word.advance - left_word.right) * c_left
    both = ~np.isnan(lk) & ~np.isnan(rg)
    if both.any():
        return float(np.min(lk[both] + rg[both]))
    # no shared band (e.g. a mark-only word): fall back to the boxes
    return float(np.nanmin(lk) + np.nanmin(rg)) if np.isfinite(np.nanmin(lk)) else 0.0
