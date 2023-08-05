"""Testing the Generated JSON DB including all Quran data
"""
import unittest
import glob
import json


class Test(unittest.TestCase):
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
            for sura in data["data"]['suras']:
                for aya in sura['ayas']:
                    for part in aya['r']:
                        self.assertGreaterEqual(part['s'], 0.8, "Stretch factor is too low")
                        self.assertLessEqual(part['s'], 1.2, "Stretch factor is too high")

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
            for sura in data["data"]['suras']:
                for aya in sura['ayas']:
                    for part in aya['r']:
                        self.assertLessEqual(part['o'], data["data"]["line_width"],
                                             "Offset is too high")

if __name__ == '__main__':
    unittest.main()
