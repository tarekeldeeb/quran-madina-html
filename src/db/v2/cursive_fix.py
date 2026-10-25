"""Make a v2 font join on Apple's CoreText exactly as it does in HarfBuzz.

    python src/db/v2/cursive_fix.py assets/db/v2/Madina-1441H.json   (DB + its woff2, in place)

Why: DigitalKhatt's fonts join letters with cursive attachment ('curs') in several lookups,
one of them flagged RightToLeft and the others not. HarfBuzz (Chrome, Firefox, Android)
resolves the mixed directions by reversing attachment chains; CoreText (every iOS browser,
Safari) does not, so the heights at those joins come out wrong and letters show steps (iPhone
screenshots, 2.2.1). Two encoding details break CoreText too: the CGJ (U+034F) the encoding
puts between a hamza and its vowel is a base glyph that sits inside a joint, which HarfBuzz
skips (default ignorable) and CoreText does not.

What this does, for every layout, verified word by word with HarfBuzz:
  * the font: every cursive lookup loses its RightToLeft flag, so each chain has one
    direction and one root (its first glyph) in both engines;
  * that alone moves some letter groups up or down (the chain root differs), so the font gets
    position features `z<p><dd>`: shift the glyph at buffer position p (base 36) by dd font
    units (two base-36 digits, value + 648) before the joining runs; the shift carries the
    glyph's whole chain;
  * the DB: each word gets the z features its HarfBuzz rendering needs in `f` (bare tags,
    `jp04=3,z12k`, with the stretch features, for justified lines). Unstretched renders
    (titles, basmala, inline quotes) take the z tags of `f`, unless the part has `g` with a
    non-null entry for the word: then that ("" = none). Sura names (the frame header) get
    theirs in `nf` (one per word). CGJs go, except where HarfBuzz needs them (strip_cgj).
The result shapes exactly like the original font in HarfBuzz (checked for every word; the
script fails otherwise), so Chrome is pixel-identical, and CoreText now joins.
"""
# pylint: disable=no-member  # otTables classes are built dynamically by fontTools
import argparse
import io
import json
import os
import re
import sys

import uharfbuzz as hb
from fontTools.otlLib import builder as otl
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables as ot

B36 = "0123456789abcdefghijklmnopqrstuvwxyz"
DELTA_BIAS = 648                       # 2 base-36 digits hold -648..647
PROBE = 1000                           # the shift used to find which glyphs a root carries
CGJ = "͏"
# CGJs HarfBuzz needs: they keep these marks in the encoding's order (removing them changes the
# shaping of a handful of words: sukun + sakta, dagger alef + hamza, damma + U+08F3, ...)
_KEEP_CGJ = re.compile("(?<=[ُْٰۢ])͏(?=[ْۜٔࣳٓ])")


def strip_cgj(word):
    """The word without the CGJs CoreText trips on (all but _KEEP_CGJ's)."""
    return re.sub(CGJ, lambda m: m.group(0) if _KEEP_CGJ.match(word, m.start()) else "", word)


def z_tag(pos, delta):
    """(buffer position, y shift) -> feature tag."""
    if not 0 <= pos < 36 or not -DELTA_BIAS <= delta < DELTA_BIAS:
        raise ValueError(f"z feature out of range: position {pos}, shift {delta}")
    v = delta + DELTA_BIAS
    return f"z{B36[pos]}{B36[v // 36]}{B36[v % 36]}"


def _probe_tag(pos):
    return f"zp{B36[pos // 36]}{B36[pos % 36]}"


def _lookup_type(lookup):
    if lookup.LookupType == 9:
        return lookup.SubTable[0].ExtensionLookupType if lookup.SubTable else 0
    return lookup.LookupType


def uniform_cursive(font):
    """Clear RightToLeft on every cursive lookup; returns how many changed."""
    n = 0
    for lookup in font["GPOS"].table.LookupList.Lookup:
        if _lookup_type(lookup) == 3 and lookup.LookupFlag & 1:
            lookup.LookupFlag &= ~1
            n += 1
    return n


