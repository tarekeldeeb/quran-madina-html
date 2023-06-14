"""Testing the Generated JSON DB including all Quran data
"""
import unittest
import glob
import json


class Test(unittest.TestCase):
    """Testing the Generated JSON DB including all Quran data
    """
    db = []
    for f in glob.glob('./*px.json'):
        with open(f, 'r', encoding="utf-8") as file_handler:
            db.append({"name":f,"data":json.load(file_handler)})

    def test_0_db_fields(self):
        """Test all JSON header fields if exist
        """
        for field in ['title','published','font_family','font_url',
                      'font_size','line_width','suras']:
            # check if the obtained field is null or not
            for data in self.db:
                self.assertIsNotNone(data["data"][field])  # null will fail the test

    def test_1_sura_count(self):
        """Test Sura Count
        """
        for data in self.db:
            self.assertEqual(len(data["data"]['suras']), 114, "Missing Suras!")

if __name__ == '__main__':
    unittest.main()
