"""Place Tanzil's words on the page lines of a DigitalKhatt layout.

The DigitalKhatt texts give, for each of the 604 pages, the 15 lines of the
print. Only their line breaks are used: every converted Tanzil token is
matched to a token of the layout text (they agree on all letters — see
validate_encoding.py), and inherits its page and line.

Line kinds (as in DigitalKhatt's QuranTextService):
  * "sura"  — a sura title line ("سُورَةُ ...")
  * "bism"  — a standalone basmala line
  * "text"  — Quran text, justified (or centered if the layout says so)
"""
import difflib
import re
from dataclasses import dataclass, field

SURA_PREFIX = "سُورَةُ"
# shadda before fatha, as in the DigitalKhatt texts
_BISMI = "\u0628\u0650\u0633\u0652\u0645\u0650"
_REST = (" \u0671\u0644\u0644\u0651\u064E\u0647\u0650"
         " \u0671\u0644\u0631\u0651\u064E\u062D\u0652\u0645\u064E\u0670\u0646\u0650"
         " \u0671\u0644\u0631\u0651\u064E\u062D\u0650\u064A\u0645\u0650")
BASMALA_TEXTS = (
    _BISMI + _REST,
    "\u0628\u0651\u0650\u0633\u0652\u0645\u0650" + _REST,   # after a sura ending in ba
)


@dataclass
class LayoutLine:
    page: int                 # 1-based
    line: int                 # 1-based
    kind: str                 # "sura" | "bism" | "text"
    text: str                 # the layout's own text for the line
    tokens: list = field(default_factory=list)   # indexes into the Tanzil token list
    width: float = None       # print's width ratio for a narrower (centered) line


def load_dk_pages(path):
    """[[line text, ...] per page] from a DigitalKhatt quran_text_*.ts file."""
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    pages = re.findall(r"\[\s*((?:'[^']*',?\s*)+)\]", src)
    return [re.findall(r"'([^']*)'", p) for p in pages]


def line_kind(text, page_index, line_index):
    if text.startswith(SURA_PREFIX):
        return "sura"
    if text in BASMALA_TEXTS and not (page_index == 0 and line_index == 1):
        return "bism"           # Al-Fatiha's basmala is aya 1: a text line
    return "text"


def place_tokens(tokens, pages):
    """Assign each Tanzil token (already converted to the layout's encoding) to a
    layout line. Returns (lines, unmatched) where `unmatched` lists Tanzil token
    indexes that had no counterpart in the layout text (placed with their
    neighbours) — expected to be empty or a handful of known differences."""
    lines, ref, owner = [], [], []
    for pi, page in enumerate(pages):
        for li, text in enumerate(page):
            line = LayoutLine(pi + 1, li + 1, line_kind(text, pi, li), text)
            lines.append(line)
            if line.kind == "sura":
                continue
            for tok in text.split():
                ref.append(tok)
                owner.append(len(lines) - 1)
    where = [None] * len(tokens)
    sm = difflib.SequenceMatcher(None, tokens, ref, autojunk=False)
    for op, a1, a2, b1, b2 in sm.get_opcodes():
        if op in ("equal", "replace") and a2 - a1 == b2 - b1:
            for k in range(a2 - a1):
                where[a1 + k] = owner[b1 + k]
        elif op == "replace" or op == "delete":
            target = owner[b1] if b1 < len(owner) else owner[-1]
            if op == "replace":
                target = owner[b1]
            for k in range(a1, a2):
                where[k] = target if op == "replace" else None
    unmatched = [i for i, w in enumerate(where) if w is None]
    # tokens without a counterpart go with the previous token's line
    last = 0
    for i, w in enumerate(where):
        if w is None:
            where[i] = last
        last = where[i]
    for i, w in enumerate(where):
        lines[w].tokens.append(i)
    return lines, unmatched


def token_keys(meta):
    """'sura:aya:i' for every token: i counts the aya's words from 1, its
    number marker last; basmala tokens of aya 1 get None (they sit on the
    basmala line)."""
    keys, count = [], {}
    for sura, aya, kind in meta:
        if kind == "bism":
            keys.append(None)
            continue
        n = count.get((sura, aya), 0) + 1
        count[(sura, aya)] = n
        keys.append(f"{sura}:{aya}:{n}")
    return keys


def place_tokens_print(tokens, meta, pages, print_pages):
    """Like place_tokens(), but every line takes its words from the print's own
    line breaks (`print_pages`, see extract_print_lines.py) instead of the
    DigitalKhatt text. Sura titles and basmala texts still come from `pages`
    (in order). Returns (lines, problems)."""
    titles = [t for p in pages for t in p if t.startswith(SURA_PREFIX)]
    keys = token_keys(meta)
    index = {k: i for i, k in enumerate(keys) if k}
    bism_tokens = [i for i, k in enumerate(keys) if k is None]
    lines, problems = [], []
    title_it = iter(titles)
    bism_pos = 0
    for pi, page in enumerate(print_pages):
        for li, pl in enumerate(page):
            if pl["k"] == "sura":
                lines.append(LayoutLine(pi + 1, li + 1, "sura", next(title_it)))
                continue
            line = LayoutLine(pi + 1, li + 1, pl["k"], "")
            if pl["k"] == "bism":
                line.text = BASMALA_TEXTS[0]
                lines.append(line)
                continue
            a, b = index.get(pl["a"]), index.get(pl["b"])
            if a is None or b is None or b < a:
                problems.append((pi + 1, li + 1, pl["a"], pl["b"]))
                lines.append(line)
                continue
            line.tokens = list(range(a, b + 1))
            line.width = pl.get("w")
            lines.append(line)
    placed = sorted(i for ln in lines for i in ln.tokens)
    missing = set(range(len(tokens))) - set(placed) - set(bism_tokens)
    if missing:
        problems.append(("unplaced tokens", sorted(missing)[:10], len(missing)))
    if len(placed) != len(set(placed)):
        problems.append(("tokens on two lines",))
    return lines, problems


INDOPAK_BASMALA = ("بِسْمِ اللّٰهِ "
                   "الرَّحْمٰنِ "
                   "الرَّحِيْمِ ۝")
AYA_END = "۝"


def layout_tokens(pages):
    """For a layout whose text is used as is (IndoPak: its spelling differs from
    Tanzil's Uthmani text): tokens, (sura, aya, kind) per token and the lines.

    Aya numbers follow the Kufan count used everywhere else, so sura/aya mean the
    same verse in every layout. They agree with the IndoPak print's own numbers
    except in Al-Fatiha, where the print leaves the basmala unnumbered (it is
    aya 1 here) and marks the non-Kufan end after عَلَيْهِمْ with a sign inside
    aya 7."""
    tokens, meta, lines = [], [], []
    sura, aya = 0, 1
    for pi, page in enumerate(pages):
        for li, text in enumerate(page):
            if text.startswith(SURA_PREFIX):
                sura, aya = sura + 1, 1
                lines.append(LayoutLine(pi + 1, li + 1, "sura", text))
                continue
            is_bism = text.strip() == INDOPAK_BASMALA and sura != 1
            line = LayoutLine(pi + 1, li + 1, "bism" if is_bism else "text", text)
            for tok in text.split():
                line.tokens.append(len(tokens))
                tokens.append(tok)
                if is_bism:
                    meta.append((sura, 1, "bism"))
                    continue
                meta.append((sura, aya, "marker" if AYA_END in tok else "word"))
                if AYA_END in tok:
                    aya += 1
            lines.append(line)
    return tokens, meta, lines