def _pos_lookup_records(st):
    """Every PosLookupRecord of a (chain) context positioning subtable, any format."""
    out = list(getattr(st, "PosLookupRecord", None) or [])
    for attr in ("PosRuleSet", "PosClassSet", "ChainPosRuleSet", "ChainPosClassSet"):
        for rule_set in filter(None, getattr(st, attr, None) or []):
            for name in ("PosRule", "PosClassRule", "ChainPosRule", "ChainPosClassRule"):
                for rule in getattr(rule_set, name, None) or []:
                    out.extend(rule.PosLookupRecord)
    return out


def _insert_lookups_first(font, new):
    """Put `new` GPOS lookups before all others, renumbering every reference."""
    gpos = font["GPOS"].table
    k = len(new)
    for lookup in gpos.LookupList.Lookup:
        for st in lookup.SubTable:
            for rec in _pos_lookup_records(st.ExtSubTable if lookup.LookupType == 9 else st):
                rec.LookupListIndex += k
    for rec in gpos.FeatureList.FeatureRecord:
        rec.Feature.LookupListIndex = [i + k for i in rec.Feature.LookupListIndex]
    gpos.LookupList.Lookup = new + gpos.LookupList.Lookup
    gpos.LookupList.LookupCount = len(gpos.LookupList.Lookup)


def _chain_pos(order, backtrack, lookup_index):
    """Match any glyph with at least `backtrack` glyphs before it; apply lookup_index."""
    cov = otl.buildCoverage(order, {g: i for i, g in enumerate(order)})
    st = ot.ChainContextPos()
    st.Format = 3
    st.BacktrackGlyphCount = backtrack
    st.BacktrackCoverage = [cov] * backtrack
    st.InputGlyphCount = 1
    st.InputCoverage = [cov]
    st.LookAheadGlyphCount = 0
    st.LookAheadCoverage = []
    records = []
    if lookup_index is not None:
        rec = ot.PosLookupRecord()
        rec.SequenceIndex, rec.LookupListIndex = 0, lookup_index
        records.append(rec)
    st.PosLookupRecord = records
    st.PosCount = len(records)
    return st


def _register(font, tags_lookups):
    gpos = font["GPOS"].table
    fl = gpos.FeatureList
    added = []
    for tag, index in tags_lookups:
        rec = ot.FeatureRecord()
        rec.FeatureTag = tag
        rec.Feature = ot.Feature()
        rec.Feature.FeatureParams = None
        rec.Feature.LookupListIndex = [index]
        rec.Feature.LookupCount = 1
        fl.FeatureRecord.append(rec)
        added.append(len(fl.FeatureRecord) - 1)
    recs = fl.FeatureRecord
    order = sorted(range(len(recs)), key=lambda i: recs[i].FeatureTag)
    remap = {old: new for new, old in enumerate(order)}
    fl.FeatureRecord = [recs[i] for i in order]
    fl.FeatureCount = len(fl.FeatureRecord)
    for script in gpos.ScriptList.ScriptRecord:
        for ls in [script.Script.DefaultLangSys] + [r.LangSys for r in script.Script.LangSysRecord]:
            if ls is None:
                continue
            ls.FeatureIndex = sorted(remap[i] for i in list(ls.FeatureIndex) + added)
            ls.FeatureCount = len(ls.FeatureIndex)
            if ls.ReqFeatureIndex != 0xFFFF:
                ls.ReqFeatureIndex = remap[ls.ReqFeatureIndex]


