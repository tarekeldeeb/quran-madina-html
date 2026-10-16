"""Glyph-stretching line justifier for the DigitalKhatt Madina fonts.

Python port of the "experimental" justification in DigitalKhatt's
`hbmedina/just.service.ts` (MIT, (c) 2024 DigitalKhatt,
https://github.com/DigitalKhatt/digitalkhatt.org). It stretches letters by
setting the fonts' `cv01`/`cv02`/`cv03`/`cv10`-`cv18` feature values on
individual characters, then fills what is left with inter-word spacing.

Output of `justify_line()` is a `JustResult`:
  * features: {char_index_in_line: {"cv01": n, ...}}
  * simple_spacing / aya_spacing: advance (font units) for each space type
  * x_scale: < 1 only when the natural line is too wide (shrink)

All widths are in font units (the fonts use 1000 units per em).
"""
# pylint: disable=too-many-locals,too-many-branches,too-many-statements
# pylint: disable=too-many-arguments,too-many-positional-arguments
# pylint: disable=too-many-instance-attributes,too-many-nested-blocks
# pylint: disable=too-many-boolean-expressions
# (a build pipeline and ports of DigitalKhatt's justifier: long, stateful routines
#  kept in one piece so they read alongside the original)
import re
from dataclasses import dataclass, field

import uharfbuzz as hb

import ink

# ---------------------------------------------------------------- constants
RIGHT_NO_JOIN = "آاٱأإدذرزوؤءة"
DUAL_JOIN = "بتثجحخسشصضطظعغفقكلمنهيئى"
BASES = set(DUAL_JOIN + RIGHT_NO_JOIN)
FINAL_ASCENDANT = "آادذٱأإكلهة"
FATHA, SHADDA = "َ", "ّ"

# Applied results
NO_CHANGE, POSITIVE, OVERFLOW, FORBIDDEN = range(4)

# Stretch types
BEH, FINA_ASCENDANT, OTHER, KAF, SECOND_NOT_SAME, SECOND_SAME = range(1, 7)

_R = "بتثنيئ" + "جحخ" + "سش" + "صض" + "طظ" + "عغ" + "فق" + "م" + "ه"
_L = ("ئبتثني" + "جحخ" + "طظ" + "عغ" + "فق" + "ةلم" + "رز").replace("رز", "")
_BEH = r"^.+([بتثنيسشصض][بتثنيم]).+$"
_FINA = rf"^.*([{_R}][آادذٱأإكلهة])$"
_REH = rf".*([{_R}][رز])"
_OTHER = rf".*([{_R}](?:[ل]|[{_L}]))"
KASHIDA_REGEXPS = {
    BEH: [_BEH],
    FINA_ASCENDANT: [_FINA],
    OTHER: [_REH, _OTHER],
    KAF: [r"^.*([ك].).*$"],
    SECOND_NOT_SAME: [_BEH, _FINA, _REH, _OTHER],
    SECOND_SAME: [_BEH, rf"([{_R}][آادذٱأإكلهة])$", rf"([{_R}][رز])",
                  rf"([{_R}](?:[ل]|[{_L}]))"],
}
KASHIDA_REGEXPS = {k: [re.compile(p) for p in v] for k, v in KASHIDA_REGEXPS.items()}

# applySimpleJust patterns (just.service.ts), used for layouts other than Madina
_RIGHT_KASH = re.sub("[لك]", "", DUAL_JOIN)
_LEFT_CHARS = DUAL_JOIN + RIGHT_NO_JOIN.replace("ء", "")
_LEFT_KASH_MEDI = re.sub("[وهصضطظ]", "", _LEFT_CHARS).replace("ه", "")
_ALT_FIN_PAT = "^.*([بتثفكنصضسشقيئى])$"
_FINAL_KASH_END = rf"^.*([{_RIGHT_KASH}][آاٱأإملهة])$"
_FINAL_KASH = rf"^.*([{_RIGHT_KASH}][دذآاٱأإملهة])$"
_HAH_KASH = rf"^.*([جحخ][{_LEFT_KASH_MEDI}]).*$|^.*([جحخ][هة])$"
_ALT_FINA = re.compile(_ALT_FIN_PAT)
_HAH_FINA_ASCEN = re.compile(_HAH_KASH + "|" + _FINAL_KASH_END)
_SIMPLE = re.compile("|".join([
    _ALT_FIN_PAT, _HAH_KASH, _FINAL_KASH, r"^.+([بتثنيسشصض][بتثنيم]).+$",
    rf".*([{_RIGHT_KASH}][رز])", rf".*([{_RIGHT_KASH}](?:[ل]|[{_LEFT_KASH_MEDI}]))",
    r"^.*([ك].).*$"]))


