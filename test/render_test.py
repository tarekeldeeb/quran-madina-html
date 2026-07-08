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
ARABIC_LETTER = re.compile("[ء-يٱ-ۓ]")  # a token is a word only if it carries an Arabic letter;
# markers (﴿N﴾, ۝N), waqf/pause marks (ۖ ۗ ۚ …) and ornaments (۞ ۩) carry none and are not words.


def aya_word_list(aya):
    """Selectable words of an aya (whitespace-separated tokens that contain an Arabic letter)."""
    words = []
    for part in aya["r"]:
        for token in part["t"].split():
            if ARABIC_LETTER.search(token):
                words.append(token)
    return words


def collect_words(suras, sura_start, aya_start, word_end):
    """Mirror of the JS collectWordParts() word walk: reading order from (sura_start, aya_start),
    crossing sura boundaries, until at least `word_end` words have been gathered. The sura title
    (aya index 0) is uncounted decoration; the basmala (index 1) is real Quran text and counts
    like any other words (At-Tawba's blank slot naturally contributes none)."""
    words = []
    sura = sura_start
    while sura < len(suras):
        ayas = suras[sura]["ayas"]
        aya = aya_start if sura == sura_start else 0
        while aya < len(ayas):
            if aya >= 1:  # 0 is the sura-title decoration, never counted
                words.extend(aya_word_list(ayas[aya]))
                if len(words) >= word_end:
                    return words
            aya += 1
        sura += 1
    return words