def add_shift_features(font, pairs, probes=0):
    """z features for the (position, shift) pairs; with probes, also zpNN (shift PROBE at NN)."""
    order = font.getGlyphOrder()
    rev = font.getReverseGlyphMap()
    shifts = sorted({d for _, d in pairs} | ({PROBE} if probes else set()))
    new, index = [], {}
    for d in shifts:
        value = otl.buildValue({"YPlacement": d})
        new.append(otl.buildLookup([otl.buildSinglePosSubtable({g: value for g in order}, rev)]))
        index[d] = len(new) - 1
    tags = []
    # first subtable: more than pos glyphs before -> match, nothing; second: exactly pos -> shift
    for pos, d in sorted(pairs):
        new.append(_at_position(order, pos, index[d]))
        tags.append((z_tag(pos, d), len(new) - 1))
    for pos in range(probes):
        new.append(_at_position(order, pos, index[PROBE]))
        tags.append((_probe_tag(pos), len(new) - 1))
    _insert_lookups_first(font, new)
    _register(font, tags)


def _at_position(order, pos, lookup_index):
    """A lookup applying lookup_index to the glyph at buffer position pos only."""
    return otl.buildLookup([_chain_pos(order, pos + 1, None), _chain_pos(order, pos, lookup_index)])


def _hb(font):
    data = io.BytesIO()
    font.save(data)
    return hb.Font(hb.Face(data.getvalue()))


def _copy(font):
    data = io.BytesIO()
    font.save(data)
    data.seek(0)
    return TTFont(data)


def shape(font, text, feats):
    """[(gid, x_advance, x_offset, y_offset)] in logical order."""
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, feats)
    out = [(i.codepoint, p.x_advance, p.x_offset, p.y_offset)
           for i, p in zip(buf.glyph_infos, buf.glyph_positions)]
    return out[::-1]


def features(css):
    """'jp04=3,z12k=1' -> {'jp04': 3, 'z12k': 1}."""
    out = {}
    for kv in filter(None, (css or "").split(",")):
        k, _, v = kv.partition("=")
        out[k] = int(v or 1)
    return out


class Corrector:  # pylint: disable=too-few-public-methods
    """Finds the z features that make the uniform font render a word like the original."""

    def __init__(self, original):
        original = _copy(original)
        original.flavor = None
        self.ref = _hb(original)
        flat = _copy(original)
        uniform_cursive(flat)
        self.flat_tt = flat
        self.flat = _hb(flat)
        probe = _copy(flat)
        add_shift_features(probe, [], probes=36)
        self.probe = _hb(probe)
        marks = original["GDEF"].table.GlyphClassDef.classDefs
        self.mark = {original.getGlyphID(g) for g, c in marks.items() if c == 3}
        self.cache = {}

    def pairs(self, word, css):
        """[(position, shift)] for `word` (as stored, CGJs included) with stretch css."""
        key = (word, css)
        if key not in self.cache:
            self.cache[key] = self._pairs(word, features(css))
        return self.cache[key]

    def _pairs(self, word, feats):
        want = shape(self.ref, word, feats)
        text = strip_cgj(word)
        got = shape(self.flat, text, feats)
        if [g[:3] for g in want] != [g[:3] for g in got]:
            raise ValueError(f"{word!r}: glyphs or advances change")
        cur = [g[3] for g in got]
        out = []
        # walk the bases in reading order; one that sits wrong is the root of its chain (all
        # before it are right), so shifting it moves exactly the glyphs that need it
        for i, g in enumerate(want):
            if g[0] in self.mark or cur[i] == g[3]:
                continue
            probe = dict(feats)
            probe[_probe_tag(i)] = 1
            moved = [j for j, (p, q) in enumerate(zip(shape(self.probe, text, probe), got))
                     if p[3] - q[3] == PROBE]
            if i not in moved:
                raise ValueError(f"{word!r}: glyph {i} is not a chain root")
            d = g[3] - cur[i]
            for j in moved:
                cur[j] += d
            out.append((i, d))
        return out


def _css(base, pairs):
    return ",".join(filter(None, [base] + [z_tag(p, d) for p, d in pairs]))


def word_features(part, j, justified):
    """The feature string the runtime gives word j of a part (see the module docstring)."""
    f = (part.get("f") or [])
    f = f[j] if j < len(f) else ""
    if justified:
        return f
    g = part.get("g")
    if g is not None and g[j] is not None:
        return g[j]
    return ",".join(t for t in f.split(",") if t.startswith("z"))


