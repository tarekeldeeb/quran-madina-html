"""Convert Tanzil Uthmani text to the encoding the DigitalKhatt fonts expect.

Tanzil stays the source of truth for the words. The DigitalKhatt fonts were
built around their own text, which writes some things differently; this
module rewrites Tanzil words so the fonts produce the intended glyphs.

Rules (derived from a full-text comparison, see docs/v2/design-decisions.md):
  * hamza on a seat is decomposed: أ → ا͏ٔ͏ (alef, CGJ, hamza above, CGJ), likewise
    ؤ ئ; إ → إ͏ (alef, hamza below, CGJ)
  * alef + maddah gets a CGJ: آ / آ → ا͏ٓ
  * tatweel carrying a hamza and a vowel gets a CGJ between them: ـٔ͏َ
  * no tatweel before a dagger alef: ـٰ → ٰ
  * alef maqsura carrying a vowel, or read as yaa after kasra, is written ي
  * tanween: before the small meem of iqlab it becomes a plain vowel; before
    a letter of idgham or ikhfa (next word) it becomes the open (staggered)
    tanween ࣰ ࣱ ࣲ; before throat letters (izhar) and hamzat wasl ٱ it stays
    stacked
  * aya numbers are written ۝ + Arabic-Indic digits
  * rub el hizb ۞ is attached to the following word, sajda ۩ to the previous
    one; neither counts as the "next word" for tanween
"""
import re

CGJ = "͏"
TATWEEL = "ـ"
DAGGER_ALEF = "ٰ"
HAMZA_ABOVE, HAMZA_BELOW = "ٔ", "ٕ"
MADDAH = "ٓ"
FATHATAN, DAMMATAN, KASRATAN = "ً", "ٌ", "ٍ"
FATHA, DAMMA, KASRA, SHADDA, SUKUN = "َ", "ُ", "ِ", "ّ", "ْ"
OPEN_TANWEEN = {FATHATAN: "ࣰ", DAMMATAN: "ࣱ", KASRATAN: "ࣲ"}
PLAIN_VOWEL = {FATHATAN: FATHA, DAMMATAN: DAMMA, KASRATAN: KASRA}
SMALL_MEEM = "ۢ"            # iqlab
SMALL_LOW_MEEM = "ۭ"
AYA_MARK = "۝"
RUB_EL_HIZB = "۞"
SAJDA = "\u06E9"
VOWELS = FATHA + DAMMA + KASRA + FATHATAN + DAMMATAN + KASRATAN

# letters after which tanween is pronounced clearly (izhar): stays stacked
IZHAR = set("ءأإؤئآاهعحغخٱ")
ARABIC_LETTERS = set("ءآأؤإئابةتثجحخدذرزسشصضطظعغفقكلمنهوىيٱ")

SPECIAL_WORDS = {
    # muqatta'at written with maddah in the print, without it in Tanzil
    "يس": "يسٓ", "ص": "صٓ", "ق": "قٓ",
}
SINGLE_CHAR_MAP = {"\u06EA": "\u065C", "\u06EB": "\u06EC"}  # imala, ishmam marks
# one-off spellings in the print, matched after conversion
POST_CONVERSION = {
    # 17:7 — small waw written as the font's small high waw
    "\u0644\u0650\u064A\u064E\u0633\u064F\u06E5\u0653\u0640\u0654\u034F\u064F\u0648\u0627\u06DF":
    "\u0644\u0650\u064A\u064E\u0633\u064F\u034F\u08F3\u0653\u0640\u0654\u034F\u064F\u0648\u0627\u06DF",
}


def _decompose_hamza(word):
    word = re.sub(f"أ(?=[{VOWELS}{SHADDA}{SUKUN}]?)", "ا" + CGJ + HAMZA_ABOVE + CGJ, word)
    word = word.replace("ؤ", "و" + CGJ + HAMZA_ABOVE + CGJ)
    word = word.replace("ئ", "ي" + CGJ + HAMZA_ABOVE + CGJ)
    word = word.replace("إ", "ا" + HAMZA_BELOW + CGJ)
    return word


def first_letter(word):
    for ch in word:
        if ch in ARABIC_LETTERS:
            return ch
    return ""