class BasicRenderTest(unittest.TestCase):  # pylint: disable=too-many-public-methods
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
    with open(test_file, encoding="utf8") as _tpl_handle:
        original_template = _tpl_handle.read()  # pristine, restored in tearDownClass
    web_driver.get(test_url)
    time.sleep(10)
    with open(DEFAULT_DB, encoding="utf8") as _db_handle:
        db = json.load(_db_handle)

    @classmethod
    def tearDownClass(cls):
        """Restore the template the set_attrs/set_page helpers rewrite, and close the browser."""
        with open(cls.test_file, "w", encoding="utf8") as tpl:
            tpl.write(cls.original_template)
        cls.web_driver.quit()

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
        for key in ("sura", "aya", "words", "headless", "notitle"):  # ensure a clean page-only render
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
        for key in ("page", "sura", "aya", "words", "headless", "notitle", "quotes", "inline"):
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

    def visible_tokens(self):
        """Text of every shown word span (i.e. not hidden by a words= selection), in order.
        Includes non-word tokens like the aya-end marker, which is deliberately shown whenever
        the word it follows is visible (see appendWords)."""
        return self.web_driver.execute_script(
            "return Array.from(document.querySelectorAll('span.quran-madina-html-word'))"
            ".filter(w => !w.classList.contains('quran-madina-html-word-hidden'))"
            ".map(w => w.textContent);")

    def visible_words(self):
        """visible_tokens() restricted to real words (tokens carrying an Arabic letter), the
        unit the words= indexing counts - markers/ornaments ride along with their word and are
        excluded here so expectations can be built from aya_word_list/collect_words."""
        return [token for token in self.visible_tokens() if ARABIC_LETTER.search(token)]

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
        """words= keeps counting past the end of a sura into the next one: Al-Fatiha's last aya
        (9 words), then the basmala (4 counted words, shown as the ligature since all 4 are in
        range), then Al-Baqara's real aya 1"""
        self.set_attrs(sura=1, aya=7, words="1-14")
        expected = collect_words(self.db["suras"], 0, 8, 14)[0:14]
        # words 10-13 are the complete basmala and collapse into the ﷽ ligature token
        self.assertEqual(self.visible_words(), expected[0:9] + expected[13:14],
                         f"sura1 aya7 words=1-14 should cross into sura 2\n{self.dump_log()}")
        self.assertIn("﷽", self.visible_tokens(),
                      "the complete basmala must render as the ligature")
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

    def test_8_inline_has_popup_not_header(self):
        """An inline (single-line) verse render has no header chrome; clicking the aya opens the
        copy/translate popup instead (the lone inline copy button was replaced by the popup)"""
        self.set_attrs(sura=1, aya=1)
        self.assertEqual(self.count("quran-madina-html-line"), 1, "aya 1:1 fits one line")
        self.assertEqual(self.count("quran-madina-html-header"), 0, "inline render has no header")
        self.web_driver.execute_script(
            "document.querySelector('.quran-madina-html-001-001')"
            ".dispatchEvent(new MouseEvent('click',{bubbles:true}));")
        self.assertEqual(self.count("quran-madina-html-aya-popup.quran-madina-html-open"), 1,
                         f"clicking the aya must open its copy/translate popup\n{self.dump_log()}")

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
        # Inline words selection: no header to begin with, words unchanged.
        self.set_attrs(sura=1, aya=1, words="1:2", headless=True)
        self.assertEqual(self.count("quran-madina-html-header"), 0, "no header when headless")
        self.assertEqual(self.visible_words(), collect_words(self.db["suras"], 0, 2, 2)[0:2],
                         "selected words are unchanged by headless")
        # Multiline words selection: header only.
        self.set_attrs(sura=1, aya=1, words="3-10", headless=True)
        self.assertEqual(self.count("quran-madina-html-header"), 0, "headless drops multiline header")
        self.assertEqual(self.visible_words(), collect_words(self.db["suras"], 0, 2, 10)[2:10],
                         "selected words are unchanged by headless")

    def test_11_headless_false_keeps_chrome(self):
        """headless=False (and the default) leave the multiline header in place"""
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
        """An over-long words= span is capped at 500 counted words. A complete basmala inside
        the span (here Al-Baqara's, crossed into from Al-Fatiha) renders as one ligature token
        that still accounts for its 4 counted words."""
        self.set_attrs(sura=1, aya=1, words="1-1000")
        ligatures = self.visible_tokens().count("﷽")
        self.assertEqual(ligatures, 1, f"the span crosses one basmala\n{self.dump_log()}")
        self.assertEqual(len(self.visible_words()) + 4 * ligatures, 500,
                         f"selection capped at 500\n{self.dump_log()}")

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
        """Copy-to-clipboard carries only the visible words, not the ones hidden by words=.
        inline="no" forces the multiline layout so the header (the frame-level copy affordance,
        now that the lone inline copy button is gone) is present to click."""
        self.set_attrs(sura=1, aya=1, words="1:2", inline="no")
        self.web_driver.execute_script(
            "window.__copied=null;window.alert=function(){};"
            "navigator.clipboard.writeText=function(t){window.__copied=t;return Promise.resolve();};")
        self.web_driver.execute_script(
            "document.querySelector('quran-madina-html-header svg')."
            "dispatchEvent(new MouseEvent('click',{bubbles:true}));")
        copied = self.web_driver.execute_script("return window.__copied;")
        shown = collect_words(self.db["suras"], 0, 2, 3)
        self.assertIsNotNone(copied, f"copy handler should have run\n{self.dump_log()}")
        self.assertIn(shown[0], copied)
        self.assertIn(shown[1], copied)
        self.assertNotIn(shown[2], copied, "a hidden word must not be copied")
        self.assertIn(self.db["suras"][0]["name"], copied, "sura name is appended to the copy")

    def test_16_pause_marks_not_counted_as_words(self):
        """Waqf/pause marks (e.g. the two ۛ in Al-Baqara 2) are never counted or shown as words"""
        self.set_attrs(sura=2, aya=2, words="1-7")
        expected = collect_words(self.db["suras"], 1, 3, 7)[0:7]
        self.assertEqual(len(expected), 7, "Al-Baqara aya 2 has 7 real words")
        shown = self.visible_words()
        self.assertEqual(shown, expected,
                         f"words=1-7 should be the 7 real words, not split by pause marks\n{self.dump_log()}")
        self.assertNotIn("ۛ", self.visible_tokens(),
                         "a bare pause mark must never be its own visible token")

    def test_17_basmala_counted_and_ligature_when_complete(self):
        """Crossing into a new sura, the basmala counts as 4 real words; when all 4 fall inside
        the selection they render as the traditional ﷽ ligature, not as individual tokens —
        and the ligature still occupies all 4 word indices for anything that follows"""
        fatiha_last = aya_word_list(self.db["suras"][0]["ayas"][8])  # Al-Fatiha aya 7
        basmala = aya_word_list(self.db["suras"][1]["ayas"][1])  # Al-Baqara's basmala slot
        self.assertEqual(len(basmala), 4, "the basmala decoration must carry 4 real words")
        end = len(fatiha_last) + 4
        self.set_attrs(sura=1, aya=7, words=f"1-{end}")
        self.assertEqual(self.visible_words(), fatiha_last,
                         f"only Al-Fatiha's words render as word tokens\n{self.dump_log()}")
        tokens = self.visible_tokens()
        self.assertIn("﷽", tokens, "the complete basmala must render as the ligature")
        for word in basmala:
            self.assertNotIn(word, tokens, "no individual basmala token when complete")
        # One more word proves the ligature consumed word indices 10-13: word 14 is Al-Baqara's
        baqara_first = aya_word_list(self.db["suras"][1]["ayas"][2])[0]
        self.set_attrs(sura=1, aya=7, words=f"1-{end + 1}")
        self.assertEqual(self.visible_words(), fatiha_last + [baqara_first],
                         f"the ligature must still occupy 4 word indices\n{self.dump_log()}")

    def test_18_partial_basmala_renders_words(self):
        """A words= range covering only 1-3 of the basmala's 4 words renders those individual
        word spans (no ligature: the selection must stay visibly exact)"""
        n = len(aya_word_list(self.db["suras"][0]["ayas"][8]))
        basmala = aya_word_list(self.db["suras"][1]["ayas"][1])
        self.set_attrs(sura=1, aya=7, words=f"{n + 2}-{n + 3}")
        self.assertEqual(self.visible_words(), basmala[1:3],
                         f"words {n + 2}-{n + 3} must be basmala words 2-3\n{self.dump_log()}")
        self.assertNotIn("﷽", self.visible_tokens(),
                         "a partial basmala must not collapse into the ligature")

    def test_19_notitle_hides_title_line(self):
        """notitle drops the crossed-into sura's title line; words and basmala are unchanged"""
        self.set_attrs(sura=1, aya=7, words="1-13")
        self.assertEqual(self.count(".quran-madina-html-sura-start"), 1,
                         "title decoration shows by default")
        lines_with_title = self.count("quran-madina-html-line")
        shown_with_title = self.visible_words()
        self.set_attrs(sura=1, aya=7, words="1-13", notitle=True)
        self.assertEqual(self.count(".quran-madina-html-sura-start"), 0,
                         f"notitle must drop the title decoration\n{self.dump_log()}")
        self.assertEqual(self.count("quran-madina-html-line"), lines_with_title - 1,
                         "the title's dedicated line is removed, not just blanked")
        self.assertEqual(self.visible_words(), shown_with_title,
                         "notitle must not change the selected words")
        rendered = self.web_driver.execute_script(
            "return document.querySelector('quran-madina-html').textContent;")
        self.assertNotIn(self.db["suras"][1]["name"], rendered,
                         "the crossed-into sura name must not appear anywhere")

    def test_20_tawba_boundary_has_no_basmala(self):
        """Crossing into At-Tawba (no basmala in the real text) inserts no basmala words: the
        first counted word after Al-Anfal's last is At-Tawba's real aya 1"""
        anfal_last = aya_word_list(self.db["suras"][7]["ayas"][76])  # Al-Anfal aya 75 (its last)
        tawba_first = aya_word_list(self.db["suras"][8]["ayas"][2])  # At-Tawba real aya 1
        basmala = aya_word_list(self.db["suras"][1]["ayas"][1])
        n = len(anfal_last)
        self.set_attrs(sura=8, aya=75, words=f"1-{n + 2}")
        expected = collect_words(self.db["suras"], 7, 76, n + 2)[0:n + 2]
        self.assertEqual(expected[n:], tawba_first[0:2],
                         "the words after Al-Anfal must be At-Tawba aya 1 directly")
        shown = self.visible_words()
        self.assertEqual(shown, expected, f"no phantom basmala words\n{self.dump_log()}")
        for word in basmala:
            self.assertNotIn(word, shown[n:], "no basmala word may appear after the boundary")
        self.assertNotIn("﷽", self.visible_tokens(), "no basmala ligature either")
        self.assertEqual(self.count(".quran-madina-html-sura-start"), 1,
                         "At-Tawba's title decoration still renders")

    def test_21_basmala_only_selection_is_ligature(self):
        """A selection that is exactly the 4 basmala words shows only the ligature"""
        n = len(aya_word_list(self.db["suras"][0]["ayas"][8]))
        self.set_attrs(sura=1, aya=7, words=f"{n + 1}-{n + 4}")
        self.assertEqual(self.visible_words(), [],
                         f"no individual word tokens expected\n{self.dump_log()}")
        self.assertEqual(self.visible_tokens(), ["﷽"],
                         "exactly the ligature must be visible")

    def test_22_page_render_shows_basmala_ligature(self):
        """A full page render always shows a complete basmala line, so it gets the ligature
        (never the DB's 4 word tokens)"""
        self.set_page(2)
        text = self.web_driver.execute_script(
            "return document.querySelector('quran-madina-html').textContent;")
        self.assertIn("﷽", text, f"page 2 must open with the basmala ligature\n{self.dump_log()}")
        basmala = aya_word_list(self.db["suras"][1]["ayas"][1])
        self.assertNotIn(basmala[0], text, "the basmala's first token must not render on a page")

if __name__ == '__main__':
    unittest.main()
