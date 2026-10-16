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

    def test_pause_marks_from_reference(self):
        ours = ["\u0628\u064E\u0644\u064E\u0649\u0670", "\u0627\u0644\u0644\u0651\u064E\u0647\u0650\u06D7"]
        ref = ["\u0628\u064E\u0644\u064E\u0649\u0670\u06DA", "\u0627\u0644\u0644\u0651\u064E\u0647\u0650\u06DA"]
        out, changed = E.apply_pause_marks(ours, ref)
        self.assertEqual((out, changed), (ref, 2))

    def test_pause_marks_never_change_letters(self):
        ours = ["\u0645\u064E\u0627"]
        out, changed = E.apply_pause_marks(ours, ["\u0645\u064F\u0627\u06DA"])
        self.assertEqual((out, changed), (ours, 0))

    def test_17_7_as_tanzil_ships_it(self):
        # Tanzil 1.1 carries the small waw of 17:7 on a tatweel; both spellings map to the font's word
        dk = "\u0644\u0650\u064A\u064E\u0633\u064F\u034F\u08F3\u0653\u0640\u0654\u034F\u064F\u0648\u0627\u06DF"
        tanzil = "\u0644\u0650\u064A\u064E\u0633\u064F\u0640\u06E5\u0653\u0640\u0654\u064F\u0648\u0627\u06DF"
        self.assertEqual(E.convert_word(tanzil, ""), dk)

    def test_marks_and_signs_for_a_bare_tanzil_text(self):
        # downloaded without marks: pause marks, ۞ and ۩ come from the layout text,
        # whose spacing around ۞ and ۩ varies
        ours = ["ذَٰلِكَ", "فِيهِ", "وَأَنَابَ", "\u06DD\u0662\u0664"]
        ref = ["۞", "ذَٰلِكَ", "فِيهِۛ", "وَأَنَابَ", "۩\u06DD\u0662\u0664"]
        out, _ = E.apply_pause_marks(ours, ref, signs=True)
        self.assertEqual(out, ["۞ذَٰلِكَ", "فِيهِۛ", "وَأَنَابَ۩", "\u06DD\u0662\u0664"])


if __name__ == "__main__":
    unittest.main()
