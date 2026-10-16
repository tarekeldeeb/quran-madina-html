"""Add position-addressed stretch features to a DigitalKhatt font.

Why: the per-letter stretching chosen by `justify.justify_line()` (cv01/cv02/
cv10-cv18 on single characters) cannot be expressed in the DOM — putting one
letter in its own <span> breaks joining and kerning. But it never changes the
glyph count of a word (checked on every stretched word of both layouts), so it
can be replayed as "replace the glyph at position k of this word".

What this adds to the font (OFL allows modified versions):
  * one AlternateSubst lookup ALT: for every glyph g, the list of stretched
    glyphs that replace it somewhere in the corpus;
  * features jp01..jpNN: feature jpKK replaces the glyph at 0-based logical
    position KK-1 of the shaping buffer (= the word span) with ALT's
    alternate number <feature value>.

In the page:  <span style='font-feature-settings: "jp04" 3, "jp06" 1'>word</span>

The new lookups are appended after every existing GSUB lookup, so they act on
the final glyphs and GPOS (kerning, cursive attachment, marks) then runs on the
exact sequence HarfBuzz produces with the original per-letter features.
"""
# pylint: disable=too-many-locals
# pylint: disable=no-member  # otTables classes are built dynamically by fontTools
import argparse
import json

import uharfbuzz as hb
from fontTools.otlLib import builder as otl
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables as ot

MAX_POSITIONS = 99


def tag_for(position):
    """0-based glyph position -> feature tag."""
    return f"jp{position + 1:02d}"


def logical_glyphs(font, text, features=None):
    """Glyph ids of `text` shaped as one buffer, in logical (buffer) order."""
    buf = hb.Buffer()
    buf.add_codepoints([ord(c) for c in text])
    buf.direction, buf.script, buf.language = "rtl", "Arab", "ar"
    buf.cluster_level = hb.BufferClusterLevel.MONOTONE_CHARACTERS
    hb.shape(font, buf, features or {})
    gids = [info.codepoint for info in buf.glyph_infos]
    return gids[::-1] if buf.direction == "rtl" else gids


def word_replacements(font, word_text, hb_features):
    """[(position, from_gid, to_gid)] turning the plain word into the stretched one."""
    plain = logical_glyphs(font, word_text)
    stretched = logical_glyphs(font, word_text, hb_features)
    if len(plain) != len(stretched):
        raise ValueError(f"glyph count changed for {word_text!r}")
    return [(i, a, b) for i, (a, b) in enumerate(zip(plain, stretched)) if a != b]


class AlternateTable:
    """Collects g -> [stretched variants]; values are 1-based indexes."""

    def __init__(self):
        self.alts = {}

    def value(self, src, dst):
        """Feature value (1-based variant index) turning glyph src into dst; adds dst if new."""
        options = self.alts.setdefault(src, [])
        if dst not in options:
            options.append(dst)
        return options.index(dst) + 1

    def to_json(self):
        """The table as JSON-serialisable data."""
        return {str(k): v for k, v in self.alts.items()}

    @classmethod
    def from_json(cls, data):
        """Inverse of to_json()."""
        table = cls()
        table.alts = {int(k): list(v) for k, v in data.items()}
        return table


def css_for(replacements, table):
    """{tag: value} for one word."""
    out = {}
    for pos, src, dst in replacements:
        if pos >= MAX_POSITIONS:
            raise ValueError("word too long for position features")
        out[tag_for(pos)] = table.value(src, dst)
    return out


def _all_glyph_coverage(glyph_order):
    return otl.buildCoverage(glyph_order, {g: i for i, g in enumerate(glyph_order)})


