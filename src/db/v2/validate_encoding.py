"""Check encoding.py: convert Tanzil words and compare with DigitalKhatt's text.

Tanzil text is taken from a v1 JSON DB (its text is Tanzil's, plus aya
ornaments and build-inserted tatweels, which are removed here exactly:
Tanzil only uses a tatweel to carry a following mark).

Usage:
  python src/db/v2/validate_encoding.py assets/db/Madina05-Hafs-16px.json DK_TEXT.ts [...]
Prints, per DigitalKhatt text, how many tokens match and every difference.
"""
# pylint: disable=wrong-import-position
import argparse
import difflib
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(__file__))
import tanzil_encoding as encoding

WAQF = re.compile("[ۖ-ۜ]")


def tanzil_tokens_from_v1_db(path):
    """Tanzil tokens (converted) recovered from a v1 DB."""
    with open(path, encoding="utf-8") as fh:
        db = json.load(fh)
    lines = {}
    for sura in db["suras"]:
        for aya in sura["ayas"]:
            for part in aya["r"]:
                key = (aya["p"], part["l"])
                lines[key] = lines.get(key, "") + part["t"]
    tokens = []
    for key in sorted(lines):
        text = lines[key]
        if text.strip().startswith("سورة"):
            continue
        text = "".join(c for i, c in enumerate(text) if c != "ـ" or (
            i + 1 < len(text) and unicodedata.category(text[i + 1]) == "Mn"))
        text = re.sub(r"\s*﴿([٠-٩]+)﴾", lambda m: " ۝" + m.group(1), text)
        tokens += text.split()
    return tokens


def dk_tokens(path):
    """Tokens of a DigitalKhatt layout text, sura titles left out."""
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    pages = re.findall(r"\[\s*((?:'[^']*',?\s*)+)\]", src)
    return [w for p in pages for line in re.findall(r"'([^']*)'", p)
            if not line.startswith("سُورَةُ") for w in line.split()]


def main():
    """Compare Tanzil, converted, with each DigitalKhatt text; print the differences."""
    ap = argparse.ArgumentParser()
    ap.add_argument("v1_db")
    ap.add_argument("dk_texts", nargs="+")
    a = ap.parse_args()
    converted = encoding.convert_tokens(tanzil_tokens_from_v1_db(a.v1_db))
    for path in a.dk_texts:
        reference = dk_tokens(path)
        sm = difflib.SequenceMatcher(None, converted, reference, autojunk=False)
        same = sum(b.size for b in sm.get_matching_blocks())
        waqf_only, other = 0, []
        for op, a1, a2, b1, b2 in sm.get_opcodes():
            if op == "equal":
                continue
            if [WAQF.sub("", x) for x in converted[a1:a2]] == \
                    [WAQF.sub("", x) for x in reference[b1:b2]]:
                waqf_only += max(a2 - a1, b2 - b1)
            else:
                other.append((converted[a1:a2], reference[b1:b2]))
        print(f"{os.path.basename(path)}: {same}/{len(converted)} tokens identical; "
              f"{waqf_only} differ only in pause marks; {len(other)} other differences")
        for ours, theirs in other:
            print("   ", " ".join(ours), "->", " ".join(theirs))


if __name__ == "__main__":
    main()
