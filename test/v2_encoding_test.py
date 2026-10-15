"""Tanzil -> DigitalKhatt font encoding (src/db/v2/tanzil_encoding.py)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "db", "v2"))
import tanzil_encoding as E

CGJ = "͏"


class EncodingTest(unittest.TestCase):
    def test_hamza_on_alef_is_decomposed(self):
        self.assertEqual(E.convert_word("أَمْ"),        # أَمْ
                         "ا" + CGJ + "ٔ" + CGJ + "َمْ")

    def test_hamza_below(self):
        self.assertEqual(E.convert_word("إِنَّ"),  # إِنَّ
                         "إ" + CGJ + "ِنَّ")

    def test_no_tatweel_before_dagger_alef(self):
        self.assertEqual(E.convert_word("صَـٰر"),
                         "صَٰر")

    def test_alef_maqsura_after_kasra(self):
        self.assertEqual(E.convert_word("فِى"), "فِي")  # فِى

    def test_tanween_open_before_idgham_letter(self):
        # غِشَٰوَةٌۖ وَلَهُمْ  -> open dammatan
        self.assertIn("ࣱ", E.convert_word("غِشَٰوَ"
                                               "ةٌۖ", "وَلَ"))

    def test_tanween_stacked_before_throat_letter_and_wasl(self):
        word = "عَذَابٌ"                  # عَذَابٌ
        self.assertTrue(E.convert_word(word, "عَظِيم").endswith("ٌ"))
        self.assertTrue(E.convert_word(word, "ٱلَّه").endswith("ٌ"))

    def test_iqlab_tanween_becomes_vowel(self):
        self.assertEqual(E.convert_word("أَلِيمٌۢ")[-2:],
                         "ُۢ")

    def test_tokens_merge_rub_and_sajda(self):
        out = E.convert_tokens(["۞", "مَا", "۩", E.aya_number(12)])
        self.assertEqual(out, ["۞مَا۩", "۝١٢"])


if __name__ == "__main__":
    unittest.main()