# ------------------------------------------------------------- text model
@dataclass
class SubWord:
    """Run of joined base letters within a word (breaks after non-joining letters)."""
    base_text: str = ""
    base_indexes: list = field(default_factory=list)


@dataclass
class Word:
    """A word of the line: its span in the line text and its sub-words."""
    start: int
    end: int
    text: str = ""
    base_text: str = ""
    base_indexes: list = field(default_factory=list)
    subwords: list = field(default_factory=lambda: [SubWord()])


@dataclass
class LineInfo:
    """A line split into words and spaces (analyzeLineForJust)."""
    text: str
    words: list
    spaces: dict          # char index -> "aya" | "simple"


@dataclass
class JustResult:
    """Result of justify_line(): letter features, spacing and scale."""
    features: dict
    simple_spacing: float
    aya_spacing: float
    x_scale: float = 1.0
    natural_width: float = 0.0
    final_width: float = 0.0
    # whole-word features by word index (e.g. shrinking), applied to the
    # word's span as-is; `features` holds per-character stretch features
    word_features: dict = field(default_factory=dict)


# Base width of the spaces around an aya number, in normal spaces. The ۝ ornament
# fills its whole advance, so a plain space makes it look glued to its neighbours.
AYA_SPACE = 1.5


def is_aya_space(text, i):
    """Is the space at i next to an aya number (an aya space)?"""
    prev_c = text[i - 1] if i > 0 else ""
    next_c = text[i + 1] if i + 1 < len(text) else ""
    return ("٠" <= prev_c <= "٩") or next_c == "۝"


def analyze_line(text):
    """Split a line into words / sub-words of base letters (analyzeLineForJust)."""
    words, spaces = [Word(0, -1)], {}
    for i, ch in enumerate(text):
        if ch == " ":
            spaces[i] = "aya" if is_aya_space(text, i) else "simple"
            words.append(Word(i + 1, i))
            continue
        word = words[-1]
        word.text += ch
        if ch in BASES:
            rel = i - word.start
            word.base_text += ch
            word.base_indexes.append(rel)
            is_hamza = ch == "ء"
            if is_hamza:
                word.subwords.append(SubWord())
            sub = word.subwords[-1]
            sub.base_text += ch
            sub.base_indexes.append(rel)
            if i < len(text) - 1 and ch in RIGHT_NO_JOIN and not is_hamza:
                word.subwords.append(SubWord())
        word.end += 1
    return LineInfo(text, words, spaces)


# ------------------------------------------------------------- shaping
def shape(font, text, features=None):
    """Shape `text` RTL as the DOM does; clusters are character indexes."""
    buf = hb.Buffer()
    buf.add_codepoints([ord(c) for c in text])  # clusters = char indexes
    buf.direction, buf.script, buf.language = "rtl", "Arab", "ar"
    buf.cluster_level = hb.BufferClusterLevel.MONOTONE_CHARACTERS
    hb.shape(font, buf, features or {})
    return buf


def width(font, text, features=None):
    """Advance of `text` shaped with `features`, font units."""
    return sum(p.x_advance for p in shape(font, text, features).glyph_positions)


def to_hb_features(char_features, offset=0, lo=0, hi=None):
    """{index: {tag: value}} -> uharfbuzz ranged feature dict."""
    out = {}
    for idx, feats in char_features.items():
        if idx < lo or (hi is not None and idx > hi):
            continue
        for tag, value in feats.items():
            # uharfbuzz ranged features are (start, end, value) triples
            out.setdefault(tag, []).append((idx - offset, idx - offset + 1, value))
    return out


