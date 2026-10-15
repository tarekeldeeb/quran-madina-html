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
import re
from dataclasses import dataclass, field

import uharfbuzz as hb

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


# ------------------------------------------------------------- text model
@dataclass
class SubWord:
    base_text: str = ""
    base_indexes: list = field(default_factory=list)


@dataclass
class Word:
    start: int
    end: int
    text: str = ""
    base_text: str = ""
    base_indexes: list = field(default_factory=list)
    subwords: list = field(default_factory=lambda: [SubWord()])


@dataclass
class LineInfo:
    text: str
    words: list
    spaces: dict          # char index -> "aya" | "simple"


@dataclass
class JustResult:
    features: dict
    simple_spacing: float
    aya_spacing: float
    x_scale: float = 1.0
    natural_width: float = 0.0
    final_width: float = 0.0


def is_aya_space(text, i):
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
    buf = hb.Buffer()
    buf.add_codepoints([ord(c) for c in text])  # clusters = char indexes
    buf.direction, buf.script, buf.language = "rtl", "Arab", "ar"
    buf.cluster_level = hb.BufferClusterLevel.MONOTONE_CHARACTERS
    hb.shape(font, buf, features or {})
    return buf


def width(font, text, features=None):
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
        w = self.line.words[wi]
        return width(self.font, w.text, to_hb_features(feats, w.start, w.start, w.end))

    def try_apply(self, wi, new_feats):
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


def justify_line(font, text, desired_width, stretch_letters=True, space_stretch=1.0,
                 exhaustive=False):
    """Justify one line to `desired_width` font units (justifyLine, XScale style).

    space_stretch: how much spaces may grow (x normal width) before letters
    are stretched; the reference uses 1.0, its DOM renderer 0.5.
    exhaustive: see _Justifier."""
    line = analyze_line(text)
    space_w = width(font, " ")
    natural = width(font, text)
    n_simple = sum(1 for t in line.spaces.values() if t == "simple")
    n_aya = len(line.spaces) - n_simple
    simple = aya = space_w
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
    natural = sum(word_w) + space_w * len(line.spaces)
    if desired_width <= natural:
        res = _shrink(font, line, natural, desired_width, space_w)
        res.features = {wi: res.features[w.start] for wi, w in enumerate(line.words)
                        if w.start in res.features}
        return res
    n_simple = sum(1 for t in line.spaces.values() if t == "simple")
    n_aya = len(line.spaces) - n_simple
    max_simple, max_aya = space_w * space_stretch, space_w * 2
    max_stretch = max_simple * n_simple + max_aya * n_aya
    stretch = min(desired_width - natural, max_stretch)
    ratio = stretch / max_stretch if max_stretch else 0
    simple, aya = space_w + ratio * max_simple, space_w + ratio * max_aya
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


SHRINK_FEATURES = ("shr1", "shrr")   # the fonts' own tightening features
MIN_SPACE_RATIO = 0.6                # spaces may tighten to 60% of normal


def _shrink(font, line, natural, desired, space_w):
    """Not in the reference algorithm (it only x-scales): tighten spaces, then
    apply the fonts' shrink features word by word (last word first), and only
    then fall back to a horizontal scale for what is left."""
    n_spaces = len(line.spaces)
    space = space_w
    current = natural
    if n_spaces:
        space = max(space_w * MIN_SPACE_RATIO, space_w - (natural - desired) / n_spaces)
        current -= (space_w - space) * n_spaces
    features = {}
    for word in reversed(line.words):
        if current <= desired:
            break
        before = width(font, word.text)
        after = width(font, word.text, {tag: 1 for tag in SHRINK_FEATURES})
        if after >= before:
            continue
        for idx in range(word.start, word.end + 1):
            features.setdefault(idx, {}).update({tag: 1 for tag in SHRINK_FEATURES})
        current -= before - after
    if current < desired and n_spaces:        # overshot: give it back to spaces
        space += (desired - current) / n_spaces
        current = desired
    x_scale = min(1.0, desired / current)
    return JustResult(features, space, space, x_scale, natural, current * x_scale)


def line_glyphs(font, text, result):
    """Shape a justified line; return [(glyph_id, x, y)] left-to-right in font
    units plus total width. Spaces take the justified advances."""
    spaces = analyze_line(text).spaces
    buf = shape(font, text, to_hb_features(result.features))
    out, x = [], 0.0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        kind = spaces.get(info.cluster)
        adv = (result.aya_spacing if kind == "aya" else result.simple_spacing) if kind \
            else pos.x_advance
        out.append((info.codepoint, x + pos.x_offset, pos.y_offset))
        x += adv
    return out, x
