"""v2 fonts and DBs carry the CoreText joining fix (src/db/v2/cursive_fix.py)."""
import json
import os
import sys
import unittest

from fontTools.ttLib import TTFont

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src", "db", "v2"))
import cursive_fix  # noqa: E402  pylint: disable=wrong-import-position

STEMS = ("Madina-1441H", "Madina-1405H", "IndoPak-15")


def load(stem):
    """The DB and its font."""
    with open(os.path.join(ROOT, "assets", "db", "v2", stem + ".json"), encoding="utf-8") as fh:
        db = json.load(fh)
    return db, TTFont(os.path.join(ROOT, db["font_url"]))


def parts(db):
    """Every part of every aya."""
    return [part for sura in db["suras"] for aya in sura["ayas"] for part in aya["r"]]


class CursiveFixTest(unittest.TestCase):
    """Uniform cursive chains in the fonts, height corrections and CGJ-free text in the DBs."""

    @classmethod
    def setUpClass(cls):
        cls.layouts = {stem: load(stem) for stem in STEMS}

    def test_no_right_to_left_cursive_lookup(self):
        """CoreText cannot mix cursive directions: no cursive lookup keeps RightToLeft."""
        for stem, (_, font) in self.layouts.items():
            for i, lookup in enumerate(font["GPOS"].table.LookupList.Lookup):
                if cursive_fix._lookup_type(lookup) == 3:  # pylint: disable=protected-access
                    self.assertFalse(lookup.LookupFlag & 1, f"{stem}: lookup {i}")

    def test_every_z_tag_is_in_the_font(self):
        """Each height correction a DB uses is a GPOS feature of its font."""
        for stem, (db, font) in self.layouts.items():
            have = {r.FeatureTag for r in font["GPOS"].table.FeatureList.FeatureRecord}
            used = set()
            for part in parts(db):
                for css in (part.get("f") or []) + [g for g in part.get("g") or [] if g]:
                    used.update(t for t in css.split(",") if t.startswith("z"))
            self.assertTrue(used, stem)
            self.assertFalse(used - have, f"{stem}: {sorted(used - have)[:5]}")

    def test_parts_are_consistent(self):
        """f has one entry per word, g (when present) too."""
        for stem, (db, _) in self.layouts.items():
            for part in parts(db):
                n = len(part["t"].split(" ")) if part["t"] else 0
                self.assertEqual(len(part["f"]), n, f"{stem}: {part['t']}")
                if "g" in part:
                    self.assertEqual(len(part["g"]), n, f"{stem}: {part['t']}")

    def test_cgj_only_where_harfbuzz_needs_it(self):
        """The text keeps a CGJ only in the few contexts strip_cgj keeps."""
        for stem, (db, _) in self.layouts.items():
            for part in parts(db):
                for word in part["t"].split(" "):
                    self.assertEqual(cursive_fix.strip_cgj(word), word, f"{stem}: {word!r}")

    def test_strip_cgj(self):
        """Decomposed hamza and tatweel joints lose the CGJ; sukun + sakta keeps it."""
        self.assertEqual(cursive_fix.strip_cgj("\u0640\u0654\u034f\u064e\u0627"),
                         "\u0640\u0654\u064e\u0627")
        self.assertEqual(cursive_fix.strip_cgj("\u0627\u034f\u0654\u034f\u064e"),
                         "\u0627\u0654\u064e")
        self.assertEqual(cursive_fix.strip_cgj("مَنْ͏ۜ"), "مَنْ͏ۜ")

    def test_z_tag(self):
        """Position in base 36, shift biased into two base-36 digits."""
        self.assertEqual(cursive_fix.z_tag(0, 0), "z0i0")
        self.assertEqual(cursive_fix.z_tag(10, -1), "zahz")
        with self.assertRaises(ValueError):
            cursive_fix.z_tag(36, 0)

    def test_word_features(self):
        """Unstretched words take f's z tags unless g says otherwise."""
        part = {"t": "a b c", "f": ["jp04=3,z0i0", "z1i1", ""], "g": [None, "", None]}
        self.assertEqual(cursive_fix.word_features(part, 0, True), "jp04=3,z0i0")
        self.assertEqual(cursive_fix.word_features(part, 0, False), "z0i0")
        self.assertEqual(cursive_fix.word_features(part, 1, False), "")
        self.assertEqual(cursive_fix.word_features(part, 2, False), "")


if __name__ == "__main__":
    unittest.main()
