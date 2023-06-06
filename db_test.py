"""Testing the Generated JSON DB including all Quran data
"""
import unittest
import json
from build_db import DB_JSON_FILE


class Test(unittest.TestCase):
    """Testing the Generated JSON DB including all Quran data
    """
    try:
        with open(DB_JSON_FILE, 'r', encoding="utf-8") as file_db:
            db = json.load(file_db)
    except FileNotFoundError:
        print(f'{DB_JSON_FILE} file is not found!')
        db = {}
    def test_0_db_fields(self):
        """Test all JSON header fields if exist
        """
        for field in ['title','published','font_family','font_url',
                      'font_size','line_width','suras']:
            # check if the obtained field is null or not
            self.assertIsNotNone(self.db[field])  # null will fail the test

    def test_1_sura_count(self):
        """Test Sura Count
        """
        self.assertEqual(len(self.db['suras']), 114, "Missing Suras!")

if __name__ == '__main__':
    unittest.main()
