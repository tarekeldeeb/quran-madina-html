"""Testing the Generated JSON DB including all Quran data
"""
import unittest
import glob
import json


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

    def test_5_offset_boundaries(self):
        """Test Offset < Page width
        """
        for data in self.db:
            for sura_index, sura in enumerate(data["data"]['suras']):
                for aya_index, aya in enumerate(sura['ayas']):
                    for part_index, part in enumerate(aya['r']):
                        self.assertLessEqual(part['o'], data["data"]["line_width"],
                            f"Offset is too high @{sura_index}:{aya_index}:{part_index}")

if __name__ == '__main__':
    unittest.main()