# ---------------------------------------------------------- justifier
class _Justifier:
    def __init__(self, font, line, line_width, desired, exhaustive=False):
        self.font, self.line = font, line
        # exhaustive: on overflow keep trying smaller stretches elsewhere
        # instead of stopping (the reference stops at the first overflow)
        self.exhaustive = exhaustive
        self.features = {}
        self.text_width = line_width
        self.desired = desired
        self.word_widths = [width(font, w.text) for w in line.words]
        self.applied = [{} for _ in line.words]

    def word_width(self, wi, feats):
        """Width of word wi with the line-level per-character features `feats`."""
        w = self.line.words[wi]
        return width(self.font, w.text, to_hb_features(feats, w.start, w.start, w.end))

    def try_apply(self, wi, new_feats):
        """Keep `new_feats` if word wi then still fits the line; report the outcome."""
        new_w = self.word_width(wi, new_feats)
        diff = new_w - self.word_widths[wi]
        if new_w != self.word_widths[wi] and self.text_width + diff < self.desired:
            self.text_width += diff
            self.word_widths[wi] = new_w
            self.features = new_feats
            return POSITIVE
        return NO_CHANGE if diff == 0 else OVERFLOW

    @staticmethod
    def _fatha_index(text, i):
        if i + 1 < len(text) and text[i + 1] == FATHA:
            return i + 1
        if i + 2 < len(text) and text[i + 1] == SHADDA and text[i + 2] == FATHA:
            return i + 2
        return None

    # -- kashida between two joined letters (applyKashida)
    def apply_kashida(self, wi, si, first, second):
        """Stretch the connection between two letters of a sub-word (applyKashida)."""
        text, word = self.line.text, self.line.words[wi]
        sub = word.subwords[si]
        first_m, second_m = sub.base_indexes[first], sub.base_indexes[second]
        i1, i2 = word.start + first_m, word.start + second_m
        temp = {k: dict(v) for k, v in self.features.items()}
        if "cv01" in temp.get(i2, {}):
            return FORBIDDEN
        c3, c4 = text[i1], text[i2]
        last_base = sub.base_indexes[-1] == second_m
        first_base = sub.base_indexes[0] == first_m
        if c4 == "ق" and last_base:
            return FORBIDDEN
        if c3 == "ل" and (c4 in "كدذة" or (c4 == "ه" and last_base)):
            return FORBIDDEN
        if c3 in "ئبتثنيى" and not first_base and c4 in "رز":
            return FORBIDDEN

        first_feats = dict(temp.get(i1, {}))
        cv01 = min(first_feats.get("cv01", 0) + 1, 6)
        first_feats["cv01"] = cv01
        second_feats = {}
        if c3 in "بتثنيئ":
            first_feats["cv10"] = 1

        def both(tag):
            first_feats[tag] = 1
            second_feats[tag] = 1

        bt = sub.base_text
        if c3 == "ه" and c4 == "م" and last_base:
            both("cv11")
        elif c3 in "بتثنيئ" and first_base and c4 in "جحخ":
            both("cv12")
        elif c3 == "م" and first_base and c4 in "جحخ":
            both("cv13")
        elif c3 in "فق" and first_base and c4 in "جحخ":
            both("cv14")
        elif c3 == "ل" and first_base and c4 in "جحخ":
            both("cv15")
        elif c3 in "عغ" and first_base and (
                c4 in "آادذٱأإل" or (c4 in "بتثنيئ" and len(bt) > 2 and bt[2] in "سش")):
            both("cv16")
        elif c3 in "جحخ":
            if (c4 in "آادذٱأإل" or (c4 in "هة" and last_base)
                    or (c4 in "بتثنيئ" and len(sub.base_indexes) > 1
                        and sub.base_indexes[-2] == second_m and bt and bt[-1] in "رزن")):
                both("cv16")
            elif first_base and c4 == "م":
                both("cv18")
        elif c3 in "سشصض" and c4 in "رز":
            both("cv17")

        second_feats["cv02"] = cv01 if (c4 in FINAL_ASCENDANT and last_base) else 2 * cv01
        temp[i1], temp[i2] = first_feats, second_feats
        return self.try_apply(wi, temp)

    # -- kaf alternate (applyKaf)
    def apply_kaf(self, wi, si, first, second):
        """Use the wide kaf form, with its following letter (applyKaf)."""
        text, word = self.line.text, self.line.words[wi]
        sub = word.subwords[si]
        i1 = word.start + sub.base_indexes[first]
        i2 = word.start + sub.base_indexes[second]
        temp = {k: dict(v) for k, v in self.features.items()}
        temp.setdefault(i1, {})["cv03"] = 1
        temp.setdefault(i2, {})["cv03"] = 1
        fatha = self._fatha_index(text, i1)
        if fatha is not None:
            temp[fatha] = {"cv01": 1 + temp[i2].get("cv01", 0) // 3}
        return self.try_apply(wi, temp)

    # -- wider final/isolated alternate (applyAlternate)
    def apply_alternate(self, wi, idx):
        """Widen the final/isolated letter at idx one level (applyAlternate)."""
        temp = {k: dict(v) for k, v in self.features.items()}
        prev = temp.get(idx, {})
        if prev.get("cv02", 0) > 0:
            return FORBIDDEN
        new = dict(prev)
        new["cv01"] = min(new.get("cv01", 0) + 1, 12)
        temp[idx] = new
        fatha = self._fatha_index(self.line.text, idx)
        if fatha is not None:
            temp[fatha] = {"cv01": 1 + new["cv01"] // 3}
        return self.try_apply(wi, temp)

    @staticmethod
    def _match_subwords(word, regexps):
        subword_indexes, matches = [], []
        for si, sub in enumerate(word.subwords):
            found = [m for rx in regexps for m in rx.finditer(sub.base_text)]
            matches.append(found)
            if found:
                subword_indexes.append(si)
        return subword_indexes, matches

    def kashidas(self, stype, levels):
        """Apply kashidas of one stretch type, level by level; True on overflow."""
        words = self.line.words
        found = [self._match_subwords(w, KASHIDA_REGEXPS[stype]) for w in words]
        for _ in range(levels):
            for wi in range(len(words)):
                sub_idx, matches = found[wi]
                applied = self.applied[wi]
                t1, t2, t3 = applied.get(BEH), applied.get(FINA_ASCENDANT), applied.get(OTHER)
                t5 = applied.get(SECOND_NOT_SAME)
                if stype == BEH and (t2 or t3):
                    continue
                if stype == FINA_ASCENDANT and (t1 or t3):
                    continue
                if stype == OTHER and (t1 or t2):
                    continue
                done = False
                for si in reversed(sub_idx):
                    if done:
                        break
                    for m in matches[si]:
                        first = m.start(1)
                        t123 = t1 or t2 or t3
                        if stype == SECOND_NOT_SAME and t123 and t123[0] == si:
                            continue
                        if stype == SECOND_SAME and (
                                (t123 and t123 == (si, first)) or (t5 and t5 == (si, first))):
                            continue
                        apply = self.apply_kaf if stype == KAF else self.apply_kashida
                        result = apply(wi, si, first, first + 1)
                        if result == POSITIVE:
                            applied[stype] = (si, first)
                        elif result == OVERFLOW and not self.exhaustive:
                            return True
                        elif result in (FORBIDDEN, OVERFLOW):
                            continue
                        done = True
                        break
        return False

    def alternates(self, chars, levels):
        """Widen final `chars`, level by level; True on overflow."""
        rx = re.compile(rf"^.*([{chars}])$")
        words = self.line.words
        found = [self._match_subwords(w, [rx]) for w in words]
        for _ in range(levels):
            for wi, word in enumerate(words):
                sub_idx, matches = found[wi]
                for si in reversed(sub_idx):
                    m = matches[si][0]
                    idx = word.start + word.subwords[si].base_indexes[m.start(1)]
                    result = self.apply_alternate(wi, idx)
                    if result == OVERFLOW and not self.exhaustive:
                        return True
                    if result in (FORBIDDEN, OVERFLOW):
                        continue
                    break
        return False

    def run_simple(self, first_word_included=True, word_by_word=False, nb_alt=2, nb_kashida=2):
        """applySimpleJust (DigitalKhatt, layouts other than Madina, e.g. IndoPak):
        each word gets one candidate - a final alternate, a hah/final-ascendant
        kashida, or the first simple pattern found from its last sub-word back -
        applied level by level from the line's last word to its first."""
        words = self.line.words
        first = 0 if first_word_included else 1
        found = []
        for wi, word in enumerate(words):
            res = None
            if word.base_text and wi >= first:
                last = len(word.subwords) - 1
                sub = word.subwords[last]
                m = _ALT_FINA.match(sub.base_text)
                if m:
                    res = (last, m, 1)
                elif word.base_text[-1] not in "يئى":
                    m = _HAH_FINA_ASCEN.match(sub.base_text)
                    if m:
                        res = (last, m, 2)
                    else:
                        for si in range(last, -1, -1):
                            m = _SIMPLE.match(word.subwords[si].base_text)
                            if m:
                                res = (si, m, 3)
                                break
            found.append(res)
        stretched = set()
        for level in range(1, max(nb_alt, nb_kashida) + 1):
            for wi in range(len(words) - 1, first - 1, -1):
                if wi + 1 in stretched:
                    continue
                if not found[wi]:
                    continue
                si, m, kind = found[wi]
                group = max(g for g in range(1, len(m.groups()) + 1) if m.group(g) is not None)
                start = m.start(group)
                result = None
                if kind == 1 or (kind == 3 and group == 1):
                    if level <= nb_alt:
                        idx = words[wi].start + words[wi].subwords[si].base_indexes[start]
                        result = self.apply_alternate(wi, idx)
                elif level <= nb_kashida:
                    if group == 8 and kind == 3:
                        result = self.apply_kaf(wi, si, start, start + 1)
                    else:
                        result = self.apply_kashida(wi, si, start, start + 1)
                if result == OVERFLOW:
                    return
                if result == POSITIVE and word_by_word:
                    stretched.add(wi)

    def run(self):
        """Priority order of applyExperimentalJust (Madina layouts)."""
        steps = [
            (self.kashidas, BEH, 2), (self.alternates, "بتثكن", 2),
            (self.kashidas, FINA_ASCENDANT, 3), (self.kashidas, OTHER, 2),
            (self.alternates, "ىصضسشفقيئ", 2), (self.kashidas, KAF, 1),
            (self.kashidas, BEH, 1), (self.alternates, "بتثكن", 1),
            (self.kashidas, FINA_ASCENDANT, 1), (self.kashidas, OTHER, 1),
            (self.alternates, "ىصضسشفقيئ", 1), (self.alternates, "بتثكن", 2),
            (self.alternates, "ىصضسشفقيئبتثكن", 2), (self.kashidas, BEH, 1),
            (self.kashidas, FINA_ASCENDANT, 1), (self.kashidas, OTHER, 1),
            (self.alternates, "ىصضسشفقيئبتثكن", 2),
            (self.kashidas, SECOND_NOT_SAME, 2), (self.kashidas, SECOND_SAME, 2),
        ]
        for fn, arg, levels in steps:
            if fn(arg, levels):
                break


def natural_width(font, text):
    """Width of a line with plain spaces (aya spaces at their base width), words
    shaped one by one as in the DOM."""
    line = analyze_line(text)
    space_w = width(font, " ")
    n_aya = sum(1 for t in line.spaces.values() if t == "aya")
    return (sum(width(font, w.text) for w in line.words)
            + space_w * (len(line.spaces) - n_aya) + space_w * AYA_SPACE * n_aya)


def justify_line(font, text, desired_width, stretch_letters=True, space_stretch=1.0,
                 exhaustive=False):
    """Justify one line to `desired_width` font units (justifyLine, XScale style).

    space_stretch: how much spaces may grow (x normal width) before letters
    are stretched; the reference uses 1.0, its DOM renderer 0.5.
    exhaustive: see _Justifier."""
    line = analyze_line(text)
    space_w = width(font, " ")
    # measured word by word, as the DOM shapes one span per word
    n_aya_spaces = sum(1 for t in line.spaces.values() if t == "aya")
    natural = (sum(width(font, w.text) for w in line.words)
               + space_w * (len(line.spaces) - n_aya_spaces) + space_w * AYA_SPACE * n_aya_spaces)
    n_simple = sum(1 for t in line.spaces.values() if t == "simple")
    n_aya = len(line.spaces) - n_simple
    simple, aya = space_w, space_w * AYA_SPACE
    features = {}
    current = natural
    if desired_width > natural:
        max_simple = min(100, space_w) * space_stretch
        max_aya = min(200, 2 * space_w) * space_stretch
        max_stretch = max_simple * n_simple + max_aya * n_aya
        stretch = min(desired_width - natural, max_stretch)
        ratio = stretch / max_stretch if max_stretch else 0
        simple += ratio * max_simple
        aya += ratio * max_aya
        current += stretch
        if stretch_letters and desired_width > current:
            j = _Justifier(font, line, current, desired_width, exhaustive)
            j.run()
            features, current = j.features, j.text_width
        if desired_width > current and line.spaces:
            extra = (desired_width - current) / len(line.spaces)
            simple += extra
            aya += extra
            current = desired_width
        return JustResult(features, simple, aya, 1.0, natural, current)
    return _shrink(font, line, natural, desired_width, space_w)


WORD_LEVEL_FEATURES = {"jt": 5, "dc": 3, "kt": 5}   # Old Madina: whole-word stretch


def justify_words(font, text, desired_width, space_stretch=0.5):
    """Word-granular justification for DOM rendering (Old Madina font only).

    Port of DigitalKhatt's oldmedina `justifyElem`/`applyExpa`: the font's
    jtNN / dcNN / ktNN features are switched on for a *whole word*, and the
    font itself decides which letters stretch. Because each feature covers a
    whole word, a browser can apply it with one `font-feature-settings` per
    word span without breaking letter joining.

    Returns a JustResult whose `features` are keyed by *word index*."""
    line = analyze_line(text)
    space_w = width(font, " ")
    word_w = [width(font, w.text) for w in line.words]
    # words are shaped separately in the DOM (one span each), so measure the
    # same way; whole-line shaping can differ slightly across spaces
    n_aya_spaces = sum(1 for t in line.spaces.values() if t == "aya")
    natural = (sum(word_w) + space_w * (len(line.spaces) - n_aya_spaces)
               + space_w * AYA_SPACE * n_aya_spaces)
    if desired_width <= natural:
        res = _shrink(font, line, natural, desired_width, space_w)
        res.features, res.word_features = res.word_features, {}
        return res
    n_simple = sum(1 for t in line.spaces.values() if t == "simple")
    n_aya = len(line.spaces) - n_simple
    max_simple, max_aya = space_w * space_stretch, space_w * 2
    max_stretch = max_simple * n_simple + max_aya * n_aya
    stretch = min(desired_width - natural, max_stretch)
    ratio = stretch / max_stretch if max_stretch else 0
    simple, aya = space_w + ratio * max_simple, space_w * AYA_SPACE + ratio * max_aya
    current = natural + stretch
    word_feats = [{} for _ in line.words]
    done = False
    for level in range(1, 6):
        for prefix, top in WORD_LEVEL_FEATURES.items():
            if done or level > top:
                continue
            for wi, word in enumerate(line.words):
                trial = dict(word_feats[wi], **{f"{prefix}{level:02d}": 1})
                new_w = width(font, word.text, trial)
                if current + new_w - word_w[wi] > desired_width:
                    done = True
                    break
                current += new_w - word_w[wi]
                word_w[wi], word_feats[wi] = new_w, trial
    if desired_width > current and line.spaces:
        extra = (desired_width - current) / len(line.spaces)
        simple, aya = simple + extra, aya + extra
        current = desired_width
    features = {wi: f for wi, f in enumerate(word_feats) if f}
    return JustResult(features, simple, aya, 1.0, natural, current)


def word_to_char_features(text, word_features):
    """Expand {word_index: feats} to {char_index: feats} (for HarfBuzz)."""
    words = analyze_line(text).words
    return {i: feats for wi, feats in word_features.items()
            for i in range(words[wi].start, words[wi].end + 1)}


# The fonts' tightening features: shr1 (narrower alternates, rarely applies) and
# shrr (GPOS: tucks letters into their neighbours, ~4.5% per line). shrr is never
# applied next to an aya number, whose ornament fills its advance edge to edge.
SHRINK_FEATURES = ("shr1", "shrr")
MIN_SPACE_RATIO = 0.6                # spaces may tighten to 60% of normal


def _shrink(font, line, natural, desired, space_w):
    """Not in the reference algorithm (it only x-scales): tighten the spaces
    between words, then apply the fonts' shrink features word by word (last
    word first), and only then fall back to a horizontal scale for what is left.
    Spaces around aya numbers keep their normal width (the marker would touch
    the next word, as in print they never tighten)."""
    n_simple = sum(1 for t in line.spaces.values() if t == "simple")
    simple = space_w
    current = natural
    if n_simple:
        simple = max(space_w * MIN_SPACE_RATIO, space_w - (natural - desired) / n_simple)
        current -= (space_w - simple) * n_simple
    word_features = {}
    shrink = {tag: 1 for tag in SHRINK_FEATURES}
    def near_marker(wi):
        return any(0 <= k < len(line.words) and line.words[k].text.startswith("\u06DD")
                   for k in (wi - 1, wi, wi + 1))

    for wi in range(len(line.words) - 1, -1, -1):
        if current <= desired:
            break
        word = line.words[wi]
        if near_marker(wi):
            continue
        before = width(font, word.text)
        after = width(font, word.text, shrink)
        if after >= before:
            continue
        word_features[wi] = dict(shrink)
        current -= before - after
    aya = space_w * AYA_SPACE
    if current < desired and line.spaces:       # overshot: give it back to the spaces
        if n_simple:
            simple += (desired - current) / n_simple
        else:
            aya += (desired - current) / len(line.spaces)
        current = desired
    x_scale = min(1.0, desired / current)
    return JustResult({}, simple, aya, x_scale, natural, current * x_scale, word_features)


def line_glyphs(font, text, result):
    """Shape a justified line; return [(glyph_id, x, y)] left-to-right in font
    units plus total width. Spaces take the justified advances."""
    line = analyze_line(text)
    spaces = line.spaces
    feats = {k: dict(v) for k, v in result.features.items()}
    for wi, wf in result.word_features.items():
        for idx in range(line.words[wi].start, line.words[wi].end + 1):
            feats.setdefault(idx, {}).update(wf)
    buf = shape(font, text, to_hb_features(feats))
    out, x = [], 0.0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        kind = spaces.get(info.cluster)
        adv = (result.aya_spacing if kind == "aya" else result.simple_spacing) if kind \
            else pos.x_advance
        out.append((info.codepoint, x + pos.x_offset, pos.y_offset))
        x += adv
    return out, x


# ------------------------------------------------- print model (1441H)
# Measured on the KFGQPC 1441H print (QCF4 glyphs, every 3rd page): closest ink
# of neighbouring words, band by band (ink.py), as a share of the line width:
#   word | word:   p1 0.0042  p5 0.0058  p25 0.0087  median 0.0109  p95 0.0181
#   word | ۝N:     p5 0.0095  median 0.0102 (most lines exactly)  p95 0.0201
#   ۝N | word:     p5 0.0078  median 0.0086  p95 0.0097
# The print never lets two words touch. Lines are filled by changing the
# *words* — stretched on loose lines, written narrower on dense ones (by up to
# ~25%) — while the gaps stay in that band and aya numbers keep their size.
# gap kinds: word|word, word|۝N (before an aya number), ۝N|word (after it)
PRINT_GAPS = {"w": 0.0109, "b": 0.0102, "a": 0.0086}
# how far each kind may tighten / open (print p5..p95 over the median)
GAP_RANGES = {"w": (0.55, 1.65), "b": (0.93, 1.9), "a": (0.91, 1.13)}
SPACE_FIRST = 1.2                # word gaps open this far before letters are stretched
MIN_WORD_SCALE = 0.8             # narrowest words; past that the whole line is scaled


@dataclass
class FitResult:
    """Result of fit_line_print(): features, spaces and scales of one line."""
    features: dict                # {char index: {cvNN: v}} letter stretching
    spaces: list                  # advance of each space (font units), reading order
    word_scale: float = 1.0       # horizontal scale of the words (aya numbers excluded)
    x_scale: float = 1.0          # whole-line scale, last resort
    natural_width: float = 0.0
    final_width: float = 0.0
    advances: list = field(default_factory=list)   # each word's advance (unscaled)
    markers: list = field(default_factory=list)    # word is an aya number

    def dom_spaces(self):
        """Spaces for a DOM that narrows words with a CSS transform, which keeps
        each word's box: a word gives back what it lost on its inner sides — half
        on each side for words scaled about their centre, all of it on the inner
        side for the line's first and last words (scaled from the line's edges)."""
        n = len(self.advances)
        def inner(i, side):           # side: "right" (towards word i-1) or "left"
            if self.markers[i] or self.word_scale >= 1:
                return 0.0
            lost = (1 - self.word_scale) * self.advances[i]
            if i == 0:
                return lost if side == "left" else 0.0
            if i == n - 1:
                return lost if side == "right" else 0.0
            return lost / 2
        return [sp - inner(k, "left") - inner(k + 1, "right") for k, sp in enumerate(self.spaces)]


def word_profile(font, text, features=None):
    """Ink profile (ink.Profile) of one word as the DOM shapes it."""
    return ink.shaped_profile(font, shape(font, text, features))


MIN_SPACE = -250      # a space may be negative (boxes overlap, ink never does)


def is_marker_word(text):
    """Is this token an aya number?"""
    return "۝" in text


def fit_line_print(font, text, desired, line_width, exhaustive=True, simple=False):
    """Fit one line to `desired` font units the way the print does.

    line_width: a full line in the same units (gaps are a share of it).
    simple: stretch letters with DigitalKhatt's applySimpleJust (non-Madina layouts)."""
    line = analyze_line(text)
    words = line.words
    marker = [is_marker_word(w.text) for w in words]
    n = len(words)
    kinds = ["b" if marker[k + 1] else "a" if marker[k] else "w" for k in range(n - 1)]
    lo_w, hi_w = GAP_RANGES["w"]

    def gaps_at(f):
        """Gap targets when word gaps are f times the print's median; the
        other kinds move proportionally within their own (narrower) range."""
        out = []
        for kind in kinds:
            lo, hi = GAP_RANGES[kind]
            if f < 1:
                g = 1 - (1 - f) * (1 - lo) / (1 - lo_w)
            else:
                g = 1 + (f - 1) * (hi - 1) / (hi_w - 1)
            out.append(PRINT_GAPS[kind] * g * line_width)
        return out

    def boxes(feats):
        return [word_profile(font, w.text, to_hb_features(feats, w.start, w.start, w.end))
                for w in words]

    def spaces_for(bx, gaps, c=1.0):
        # word k sits right of word k+1 (RTL); the space makes their closest
        # ink (band by band) exactly g apart
        out = []
        for k, g in enumerate(gaps):
            ck = 1.0 if marker[k] else c
            cn = 1.0 if marker[k + 1] else c
            out.append(max(MIN_SPACE, g - ink.clearance_offset(bx[k], bx[k + 1], ck, cn)))
        return out

    def total(bx, sp, c=1.0):
        return sum(b.advance * (1.0 if m else c) for b, m in zip(bx, marker)) + sum(sp)

    def width_at(bx, f, c=1.0):
        return total(bx, spaces_for(bx, gaps_at(f), c), c)

    def result(features, bx, f, c, natural):
        sp = spaces_for(bx, gaps_at(f), c)
        current = total(bx, sp, c)
        x = 1.0
        if current > desired * 1.0005:
            x = desired / current
        elif current != desired and sp:
            # what is left (either way) goes to the word gaps
            weights = [1.0 if k == "w" else 0.25 for k in kinds]
            extra = (desired - current) / sum(weights)
            sp = [v + extra * wgt for v, wgt in zip(sp, weights)]
            current = desired
        return FitResult(features, sp, round(c, 4), x, natural, current * x,
                         [b.advance for b in bx], marker)

    bx = boxes({})
    natural = width_at(bx, 1.0)
    if natural <= desired:
        # loose line: 1. gaps open a little, 2. letters stretch (kashida /
        # alternates, as DigitalKhatt's justifier), 3. gaps take the rest
        f = _solve(lambda v: width_at(bx, v), 1.0, SPACE_FIRST, desired)
        current = width_at(bx, f)
        features = {}
        if current < desired:
            j = _Justifier(font, line, current, desired, exhaustive)
            if simple:
                j.run_simple()
            else:
                j.run()
            features = j.features
            bx = boxes(features)
            if width_at(bx, f) > desired:     # stretched ink moved a little
                f = _solve(lambda v: width_at(bx, v), f, lo_w, desired)
        return result(features, bx, f, 1.0, natural)
    # dense line: 1. gaps tighten (word gaps most, aya gaps hardly),
    # 2. words get narrower (aya numbers keep their size), 3. the line, rarely
    f = _solve(lambda v: width_at(bx, v), 1.0, lo_w, desired)
    c = 1.0
    if width_at(bx, f) > desired:
        c = _solve(lambda v: width_at(bx, f, v), 1.0, MIN_WORD_SCALE, desired)
    return result({}, bx, f, c, natural)


def _solve(fn, a, b, target, iters=30):
    """Parameter between a and b where monotonic fn hits target (clamped to b)."""
    fa, fb = fn(a), fn(b)
    if (fb - target) * (fa - target) > 0:       # target not reachable: stop at b
        return b if abs(fb - target) < abs(fa - target) else a
    for _ in range(iters):
        m = (a + b) / 2
        if (fn(m) - target) * (fa - target) > 0:
            a, fa = m, fn(m)
        else:
            b = m
    return (a + b) / 2
