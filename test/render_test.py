"""Testing the Render of all Quran data
"""
import os
import time
import unittest
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
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
    chrome_options.set_capability("loggingPrefs", {'performance': 'ALL'})
    web_driver = webdriver.Chrome(options=chrome_options)
    test_file = os.path.join("template", "render_test.html")
    test_url = "http://localhost:8000/" + test_file
    web_driver.get(test_url)
    time.sleep(10)

    def dump_log(self):
        """Prints console logs from the browser"""
        lines = []
        for entry in self.web_driver.get_log('browser'):
            lines.append(entry)
        return lines

    def set_page(self, page):
        """Sets page argument in the test.html"""
        with open(self.test_file, "r", encoding="utf8") as template:
            soup = BeautifulSoup(template.read(), 'html.parser')
        soup.find("quran-madina-html")["page"] = page #type: ignore
        with open(self.test_file, 'w', encoding="utf8") as file:
            file.write(str(soup))
        self.web_driver.refresh()
        try:
            WebDriverWait(self.web_driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "quran-madina-html-line")) )
        except TimeoutException:
            print(f"Timeout Exception at page {page}")
        
    def test_0_lines_exists(self):
        """Check if all 15 lines exist in all pages
        """
        for page in range(3, 605):
            self.set_page(page)
            lines = self.web_driver.execute_script('return document.getElementsByTagName'
                                                   '("quran-madina-html-line").length')
            self.assertEqual(lines, 15, f'Page {page} should have 15 lines, found {lines}!'
                                        f'\n::Console::\n{self.dump_log()}')

    def test_1_lines_exists_short_pages(self):
        """Check if all 15 lines exist in all pages
        """
        for page in range(1, 3):
            self.set_page(page)
            lines = self.web_driver.execute_script('return document.getElementsByTagName'
                                                   '("quran-madina-html-line").length')
            self.assertEqual(lines, 8, f'Page {page} should have 8 lines, found {lines}!'
                                        f'\n::Console::\n{self.dump_log()}')
            
if __name__ == '__main__':
    unittest.main()
