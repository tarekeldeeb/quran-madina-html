"""Testing the Render of all Quran data
"""
import os
import re
import json
import time
import unittest
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# The render_test.html template loads the dist with default attributes, so the page fetches the
# default DB (name=Madina05, font=me_quran, size=16). Drive the words= expectations from that same
# JSON so the assertions stay in sync with the data regardless of font.
DEFAULT_DB = os.path.join("assets", "db", "Madina05-me_quran-16px.json")
AYA_MARKER = re.compile("[﴿﴾۝]")  # ornate parens / end-of-aya: not words


def aya_word_list(aya):
    """Selectable words of an aya (whitespace-separated, excluding aya-number markers)."""
    words = []
    for part in aya["r"]:
        for token in part["t"].split():
            if token and not AYA_MARKER.search(token):
                words.append(token)
    return words


def collect_words(suras, sura_start, aya_start, word_end):
    """Mirror of the JS collectWordParts() word walk: reading order from (sura_start, aya_start),
    crossing sura boundaries (aya indices 0/1 are name/basmala and are not counted), until at least
    `word_end` words have been gathered."""
    words = []
    sura = sura_start
    while sura < len(suras):
        ayas = suras[sura]["ayas"]
        aya = aya_start if sura == sura_start else 0
        while aya < len(ayas):
            if aya >= 2:  # 0/1 are the sura name / basmala decoration, not words
                words.extend(aya_word_list(ayas[aya]))
                if len(words) >= word_end:
                    return words
            aya += 1
        sura += 1
    return words

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
    chrome_options.set_capability("goog:loggingPrefs", {'performance': 'ALL'})
    web_driver = webdriver.Chrome(options=chrome_options)
    test_file = os.path.join("template", "render_test.html")
    test_url = "http://localhost:8000/" + test_file
    web_driver.get(test_url)
    time.sleep(10)
    with open(DEFAULT_DB, encoding="utf8") as _db_handle:
        db = json.load(_db_handle)

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
        tag = soup.find("quran-madina-html")
        for key in ("sura", "aya", "words", "headless"):  # ensure a clean page-only render
            if key in tag.attrs:  # type: ignore
                del tag[key]  # type: ignore
        tag["page"] = page  # type: ignore
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

    def set_attrs(self, **attrs):
        """Rewrite the template's <quran-madina-html> tag with fresh attributes and reload"""
        with open(self.test_file, "r", encoding="utf8") as template:
            soup = BeautifulSoup(template.read(), 'html.parser')
        tag = soup.find("quran-madina-html")
        for key in ("page", "sura", "aya", "words", "headless"):
            if key in tag.attrs:  # type: ignore
                del tag[key]  # type: ignore
        for key, value in attrs.items():
            tag[key] = str(value)  # type: ignore
        with open(self.test_file, 'w', encoding="utf8") as file:
            file.write(str(soup))
        self.web_driver.refresh()
        try:
            WebDriverWait(self.web_driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "quran-madina-html-line")))
        except TimeoutException:
            print(f"Timeout Exception at {attrs}")

    def visible_words(self):
        """Text of every shown word span (i.e. not hidden by a words= selection), in order"""
        return self.web_driver.execute_script(
            "return Array.from(document.querySelectorAll('span.quran-madina-html-word'))"
            ".filter(w => !w.classList.contains('quran-madina-html-word-hidden'))"
            ".map(w => w.textContent);")

    def count(self, selector):
        """Count DOM elements matching a CSS selector"""
        return self.web_driver.execute_script(
            f"return document.querySelectorAll('{selector}').length;")

    def test_2_words_single_aya_inline(self):
        """words= within one aya: only the selected words show, inline (no header)"""
        self.set_attrs(sura=1, aya=1, words="1:2")
        expected = collect_words(self.db["suras"], 0, 2, 2)[0:2]
        self.assertEqual(self.visible_words(), expected,
                         f"sura1 aya1 words=1:2 should show the first two words\n{self.dump_log()}")
        self.assertEqual(self.count("quran-madina-html-line"), 1, "single line expected")
        self.assertEqual(self.count("quran-madina-html-header"), 0, "no header when inline")

    def test_3_words_separators_equivalent(self):
        """words="1-2" and words="1:2" select the same words"""
        self.set_attrs(sura=1, aya=1, words="1:2")
        colon = self.visible_words()
        self.set_attrs(sura=1, aya=1, words="1-2")
        dash = self.visible_words()
        self.assertEqual(colon, dash, "'-' and ':' separators must be equivalent")
        self.assertEqual(len(dash), 2, "two words expected")

    def test_4_words_single_index(self):
        """A bare words="n" selects exactly one word"""
        self.set_attrs(sura=1, aya=3, words="2")
        expected = collect_words(self.db["suras"], 0, 4, 2)[1:2]
        self.assertEqual(self.visible_words(), expected,
                         f"sura1 aya3 words=2 should show only the 2nd word\n{self.dump_log()}")

    def test_5_words_span_multiple_ayas(self):
        """words= counted from aya may run past it into following ayas (same sura)"""
        self.set_attrs(sura=1, aya=1, words="3-10")
        expected = collect_words(self.db["suras"], 0, 2, 10)[2:10]
        self.assertEqual(self.visible_words(), expected,
                         f"sura1 aya1 words=3-10 should span ayas 1-3\n{self.dump_log()}")
        self.assertEqual(self.count("quran-madina-html-line"), 3, "selection spans 3 lines")
        self.assertEqual(self.count("quran-madina-html-header"), 1, "multiline gets a header")

    def test_6_words_cross_sura_boundary(self):
        """words= keeps counting past the end of a sura into the next one"""
        self.set_attrs(sura=1, aya=7, words="1-10")
        expected = collect_words(self.db["suras"], 0, 8, 10)[0:10]
        self.assertEqual(self.visible_words(), expected,
                         f"sura1 aya7 words=1-10 should cross into sura 2\n{self.dump_log()}")
        # The crossed-into sura (Al-Baqara) renders its first aya and its name decoration line
        self.assertGreaterEqual(self.count(".quran-madina-html-002-001"), 1,
                                "Al-Baqara aya 1 should be rendered after the boundary")
        self.assertEqual(self.count(".quran-madina-html-sura-start"), 1,
                         "the crossed-into sura name carries the sura-start decoration")

    def test_7_words_ignored_with_page(self):
        """words= is ignored when a full page is requested"""
        self.set_attrs(page=5, words="1:2")
        self.assertEqual(self.count("span.quran-madina-html-word"), 0,
                         "page rendering must not split words")
        self.assertEqual(self.count("quran-madina-html-line"), 15,
                         "page 5 still renders 15 lines")

    def test_8_headless_inline_hides_copy(self):
        """headless removes the copy button from an inline (single-line) verse render"""
        self.set_attrs(sura=1, aya=1)
        self.assertEqual(self.count("quran-madina-html-line"), 1, "aya 1:1 fits one line")
        self.assertEqual(self.count("quran-madina-html-copy"), 1, "inline render has a copy button")
        self.set_attrs(sura=1, aya=1, headless=True)
        self.assertEqual(self.count("quran-madina-html-line"), 1, "still one line when headless")
        self.assertEqual(self.count("quran-madina-html-copy"), 0, "headless removes the copy button")

    def test_9_headless_multiline_hides_header(self):
        """headless removes the header from a multiline verse-range render"""
        self.set_attrs(sura=1, aya="1-7")
        self.assertGreater(self.count("quran-madina-html-line"), 1, "aya 1-7 spans many lines")
        self.assertEqual(self.count("quran-madina-html-header"), 1, "multiline render has a header")
        self.set_attrs(sura=1, aya="1-7", headless=True)
        self.assertEqual(self.count("quran-madina-html-header"), 0, "headless removes the header")
        self.assertGreater(self.count("quran-madina-html-line"), 1, "lines are still rendered")

    def test_10_headless_words_paths(self):
        """headless hides chrome on both words= paths without changing the visible words"""
        # Inline words selection: copy button only.
        self.set_attrs(sura=1, aya=1, words="1:2", headless=True)
        self.assertEqual(self.count("quran-madina-html-copy"), 0, "headless drops inline copy button")
        self.assertEqual(self.visible_words(), collect_words(self.db["suras"], 0, 2, 2)[0:2],
                         "selected words are unchanged by headless")
        # Multiline words selection: header only.
        self.set_attrs(sura=1, aya=1, words="3-10", headless=True)
        self.assertEqual(self.count("quran-madina-html-header"), 0, "headless drops multiline header")
        self.assertEqual(self.visible_words(), collect_words(self.db["suras"], 0, 2, 10)[2:10],
                         "selected words are unchanged by headless")

    def test_11_headless_false_keeps_chrome(self):
        """headless=False (and the default) leave the header/copy button in place"""
        self.set_attrs(sura=1, aya=1, headless="False")
        self.assertEqual(self.count("quran-madina-html-copy"), 1, "headless=False keeps copy")
        self.set_attrs(sura=1, aya="1-7", headless="False")
        self.assertEqual(self.count("quran-madina-html-header"), 1, "headless=False keeps header")

    def test_12_words_invalid_range_falls_back(self):
        """A reversed or zero words= range is rejected; the aya renders normally (no word spans)"""
        for bad in ("3-1", "0", "0-2"):
            self.set_attrs(sura=1, aya=1, words=bad)
            self.assertEqual(self.count("span.quran-madina-html-word"), 0,
                             f"words={bad} should not split into word spans\n{self.dump_log()}")
            self.assertGreaterEqual(self.count("quran-madina-html-line"), 1,
                                    f"words={bad} should still render the aya")

    def test_13_words_capped_at_500(self):
        """An over-long words= span is capped at 500 visible words"""
        self.set_attrs(sura=1, aya=1, words="1-1000")
        self.assertEqual(len(self.visible_words()), 500, f"selection capped at 500\n{self.dump_log()}")

    def test_14_words_no_fully_hidden_leading_lines(self):
        """Leading lines that are entirely hidden are skipped: every word line shows >=1 word"""
        self.set_attrs(sura=1, aya=1, words="20-22")
        expected = collect_words(self.db["suras"], 0, 2, 22)[19:22]
        self.assertEqual(self.visible_words(), expected,
                         f"words=20-22 should show words 20..22\n{self.dump_log()}")
        fully_hidden = self.web_driver.execute_script(
            "return Array.from(document.querySelectorAll('quran-madina-html-line')).filter("
            "function(line){var w=line.querySelectorAll('span.quran-madina-html-word');"
            "return w.length>0 && Array.from(w).every(function(s){"
            "return s.classList.contains('quran-madina-html-word-hidden');});}).length;")
        self.assertEqual(fully_hidden, 0, "no rendered line may be entirely hidden")

    def test_15_copy_excludes_hidden_words(self):
        """Copy-to-clipboard carries only the visible words, not the ones hidden by words="""
        self.set_attrs(sura=1, aya=1, words="1:2")
        self.web_driver.execute_script(
            "window.__copied=null;window.alert=function(){};"
            "navigator.clipboard.writeText=function(t){window.__copied=t;return Promise.resolve();};")
        self.web_driver.execute_script(
            "document.querySelector('quran-madina-html-copy svg')."
            "dispatchEvent(new MouseEvent('click',{bubbles:true}));")
        copied = self.web_driver.execute_script("return window.__copied;")
        shown = collect_words(self.db["suras"], 0, 2, 3)
        self.assertIsNotNone(copied, f"copy handler should have run\n{self.dump_log()}")
        self.assertIn(shown[0], copied)
        self.assertIn(shown[1], copied)
        self.assertNotIn(shown[2], copied, "a hidden word must not be copied")
        self.assertIn(self.db["suras"][0]["name"], copied, "sura name is appended to the copy")

if __name__ == '__main__':
    unittest.main()