def patch_font(src_path, out_path, table, positions, family=None):
    """Write a copy of the font with ALT + jp01..jpNN (NN = `positions`)."""
    font = TTFont(src_path)
    order = font.getGlyphOrder()
    gsub = font["GSUB"].table
    lookups = gsub.LookupList.Lookup

    alt_map = {order[g]: [order[x] for x in xs] for g, xs in table.alts.items()}
    alt_lookup = otl.buildLookup([otl.buildAlternateSubstSubtable(alt_map)])
    lookups.append(alt_lookup)
    alt_index = len(lookups) - 1

    def chain_subtable(backtrack, with_lookup):
        st = ot.ChainContextSubst()
        st.Format = 3
        st.BacktrackGlyphCount = backtrack
        st.BacktrackCoverage = [_all_glyph_coverage(order) for _ in range(backtrack)]
        st.InputGlyphCount = 1
        st.InputCoverage = [_all_glyph_coverage(order)]
        st.LookAheadGlyphCount = 0
        st.LookAheadCoverage = []
        records = []
        if with_lookup:
            rec = ot.SubstLookupRecord()
            rec.SequenceIndex, rec.LookupListIndex = 0, alt_index
            records.append(rec)
        st.SubstLookupRecord = records
        st.SubstCount = len(records)
        return st

    new_features = []
    for pos in range(positions):
        # first subtable: "more than pos glyphs before me" -> match, do nothing
        # second: exactly pos glyphs before me (buffer start) -> substitute
        lookup = otl.buildLookup([chain_subtable(pos + 1, False), chain_subtable(pos, True)])
        lookups.append(lookup)
        new_features.append((tag_for(pos), len(lookups) - 1))
    gsub.LookupList.LookupCount = len(lookups)

    feat_list = gsub.FeatureList
    added = []
    for tag, lookup_index in new_features:
        rec = ot.FeatureRecord()
        rec.FeatureTag = tag
        rec.Feature = ot.Feature()
        rec.Feature.FeatureParams = None
        rec.Feature.LookupListIndex = [lookup_index]
        rec.Feature.LookupCount = 1
        feat_list.FeatureRecord.append(rec)
        added.append(len(feat_list.FeatureRecord) - 1)
    feat_list.FeatureCount = len(feat_list.FeatureRecord)

    for script in gsub.ScriptList.ScriptRecord:
        langsyses = [script.Script.DefaultLangSys] + [
            r.LangSys for r in script.Script.LangSysRecord]
        for ls in langsyses:
            if ls is None:
                continue
            ls.FeatureIndex = list(ls.FeatureIndex) + added
            ls.FeatureCount = len(ls.FeatureIndex)

    # FeatureList must stay sorted by tag for some consumers; sort and remap.
    _sort_feature_list(gsub)

    if family:
        _rename(font, family)
    font.save(out_path)


def _sort_feature_list(gsub):
    recs = gsub.FeatureList.FeatureRecord
    order = sorted(range(len(recs)), key=lambda i: recs[i].FeatureTag)
    remap = {old: new for new, old in enumerate(order)}
    gsub.FeatureList.FeatureRecord = [recs[i] for i in order]
    for script in gsub.ScriptList.ScriptRecord:
        langsyses = [script.Script.DefaultLangSys] + [
            r.LangSys for r in script.Script.LangSysRecord]
        for ls in langsyses:
            if ls is None:
                continue
            ls.FeatureIndex = sorted(remap[i] for i in ls.FeatureIndex)
            if ls.ReqFeatureIndex != 0xFFFF:
                ls.ReqFeatureIndex = remap[ls.ReqFeatureIndex]


def _rename(font, family):
    name = font["name"]
    old_full = name.getDebugName(4) or ""
    for rec in list(name.names):
        if rec.nameID in (1, 16):
            rec.string = family
        elif rec.nameID == 4:
            rec.string = f"{family} Regular"
        elif rec.nameID == 6:
            rec.string = family.replace(" ", "") + "-Regular"
        elif rec.nameID == 3:
            rec.string = f"{family}; modified from {old_full}"
    if "CFF " in font:
        cff = font["CFF "].cff
        cff.fontNames = [family.replace(" ", "") + "-Regular"]


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Add jpNN position features to a font")
    ap.add_argument("font")
    ap.add_argument("alternates_json", help="AlternateTable.to_json() output")
    ap.add_argument("out")
    ap.add_argument("--positions", type=int, required=True)
    ap.add_argument("--family")
    a = ap.parse_args()
    with open(a.alternates_json, encoding="utf-8") as fh:
        tbl = AlternateTable.from_json(json.load(fh))
    patch_font(a.font, a.out, tbl, a.positions, a.family)