def convert_word(word, next_word=""):
    """Convert one Tanzil token. `next_word` is the following token (across
    aya ends), needed for the tanween rules."""
    if word in SPECIAL_WORDS:
        word = SPECIAL_WORDS[word]
    for a, b in SINGLE_CHAR_MAP.items():
        word = word.replace(a, b)
    word = word.replace(TATWEEL + DAGGER_ALEF, DAGGER_ALEF)
    # tatweel + hamza above + vowel/sukun  ->  CGJ between hamza and vowel
    word = re.sub(f"{TATWEEL}{HAMZA_ABOVE}([{VOWELS}{SUKUN}])",
                  TATWEEL + HAMZA_ABOVE + CGJ + r"\1", word)
    # sukun followed by the small sakta letter: CGJ between them
    word = word.replace(SUKUN + "\u06DC", SUKUN + CGJ + "\u06DC")
    # dagger alef carrying a hamza: CGJ before the hamza
    word = word.replace(DAGGER_ALEF + HAMZA_ABOVE, DAGGER_ALEF + CGJ + HAMZA_ABOVE)
    word = word.replace("آ", "ا" + CGJ + MADDAH)
    word = re.sub(f"ا{MADDAH}", "ا" + CGJ + MADDAH, word)
    word = _decompose_hamza(word)
    # alef maqsura pronounced as yaa
    word = re.sub(f"(?<={KASRA})ى", "ي", word)
    word = re.sub(f"(?<={KASRA}{SHADDA})ى", "ي", word)
    word = re.sub(f"ى(?=[{VOWELS}{SHADDA}{SUKUN}{MADDAH}])", "ي", word)
    # tanween
    nxt = first_letter(next_word)

    def tanween(m):
        mark, rest = m.group(1), m.group(2)
        if rest.startswith((SMALL_MEEM, SMALL_LOW_MEEM)):
            return PLAIN_VOWEL[mark] + rest
        if nxt and nxt not in IZHAR:
            return OPEN_TANWEEN[mark] + rest
        return mark + rest
    word = re.sub(f"([{FATHATAN}{DAMMATAN}{KASRATAN}])(.*)$", tanween, word)
    return POST_CONVERSION.get(word, word)


def aya_number(n):
    return AYA_MARK + "".join(chr(0x0660 + int(d)) for d in str(n))


def is_marker(tok):
    return tok.startswith(AYA_MARK) or tok in (RUB_EL_HIZB, SAJDA)


def next_word(tokens, i):
    """The first real word after position i (skipping aya numbers, ۞, ۩)."""
    for later in tokens[i + 1:]:
        if not is_marker(later):
            return later
    return ""


def convert_tokens(tokens):
    """Convert a sequence of Tanzil tokens (words, aya-number tokens like
    '۝١٢', '۞', '۩'). Returns display tokens: '۞' is merged into the next
    word and '۩' into the previous one."""
    out = [tok if is_marker(tok) else convert_word(tok, next_word(tokens, i))
           for i, tok in enumerate(tokens)]
    merged = []
    for tok in out:
        if merged and merged[-1] == RUB_EL_HIZB:
            merged[-1] = RUB_EL_HIZB + tok
        elif tok == SAJDA and merged:
            merged[-1] += tok
        else:
            merged.append(tok)
    return merged


WAQF_MARKS = re.compile("[ۖ-ۜ]")


def strip_pause_marks(token):
    return WAQF_MARKS.sub("", token)


def apply_pause_marks(tokens, reference):
    """Take pause marks (waqf, U+06D6-U+06DC) from `reference` tokens.

    The 1441H print revised ~350 pause marks; Tanzil keeps the earlier ones.
    Tokens are aligned on their text without pause marks; wherever a token
    matches its reference token apart from pause marks, the reference's marks
    are used. Letters and vowels always stay Tanzil's. Returns (tokens, n_changed)."""
    import difflib
    ours = [strip_pause_marks(t) for t in tokens]
    theirs = [strip_pause_marks(t) for t in reference]
    out = list(tokens)
    changed = 0
    for block in difflib.SequenceMatcher(None, ours, theirs, autojunk=False).get_matching_blocks():
        for k in range(block.size):
            i, j = block.a + k, block.b + k
            if out[i] != reference[j]:
                out[i] = reference[j]
                changed += 1
    return out, changed