def fix(db, font):  # pylint: disable=too-many-locals
    """Rewrite db (in memory) and return the fixed font; raises if anything is off."""
    if any(r.FeatureTag.startswith("z") for r in font["GPOS"].table.FeatureList.FeatureRecord):
        raise ValueError("font already has z features: run on a freshly built font")
    corr = Corrector(font)
    used = set()
    checks = []
    parts = [part for sura in db["suras"] for aya in sura["ayas"] for part in aya["r"]]
    for part in parts:
        words = part["t"].split(" ") if part["t"] else []
        fs = part.get("f") or [""] * len(words)
        new_f, new_g = [], []
        for w, css in zip(words, fs):
            if not w:
                new_f.append(css)
                new_g.append(None)
                continue
            checks.append((part, len(new_f), w, css))
            justified = corr.pairs(w, css)
            plain = corr.pairs(w, "")
            used.update(justified)
            used.update(plain)
            new_f.append(_css(css, justified))
            # null: the unstretched word takes f's z tags (the usual case)
            new_g.append(None if plain == justified else _css("", plain))
        part["t"] = " ".join(strip_cgj(w) for w in words)
        part["f"] = new_f
        if any(g is not None for g in new_g):
            part["g"] = new_g
        else:
            part.pop("g", None)
    # sura names (the multiline frame's header): unstretched words, own list `nf`
    names = []
    for sura in db["suras"]:
        words = sura["name"].split(" ")
        pairs = [corr.pairs(w, "") if w else [] for w in words]
        for w, p in zip(words, pairs):
            used.update(p)
            if w:
                names.append((w, strip_cgj(w), _css("", p)))
        sura["name"] = " ".join(strip_cgj(w) for w in words)
        if any(pairs):
            sura["nf"] = [_css("", p) for p in pairs]
        else:
            sura.pop("nf", None)
    fixed = corr.flat_tt
    add_shift_features(fixed, sorted(used))
    # verify: the fixed font + DB render every word exactly like the original font + old DB
    check = _hb(fixed)
    for (w, css), pairs in corr.cache.items():
        feats = features(css)
        feats.update({z_tag(p, d): 1 for p, d in pairs})
        if shape(check, strip_cgj(w), feats) != shape(corr.ref, w, features(css)):
            raise ValueError(f"{w!r} [{css}]: fixed font renders it differently")
    # ... and the DB as stored, read the way the runtime reads it
    for w, word, css in names:
        if shape(check, word, features(css)) != shape(corr.ref, w, {}):
            raise ValueError(f"sura name word {w!r}: stored features render it differently")
    done = {}
    for part, j, w, css in checks:
        word = part["t"].split(" ")[j]
        for justified, want_css in ((True, css), (False, "")):
            key = (word, word_features(part, j, justified), w, want_css)
            if key in done:
                continue
            done[key] = True
            if shape(check, word, features(key[1])) != shape(corr.ref, w, features(want_css)):
                raise ValueError(f"{w!r}: stored features render it differently ({key[1]})")
    return fixed, len(used), len(corr.cache)


def main():
    """Fix a DB and its woff2 in place."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n", maxsplit=1)[0])
    ap.add_argument("db")
    ap.add_argument("--font", help="default: the DB's font_url next to it")
    a = ap.parse_args()
    with open(a.db, encoding="utf-8") as fh:
        db = json.load(fh)
    font_path = a.font or os.path.join(os.path.dirname(a.db), os.path.basename(db["font_url"]))
    font = TTFont(font_path)
    font.flavor = None
    fixed, n_pairs, n_words = fix(db, font)
    fixed.flavor = "woff2" if font_path.endswith(".woff2") else None
    fixed.save(font_path)
    with open(a.db, "w", encoding="utf-8") as fh:
        json.dump(db, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"{a.db}: {n_words} word forms verified, {n_pairs} shift features; wrote {font_path}")


if __name__ == "__main__":
    sys.exit(main())
