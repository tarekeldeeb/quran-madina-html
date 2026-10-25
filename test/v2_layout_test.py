"""v2 1441H DB against the print: line breaks and word spacing.

    python -m pytest test/v2_layout_test.py
"""
import io
import json
# pylint: disable=line-too-long,wrong-import-position  # escaped Arabic literals; sys.path setup
import os
import sys
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src", "db", "v2"))

DB = os.path.join(ROOT, "assets", "db", "v2", "Madina-1441H.json")
PRINT = os.path.join(ROOT, "src", "db", "v2", "data", "print-1441H-lines.json")
MARKER = "۝"


def db_lines(db):
    """{(page, line): [(token, features, "sura:aya:index")]} rebuilt from the
    suras/ayas parts (index counts the aya's tokens, its number last)."""
    lines = {}
    for s, sura in enumerate(db["suras"], start=1):
        for a, aya in enumerate(sura["ayas"][2:], start=1):
            page, prev, i = aya["p"], None, 0
            for part in aya["r"]:
                if prev is not None and part["l"] < prev:
                    page += 1
                prev = part["l"]
                for token, feats in zip(part["t"].split(), part["f"]):
                    i += 1
                    lines.setdefault((page, part["l"]), []).append((token, feats, f"{s}:{a}:{i}"))
    return lines


class PrintLayoutTest(unittest.TestCase):
    """The 1441H DB against the print's line breaks and word gaps."""
    @classmethod
    def setUpClass(cls):
        with open(DB, encoding="utf-8") as fh:
            cls.db = json.load(fh)
        with open(PRINT, encoding="utf-8") as fh:
            cls.print_pages = json.load(fh)["pages"]
        cls.lines = db_lines(cls.db)

    def test_1_same_lines_as_print(self):
        """Every page has the print's lines, of the print's kinds."""
        for p, page in enumerate(self.print_pages, start=1):
            rows = self.db["lines"][p - 1]
            self.assertEqual(len(rows), len(page), f"page {p}")
            for l, (row, pl) in enumerate(zip(rows, page), start=1):
                self.assertEqual(row["k"], pl["k"], f"p{p} l{l}")

    def test_2_words_per_line_match_print(self):
        """Each text line starts and ends on the print's words."""
        for p, page in enumerate(self.print_pages, start=1):
            for l, pl in enumerate(page, start=1):
                if pl["k"] != "text":
                    continue
                words = self.lines[(p, l)]
                self.assertEqual((words[0][2], words[-1][2]), (pl["a"], pl["b"]), f"p{p} l{l}")

    def test_3_no_line_starts_with_aya_number(self):
        """The print never opens a line with an aya number."""
        for (p, l), words in self.lines.items():
            self.assertNotIn(MARKER, words[0][0], f"p{p} l{l}")

    def test_4_no_overlapping_shrink(self):
        """shr1/shrr shrink by overlapping letters; the print never does."""
        for (p, l), words in self.lines.items():
            for token, feats, _ in words:
                self.assertNotIn("shr", feats, f"p{p} l{l} {token}")

    def test_5_word_gaps_like_print(self):
        """On sample pages, no two words come closer (ink to ink, band by band)
        than the print's own narrowest gaps."""
        import uharfbuzz as hb
        from fontTools.ttLib import TTFont
        import ink
        import justify

        tt = TTFont(os.path.join(ROOT, self.db["font_url"]))
        tt.flavor = None
        data = io.BytesIO()
        tt.save(data)
        font = hb.Font(hb.Face(data.getvalue()))
        full = self.db["line_width"] * 1000
        worst = 1.0
        for p in (3, 50, 300, 507, 579, 600):
            for l in range(1, 16):
                row = self.db["lines"][p - 1][l - 1]
                if row["k"] != "text" or (p, l) not in self.lines:
                    continue
                words = self.lines[(p, l)]
                profs = [justify.word_profile(font, t, {k: int(v or 1) for k, _, v in (
                    kv.partition("=") for kv in f.split(","))} if f else {}) for t, f, _ in words]
                c = row.get("c", 1)
                n = len(words)
                for k, space in enumerate(row["s"]):
                    ck = 1 if MARKER in words[k][0] else c
                    cn = 1 if MARKER in words[k + 1][0] else c
                    # the DOM keeps narrowed words' boxes: add back what each lost inside
                    lost_k = 0 if ck == 1 else (1 - c) * profs[k].advance * (1 if k == 0 else 0.5)
                    lost_n = 0 if cn == 1 else (1 - c) * profs[k + 1].advance * (
                        1 if k + 1 == n - 1 else 0.5)
                    gap = (space * 1000 + lost_k + lost_n
                           + ink.clearance_offset(profs[k], profs[k + 1], ck, cn))
                    ratio = gap * row.get("z", 1) / full      # share of the line width
                    worst = min(worst, ratio)
        # print: 1% of word gaps are below 0.0042 of the line, none touch
        self.assertGreater(worst, 0.004, f"closest words: {worst:.4f} of the line")


if __name__ == "__main__":
    unittest.main()


class OtherLayoutsTest(unittest.TestCase):
    """1405H and IndoPak DBs: structure shared with 1441H."""

    def test_same_suras_and_ayas_in_every_layout(self):
        """Every layout has the same suras and Kufan aya counts."""
        counts = {}
        for stem in ("Madina-1441H", "Madina-1405H", "IndoPak-15"):
            with open(os.path.join(ROOT, "assets", "db", "v2", stem + ".json"), encoding="utf-8") as fh:
                db = json.load(fh)
            counts[stem] = [len(s["ayas"]) for s in db["suras"]]
        self.assertEqual(sum(counts["Madina-1441H"]) - 2 * 114, 6236)
        self.assertEqual(counts["Madina-1405H"], counts["Madina-1441H"])
        self.assertEqual(counts["IndoPak-15"], counts["Madina-1441H"])

    def test_indopak_ayas_end_with_their_marker(self):
        """Every IndoPak aya ends with an aya number; 610 pages."""
        with open(os.path.join(ROOT, "assets", "db", "v2", "IndoPak-15.json"), encoding="utf-8") as fh:
            db = json.load(fh)
        self.assertEqual(len(db["lines"]), 610)
        for s, sura in enumerate(db["suras"], start=1):
            for a, aya in enumerate(sura["ayas"][2:], start=1):
                self.assertIn(MARKER, aya["r"][-1]["t"].split()[-1], f"{s}:{a}")


class BrowserFeaturesTest(unittest.TestCase):
    """The browser gets on/off twins of the DB's jpKK=v features (CoreText ignores values)."""

    def test_font_has_on_off_feature_for_every_pair(self):
        """Each layout's font carries q<KK><v> for every (jpKK, v) its DB uses."""
        from fontTools.ttLib import TTFont
        import font_patch
        for stem in ("Madina-1441H", "Madina-1405H", "IndoPak-15"):
            with open(os.path.join(ROOT, "assets", "db", "v2", stem + ".json"), encoding="utf-8") as fh:
                db = json.load(fh)
            tags = {r.FeatureTag for r in
                    TTFont(os.path.join(ROOT, db["font_url"]))["GSUB"].table.FeatureList.FeatureRecord}
            missing = {font_patch.bool_tag(k, v) for k, v in font_patch.db_feature_pairs(db)} - tags
            self.assertFalse(missing, f"{stem}: {sorted(missing)[:5]}")
