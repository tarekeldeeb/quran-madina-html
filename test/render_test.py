"""Testing the Render of all Quran data
"""
import os
import time
import unittest
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class BasicRenderTest(unittest.TestCase):
    """Testing the Render of all Quran data
    """
    chrome_options = Options()
    options = [
        "--headless",
        "--disable-gpu",
        "--ignore-certificate-errors",
        "--disable-extensions",
        "--no-sandbox",
        "--disable-dev-shm-usage"
    ]
    for option in options:
        chrome_options.add_argument(option)
    chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
    web_driver = webdriver.Chrome(options=chrome_options)
    test_file = os.path.join("template", "render_test.html")
    test_url = "http://localhost:8000/" + test_file
    web_driver.get(test_url)
    time.sleep(10)

    def set_page(self, page):
        """Sets page argument in the test.html"""
        with open(self.test_file, "r", encoding="utf8") as template:
            soup = BeautifulSoup(template.read(), 'html.parser')
        soup.find("quran-madina-html")["page"] = page #type: ignore
        with open(self.test_file, 'w', encoding="utf8") as file:
            file.write(str(soup))

    def test_0_lines_exists(self):
        """Check if all 15 lines exist in all pages
        """
        for page in range(3, 604):
            self.set_page(page)
            self.web_driver.refresh()
            lines = self.web_driver.execute_script('return document.getElementsByTagName'
                                                   '("quran-madina-html-line").length')
            self.assertEqual(lines, 15, f"Page {page} should have 15 lines, found {lines}!")

if __name__ == '__main__':
    unittest.main()
