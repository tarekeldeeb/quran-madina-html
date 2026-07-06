"""Testing the Generated JSON DB including all Quran data
"""
import unittest
import glob
import json
import re

# Mirrors QuranLine.AYA_MARKER_PATTERN/SHORT_WORD_LIMIT in src/db/build_db.py: an aya-number
# ornament is always its own whitespace-separated token, so it's excluded from the word count.
AYA_MARKER_PATTERN = re.compile(r'^(﴿[٠-٩]+﴾|۝\d+)$')
SHORT_WORD_LIMIT = 2


class BasicDBTest(unittest.TestCase):
    """Testing the Generated JSON DB including all Quran data
    """
    db = []
    for f in glob.glob('assets/db/*px.json'):
        with open(f, 'r', encoding="utf-8") as file_handler:
            db.append({"name":f,"data":json.load(file_handler)})

    def _line_exists(self, suras, page, line):
        for sura in suras:
            for aya in sura['ayas']:
                if aya['p'] == page:
                    for part in aya['r']:
                        if part['l'] == line:
                            return True
        return False

    def test_0_db_exists(self):
        """Check if DB exists
        """
        self.assertGreater(len(self.db), 0)

    def test_1_db_fields(self):
        """Test all JSON header fields if exist
        """
        for field in ['title','published','font_family','font_url',
                      'font_size','line_width','suras']:
            # check if the obtained field is null or not
            for data in self.db:
                self.assertIsNotNone(data["data"][field])  # null will fail the test

    def test_2_sura_count(self):
        """Test Sura Count
        """
        for data in self.db:
            self.assertEqual(len(data["data"]['suras']), 114, "Missing Suras!")

    def test_3_stretch_boundaries(self):
        """Test Stretching factors
        """
        for data in self.db:
            for sura_index, sura in enumerate(data["data"]['suras']):
                for aya_index, aya in enumerate(sura['ayas']):
                    for part_index, part in enumerate(aya['r']):
                        stretching_factor = part['s']
                        if stretching_factor >= 0:
                            self.assertGreaterEqual(stretching_factor, 0.5,
                                f"Stretch factor is low @{sura_index}:{aya_index}:{part_index}")
                            self.assertLessEqual(stretching_factor, 2, # Upper boundary=2 (awful)
                                f"Stretch factor is high @{sura_index}:{aya_index}:{part_index}")

    def test_4_page_15_lines(self):
        """Ensure all pages have 15 lines
        """
        for data in self.db:
            for page in range(3,605):
                for line in range(1,16):
                    self.assertTrue(self._line_exists(data["data"]['suras'], page, line),
                                    f'Missing Line: {line} in page: {page}!')

    def test_5_stretch_minus_one_restricted(self):
        """A part is only allowed stretch=-1 (unjustified, natural width) if it's on Al-Fatiha's
        page (page 1: every line there is deliberately un-stretched regardless of length), it's
        part of a surah's actual last line, or its line is a standalone short line (e.g. a Huroof
        Muqattaat opener like "الٓمٓ ﴿١﴾", <= SHORT_WORD_LIMIT real words). Anything else with -1
        means a normal-length line was mistakenly left un-stretched - which either looks flat
        (mid-surah) or overflows/gets clipped by the frame (e.g. this used to happen throughout
        Al-Baqara's page 2, since page<=2 was once hardcoded to -1 unconditionally).
        """
        for data in self.db:
            for sura_index, sura in enumerate(data["data"]['suras']):
                # ayas[0:2] are the synthetic surah-name/basmala entries (always centered by
                # design, regardless of page); only real ayas are checked here.
                real_ayas = sura['ayas'][2:]
                self.assertTrue(real_ayas, f"Sura {sura_index} has no real ayas!")
                last_aya = real_ayas[-1]
                sura_end = (last_aya['p'], last_aya['r'][-1]['l'])
                # Group parts by (page, line) so multi-part lines are word-counted as a whole.
                lines = {}
                for aya in real_ayas:
                    for part in aya['r']:
                        lines.setdefault((aya['p'], part['l']), []).append(part)
                for (page, line), parts in lines.items():
                    if any(part['s'] == -1 for part in parts):
                        words = [tok for part in parts for tok in part['t'].split()
                                 if not AYA_MARKER_PATTERN.match(tok)]
                        is_fatiha_page = page == 1
                        is_sura_end = (page, line) == sura_end
                        is_short_standalone = len(words) <= SHORT_WORD_LIMIT
                        self.assertTrue(is_fatiha_page or is_sura_end or is_short_standalone,
                            f"Unexpected stretch=-1 in {data['name']} sura {sura_index} "
                            f"page {page} line {line}: {' '.join(p['t'] for p in parts)}")

if __name__ == '__main__':
    unittest.main()
