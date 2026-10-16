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
# default DB (v2, layout 1441H). Drive the words= expectations from that same JSON so the
# assertions stay in sync with the data. In v2 every shown word is its own span (with its stretch
# features) and the basmala always shows as its 4 words: there is no ﷽ ligature.
DEFAULT_DB = os.path.join("assets", "db", "v2", "Madina-1441H.json")
ARABIC_LETTER = re.compile("[ء-يٱ-ۓ]")  # a token is a word only if it carries an Arabic letter;
# Characters that ride on the letter before them (the runtime's LETTER_RIDER)
LETTER_RIDER = re.compile("[\u0300-\u036F\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC"
                          "\u06DF-\u06E8\u06EA-\u06ED\u08D3-\u08FF\u200C\u200D\u0640]")


def letters_of(word):
    """A word split into letters the way letters= counts them: base character + its riders"""
    out = []
    for ch in word:
        if out and LETTER_RIDER.match(ch):
            out[-1] += ch
        else:
            out.append(ch)
    return out
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
    crossing sura boundaries — and wrapping around from An-Nas to Al-Fatiha — until at least
    `word_end` words have been gathered. Sura titles are uncounted decoration (slot 0 everywhere,
    plus Al-Fatiha's slot 1); the basmala is real Quran text and counts like any other words
    (At-Tawba's blank slot naturally contributes none). A walk anchored at a sura's first real
    aya (internal index 2) rewinds to its basmala slot so the anchor sura's own basmala is
    counted too — Al-Fatiha exempt (its slot 1 is its title)."""
    words = []
    anchor_begin = 1 if (aya_start == 2 and sura_start > 0) else aya_start
    for si in range(len(suras)):
        sura = (sura_start + si) % len(suras)
        ayas = suras[sura]["ayas"]
        aya = anchor_begin if si == 0 else 0
        while aya < len(ayas):
            if aya >= (2 if sura == 0 else 1):  # skip title slots (0; Al-Fatiha's is slot 1)
                words.extend(aya_word_list(ayas[aya]))
                if len(words) >= word_end:
                    return words
            aya += 1
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
        for key in ("sura", "aya", "words", "highlight", "error", "headless", "notitle"):
            # ensure a clean page-only render
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
        for key in ("page", "sura", "aya", "words", "highlight", "error", "headless", "notitle",
                    "quotes", "inline", "letters"):
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
            # v2 renders the invisible context around a selection (spacers) as word spans too
            ".filter(w => getComputedStyle(w).visibility !== 'hidden')"
            ".map(w => w.textContent);")

    def visible_words(self):
        """visible_tokens() restricted to real words (tokens carrying an Arabic letter), the
        unit the words= indexing counts - markers/ornaments ride along with their word and are
        excluded here so expectations can be built from aya_word_list/collect_words."""
        return [token for token in self.visible_tokens() if ARABIC_LETTER.search(token)]

    def visible_word_marks(self):
        """visible_words(), but for every visible real word: whether it also carries the
        highlight/error classes (see appendWords). A word hidden by a words= selection is
        excluded here just like in visible_words()/visible_tokens()."""
        raw = self.web_driver.execute_script(
            "return Array.from(document.querySelectorAll('span.quran-madina-html-word'))"
            ".filter(w => !w.classList.contains('quran-madina-html-word-hidden'))"
            ".filter(w => getComputedStyle(w).visibility !== 'hidden').map("
            "function(w){return {text:w.textContent,"
            "highlight:w.classList.contains('quran-madina-html-word-highlight'),"
            "error:w.classList.contains('quran-madina-html-word-error')};});")
        return [m for m in raw if ARABIC_LETTER.search(m["text"])]

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
        (9 words), then the basmala (4 counted words, shown as words), then Al-Baqara's real
        aya 1"""
        self.set_attrs(sura=1, aya=7, words="1-14")
        expected = collect_words(self.db["suras"], 0, 8, 14)[0:14]
        self.assertEqual(self.visible_words(), expected,
                         f"sura1 aya7 words=1-14 should cross into sura 2\n{self.dump_log()}")
        self.assertNotIn("﷽", self.visible_tokens(), "v2 shows the basmala as its words")
        # The crossed-into sura (Al-Baqara) renders its first aya and its name decoration line
        self.assertGreaterEqual(self.count(".quran-madina-html-002-001"), 1,
                                "Al-Baqara aya 1 should be rendered after the boundary")
        self.assertEqual(self.count(".quran-madina-html-sura-start"), 1,
                         "the crossed-into sura name carries the sura-start decoration")

    def test_7_words_ignored_with_page(self):
        """words= is ignored when a full page is requested: nothing is hidden"""
        self.set_attrs(page=5, words="1:2")
        self.assertEqual(self.count("span.quran-madina-html-word-hidden"), 0,
                         "a page render must not hide words")
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
        """A reversed or zero words= range is rejected; the aya renders normally (all words)"""
        aya1 = aya_word_list(self.db["suras"][0]["ayas"][2])
        for bad in ("3-1", "0", "0-2"):
            self.set_attrs(sura=1, aya=1, words=bad)
            self.assertEqual(self.count("span.quran-madina-html-word-hidden"), 0,
                             f"words={bad} must not hide words\n{self.dump_log()}")
            self.assertEqual(self.visible_words(), aya1,
                             f"words={bad} should still render the whole aya")

    def test_13_words_capped_at_500(self):
        """An over-long words= span is capped at 500 counted words (here crossing Al-Baqara's
        basmala, whose 4 words count and show)"""
        self.set_attrs(sura=1, aya=1, words="1-1000")
        self.assertEqual(len(self.visible_words()), 500,
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

    def test_17_basmala_counted_as_four_words(self):
        """Crossing into a new sura, the basmala counts as 4 real words and shows them; the next
        word after them is Al-Baqara's first"""
        fatiha_last = aya_word_list(self.db["suras"][0]["ayas"][8])  # Al-Fatiha aya 7
        basmala = aya_word_list(self.db["suras"][1]["ayas"][1])  # Al-Baqara's basmala slot
        self.assertEqual(len(basmala), 4, "the basmala decoration must carry 4 real words")
        end = len(fatiha_last) + 4
        self.set_attrs(sura=1, aya=7, words=f"1-{end}")
        self.assertEqual(self.visible_words(), fatiha_last + basmala,
                         f"Al-Fatiha's last aya, then the 4 basmala words\n{self.dump_log()}")
        baqara_first = aya_word_list(self.db["suras"][1]["ayas"][2])[0]
        self.set_attrs(sura=1, aya=7, words=f"1-{end + 1}")
        self.assertEqual(self.visible_words(), fatiha_last + basmala + [baqara_first],
                         f"the basmala occupies 4 word indices\n{self.dump_log()}")

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

    def test_19_notitle_hides_name_keeps_decorated_line(self):
        """notitle keeps the crossed-into sura's title line and its decorative frame (the
        sura-start class the border SVG hangs off) but hides the sura name text itself"""
        self.set_attrs(sura=1, aya=7, words="1-13")
        self.assertEqual(self.count(".quran-madina-html-sura-start"), 1,
                         "title decoration shows by default")
        lines_with_title = self.count("quran-madina-html-line")
        shown_with_title = self.visible_words()
        name = self.db["suras"][1]["name"]
        self.set_attrs(sura=1, aya=7, words="1-13", notitle=True)
        self.assertEqual(self.count(".quran-madina-html-sura-start"), 1,
                         f"the decorated title line must survive notitle\n{self.dump_log()}")
        self.assertEqual(self.count("quran-madina-html-line"), lines_with_title,
                         "notitle must not change the line count")
        self.assertEqual(self.visible_words(), shown_with_title,
                         "notitle must not change the selected words")
        # The name text is still laid out (it sizes/centers the line) but invisible.
        title_probe = self.web_driver.execute_script(
            "var el = document.querySelector('.quran-madina-html-sura-start');"
            "return {text: el.textContent, visible: el.innerText.trim()};")
        self.assertIn(name, title_probe["text"], "the name still occupies the line's layout")
        self.assertEqual(title_probe["visible"], "", "the name must not be visible")

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

    def test_21_basmala_only_selection(self):
        """A selection that is exactly the 4 basmala words shows exactly those words"""
        n = len(aya_word_list(self.db["suras"][0]["ayas"][8]))
        basmala = aya_word_list(self.db["suras"][1]["ayas"][1])
        self.set_attrs(sura=1, aya=7, words=f"{n + 1}-{n + 4}")
        self.assertEqual(self.visible_words(), basmala,
                         f"exactly the basmala words\n{self.dump_log()}")

    def test_22_anchor_sura_basmala_counted(self):
        """A words= walk anchored at a sura's first real aya counts that sura's OWN basmala:
        words 1-4 are the basmala and word 5 is the first word of real aya 1"""
        basmala = aya_word_list(self.db["suras"][107]["ayas"][1])  # Al-Kawthar's basmala slot
        aya1 = aya_word_list(self.db["suras"][107]["ayas"][2])     # Al-Kawthar real aya 1
        self.assertEqual(len(basmala), 4, "the basmala slot must carry 4 real words")
        self.set_attrs(sura=108, aya=1, words="1-5")
        self.assertEqual(self.visible_words(), basmala + aya1[0:1],
                         f"word 5 of an aya-1 anchor must be the aya's first word\n{self.dump_log()}")

    def test_23_anchor_partial_basmala_regression(self):
        """Anchored at aya 1, words=4-6 are basmala word 4 + the aya's first two words. This is
        the quranquiz off-by-4 regression: quranquiz's flat Tanzil word offsets count the anchor
        sura's basmala, so before the anchor rewind these indices rendered 4 words late
        (words 4-6 of Al-Kawthar showed aya 2 instead of الرحيم انا اعطينك)"""
        basmala = aya_word_list(self.db["suras"][107]["ayas"][1])
        aya1 = aya_word_list(self.db["suras"][107]["ayas"][2])
        self.set_attrs(sura=108, aya=1, words="4-6")
        self.assertEqual(self.visible_words(), basmala[3:4] + aya1[0:2],
                         f"words 4-6 must start at the anchor basmala's 4th word\n{self.dump_log()}")
        self.assertNotIn("﷽", self.visible_tokens(),
                         "a partial anchor basmala must not collapse into the ligature")

    def test_24_anchor_past_basmala(self):
        """An aya-1 anchored selection that starts past the basmala shows exactly the real aya's
        words (the leading basmala line is dropped, its 4 words carried as counter offset)"""
        aya1 = aya_word_list(self.db["suras"][107]["ayas"][2])  # 3 words: انا اعطينك الكوثر
        self.set_attrs(sura=108, aya=1, words=f"5-{4 + len(aya1)}")
        self.assertEqual(self.visible_words(), aya1,
                         f"words 5.. of an aya-1 anchor must be real aya 1\n{self.dump_log()}")

    def test_25_anchor_tawba_and_fatiha_exempt(self):
        """At-Tawba's blank basmala slot adds no words to an aya-1 anchor, and Al-Fatiha's
        anchor is exempt from the rewind (its slot 1 is its title; its basmala is real aya 1)"""
        tawba_first = aya_word_list(self.db["suras"][8]["ayas"][2])  # At-Tawba real aya 1
        self.set_attrs(sura=9, aya=1, words="1-2")
        self.assertEqual(self.visible_words(), tawba_first[0:2],
                         f"At-Tawba aya-1 anchor: word 1 is its real aya 1\n{self.dump_log()}")
        fatiha_basmala = aya_word_list(self.db["suras"][0]["ayas"][2])  # Fatiha's real aya 1
        self.set_attrs(sura=1, aya=1, words="1-2")
        self.assertEqual(self.visible_words(), fatiha_basmala[0:2],
                         f"Al-Fatiha aya-1 anchor: word 1 is بسم, not its title\n{self.dump_log()}")

    def test_26_popup_escapes_transformed_ancestor(self):
        """The aya popup must land next to the clicked aya even when the host tag sits under a
        CSS-transformed ancestor (e.g. an app's card-flip rotateY): a transformed ancestor
        becomes the containing block of position:fixed children, re-basing their viewport
        coordinates and clipping them under app chrome — so the popup lives on document.body"""
        self.set_attrs(sura=1, aya=1)
        self.web_driver.execute_script(
            "var tag=document.querySelector('quran-madina-html');"
            "var wrap=document.createElement('div');"
            "wrap.style.transform='rotateY(360deg)';wrap.style.marginTop='150px';"
            "tag.parentNode.insertBefore(wrap,tag);wrap.appendChild(tag);"
            "document.querySelector('.quran-madina-html-001-001')"
            ".dispatchEvent(new MouseEvent('click',{bubbles:true}));")
        probe = self.web_driver.execute_script(
            "var p=document.querySelector('quran-madina-html-aya-popup.quran-madina-html-open');"
            "if(!p) return null;"
            "var a=document.querySelector('.quran-madina-html-001-001');"
            "return {onBody:p.parentNode===document.body,"
            "top:p.getBoundingClientRect().top,left:p.getBoundingClientRect().left,"
            "ayaTop:a.getBoundingClientRect().top,ayaBottom:a.getBoundingClientRect().bottom,"
            "ayaLeft:a.getBoundingClientRect().left};")
        self.assertIsNotNone(probe, f"the aya popup must open\n{self.dump_log()}")
        self.assertTrue(probe["onBody"], "the popup must be a direct child of document.body")
        # positionAyaPopup hugs the aya: ~40px above it, or 6px below if there is no room above.
        self.assertTrue(probe["ayaTop"] - 60 <= probe["top"] <= probe["ayaBottom"] + 20,
                        f"popup top {probe['top']} must hug the aya "
                        f"({probe['ayaTop']}..{probe['ayaBottom']})\n{self.dump_log()}")
        self.assertLess(abs(probe["left"] - max(4, probe["ayaLeft"])), 10,
                        "popup left must align with the aya's left edge")

    def test_27_words_wrap_around_to_fatiha(self):
        """A words= walk anchored at the end of An-Nas wraps around to Al-Fatiha: after An-Nas's
        last aya come Al-Fatiha's basmala (its real aya 1 — 4 counted words, ligature when
        complete) and then الحمد. Al-Fatiha's title (slot 1) stays uncounted decoration, and
        notitle hides its name text like any crossed-into title"""
        nas_last = aya_word_list(self.db["suras"][113]["ayas"][7])   # An-Nas aya 6
        fatiha_basmala = aya_word_list(self.db["suras"][0]["ayas"][2])  # Fatiha real aya 1
        fatiha_aya2 = aya_word_list(self.db["suras"][0]["ayas"][3])     # الحمد لله رب العالمين
        fatiha_name = self.db["suras"][0]["name"]
        n = len(nas_last)
        self.assertEqual(len(fatiha_basmala), 4, "Al-Fatiha's aya 1 is the 4-word basmala")
        expected = collect_words(self.db["suras"], 113, 7, n + 5)[0:n + 5]
        self.assertEqual(expected, nas_last + fatiha_basmala + fatiha_aya2[0:1],
                         "the word walk mirror must wrap An-Nas → Al-Fatiha")
        self.set_attrs(sura=114, aya=6, words=f"1-{n + 5}")
        # Al-Fatiha's basmala is its REAL aya 1 (it carries the ﴿١﴾ marker in the Mushaf), so
        # unlike other suras' basmala slots it renders as word tokens, never the ligature.
        self.assertEqual(self.visible_words(), nas_last + fatiha_basmala + fatiha_aya2[0:1],
                         f"words must continue into Al-Fatiha after An-Nas\n{self.dump_log()}")
        self.assertNotIn("﷽", self.visible_tokens(),
                         "Al-Fatiha's basmala is a real aya, not an ornamental ligature")
        self.assertNotIn(fatiha_name, self.visible_words(),
                         "Al-Fatiha's title must stay uncounted decoration")
        # notitle hides the wrapped-into Fatiha's name text (slot 1, unlike other suras' slot 0).
        probe = self.web_driver.execute_script(
            "var el=document.querySelector('.quran-madina-html-001-000');"
            "return el ? {text:el.textContent, visible:el.innerText.trim()} : null;")
        self.assertIsNotNone(probe, "Al-Fatiha's title line must be rendered")
        # Its title line carries the sura-start decoration despite living at slot 1.
        self.assertEqual(self.count(".quran-madina-html-001-000.quran-madina-html-sura-start"), 1,
                         "Al-Fatiha's title must carry the decorated sura-start frame")
        self.set_attrs(sura=114, aya=6, words=f"1-{n + 5}", notitle=True)
        self.assertEqual(self.count(".quran-madina-html-001-000.quran-madina-html-sura-start"), 1,
                         f"the decorated frame must survive notitle\n{self.dump_log()}")
        probe = self.web_driver.execute_script(
            "var el=document.querySelector('.quran-madina-html-001-000');"
            "return el ? {text:el.textContent, visible:el.innerText.trim()} : null;")
        self.assertIsNotNone(probe, f"the title line must survive notitle\n{self.dump_log()}")
        self.assertIn(fatiha_name, probe["text"], "the name still occupies the line's layout")
        self.assertEqual(probe["visible"], "", "the name must not be visible under notitle")

    def test_28_page_render_shows_basmala_words(self):
        """A full page render shows the basmala line as its 4 words, like the print"""
        self.set_page(2)
        basmala = aya_word_list(self.db["suras"][1]["ayas"][1])
        self.assertEqual(self.visible_words()[0:4], basmala,
                         f"page 2 must open with the basmala\n{self.dump_log()}")
        self.assertNotIn("﷽", self.visible_tokens(), "no ligature in v2")

    def test_29_highlight_marks_words_in_words_selection(self):
        """highlight= marks a sub-range of words within an existing words= selection"""
        self.set_attrs(sura=1, aya=1, words="1-5", highlight="2-3")
        expected = collect_words(self.db["suras"], 0, 2, 5)[0:5]
        marks = self.visible_word_marks()
        self.assertEqual([m["text"] for m in marks], expected,
                         f"words=1-5 should show exactly those 5 words\n{self.dump_log()}")
        self.assertEqual([m["highlight"] for m in marks], [False, True, True, False, False],
                         f"only words 2-3 should carry the highlight class\n{self.dump_log()}")
        self.assertFalse(any(m["error"] for m in marks), "no error class expected")

    def test_30_error_marks_words_in_words_selection(self):
        """error= marks a sub-range of words within an existing words= selection"""
        self.set_attrs(sura=1, aya=1, words="1-5", error="4-5")
        marks = self.visible_word_marks()
        self.assertEqual([m["error"] for m in marks], [False, False, False, True, True],
                         f"only words 4-5 should carry the error class\n{self.dump_log()}")
        self.assertFalse(any(m["highlight"] for m in marks), "no highlight class expected")

    def test_31_highlight_error_overlap_error_wins(self):
        """When highlight= and error= overlap on a word, error wins for that word"""
        self.set_attrs(sura=1, aya=1, words="1-5", highlight="2-4", error="3-4")
        marks = self.visible_word_marks()
        self.assertEqual([m["highlight"] for m in marks], [False, True, False, False, False],
                         f"only word 2 should stay highlighted\n{self.dump_log()}")
        self.assertEqual([m["error"] for m in marks], [False, False, True, True, False],
                         f"words 3-4 should be error (overlap with highlight)\n{self.dump_log()}")

    def test_32_highlight_error_invalid_range_ignored(self):
        """A malformed (reversed/zero) or out-of-bounds highlight=/error= is ignored (warning
        only); the words= selection itself must still render normally"""
        for bad in ("3-1", "0", "6-8"):  # reversed/zero (malformed), 6-8 out of the 5 shown
            self.set_attrs(sura=1, aya=1, words="1-5", highlight=bad, error=bad)
            marks = self.visible_word_marks()
            self.assertEqual(len(marks), 5, f"highlight/error={bad} must not affect words=1-5")
            self.assertFalse(any(m["highlight"] or m["error"] for m in marks),
                             f"highlight/error={bad} should be ignored\n{self.dump_log()}")

    def test_33_highlight_error_plain_verse_no_words(self):
        """highlight=/error= work on a plain verse render with no words= selection at all"""
        self.set_attrs(sura=1, aya=1, highlight="2-2", error="3-4")
        marks = self.visible_word_marks()
        expected = aya_word_list(self.db["suras"][0]["ayas"][2])  # Al-Fatiha aya 1: 4 words
        self.assertEqual([m["text"] for m in marks], expected, "plain verse render shows every word")
        self.assertEqual([m["highlight"] for m in marks], [False, True, False, False],
                         f"only word 2 should be highlighted\n{self.dump_log()}")
        self.assertEqual([m["error"] for m in marks], [False, False, True, True],
                         f"words 3-4 should be error\n{self.dump_log()}")

    def test_34_highlight_out_of_range_plain_verse_ignored(self):
        """A highlight= range beyond a plain verse's word count is ignored: nothing is marked
        and the verse renders normally"""
        self.set_attrs(sura=1, aya=1, highlight="5-6")
        self.assertEqual(self.count("span.quran-madina-html-word-highlight"), 0,
                         "an out-of-range highlight must mark nothing")
        self.assertEqual(self.visible_words(), aya_word_list(self.db["suras"][0]["ayas"][2]),
                         f"the verse must still render its text\n{self.dump_log()}")

    def test_35_page_mode_highlight_anchors_first_aya(self):
        """On a page render, highlight= counts from the page's first (real) aya - here
        Al-Baqara's basmala, which opens page 2 - and a partial overlap forces individual
        tokens instead of the ligature"""
        self.set_attrs(page=2, highlight="1-2")
        self.assertNotIn("﷽", self.visible_tokens(),
                         "a highlight cutting into only part of the basmala must not use the ligature")
        marks = self.visible_word_marks()
        basmala = aya_word_list(self.db["suras"][1]["ayas"][1])
        self.assertEqual([m["text"] for m in marks[0:4]], basmala,
                         "page 2 opens with Al-Baqara's basmala tokens")
        self.assertEqual([m["highlight"] for m in marks[0:4]], [True, True, False, False],
                         f"only the first two basmala words should be highlighted\n{self.dump_log()}")

    def test_36_page_mode_highlight_full_basmala(self):
        """A highlight= covering the complete basmala on a page render marks its 4 words"""
        self.set_attrs(page=2, highlight="1-4")
        marks = self.visible_word_marks()
        self.assertEqual([m["highlight"] for m in marks[0:5]], [True, True, True, True, False],
                         f"exactly the 4 basmala words are highlighted\n{self.dump_log()}")

    def test_37_words_highlight_partial_basmala_forces_tokens(self):
        """Within a words= selection that fully covers the basmala, a highlight cutting into
        only some of its words forces the individual tokens instead of the ligature"""
        fatiha_last = aya_word_list(self.db["suras"][0]["ayas"][8])
        basmala = aya_word_list(self.db["suras"][1]["ayas"][1])
        end = len(fatiha_last) + 4
        start_word = len(fatiha_last) + 1
        self.set_attrs(sura=1, aya=7, words=f"1-{end}", highlight=f"{start_word}-{start_word + 1}")
        tokens = self.visible_tokens()
        self.assertNotIn("﷽", tokens, "partial highlight must force individual basmala tokens")
        self.assertIn(basmala[0], tokens)
        self.assertIn(basmala[1], tokens)

    def test_38_words_highlight_full_basmala(self):
        """A highlight= covering the complete basmala within a words= selection marks its 4
        words"""
        fatiha_last = aya_word_list(self.db["suras"][0]["ayas"][8])
        end = len(fatiha_last) + 4
        start_word = len(fatiha_last) + 1
        self.set_attrs(sura=1, aya=7, words=f"1-{end}", highlight=f"{start_word}-{start_word + 3}")
        marks = self.visible_word_marks()
        self.assertEqual([m["highlight"] for m in marks],
                         [False] * len(fatiha_last) + [True] * 4,
                         f"exactly the basmala words are highlighted\n{self.dump_log()}")

    # ---- letters= -------------------------------------------------------------------------

    def letter_marks(self):
        """[(word number, letter text, computed colour)] of every marked letter, in order"""
        return [tuple(x) for x in self.web_driver.execute_script(
            "return Array.from(document.querySelectorAll('.quran-madina-html-letter')).map("
            "s => [parseInt(s.parentElement.getAttribute('data-qmh-w'), 10), s.textContent,"
            " getComputedStyle(s).color]);")]

    def word_geometry(self):
        """{word number: (left, top, width, height)} relative to the tag, for the shown words"""
        return {int(k): tuple(v) for k, v in self.web_driver.execute_script(
            "var t = document.querySelector('quran-madina-html').getBoundingClientRect(), out = {};"
            "document.querySelectorAll('[data-qmh-w]').forEach(function(w){"
            " var r = w.getBoundingClientRect();"
            " out[w.getAttribute('data-qmh-w')] ="
            "  [r.left - t.left, r.top - t.top, r.width, r.height];});"
            "return out;").items()}

    def test_39_letters_marks_letters_with_colours(self):
        """letters= wraps the chosen letters of the chosen words; crimson by default, a named
        palette colour or any CSS colour per group"""
        words = aya_word_list(self.db["suras"][0]["ayas"][3])          # Al-Fatiha 2
        self.set_attrs(sura=1, aya=2, letters="1:3, 3:1 emerald, 4:2-3 #123456")
        marks = self.letter_marks()
        self.assertEqual([(w, t) for w, t, _ in marks],
                         [(1, letters_of(words[0])[2]), (3, letters_of(words[2])[0]),
                          (4, letters_of(words[3])[1]), (4, letters_of(words[3])[2])],
                         f"wrong letters marked\n{self.dump_log()}")
        self.assertEqual([c for _, _, c in marks],
                         ["rgb(163, 38, 58)", "rgb(15, 107, 79)",
                          "rgb(18, 52, 86)", "rgb(18, 52, 86)"])

    def test_40_letters_do_not_move_anything(self):
        """Marking letters changes colour only: every word keeps its exact place and size"""
        self.set_attrs(sura=1, aya="2-4", highlight="1")      # numbered words, no letters
        plain = self.word_geometry()
        self.set_attrs(sura=1, aya="2-4", highlight="1", letters="1:3, 4:3+5, 6:2-4")
        lettered = self.word_geometry()
        self.assertEqual(len(self.letter_marks()), 6)
        self.assertEqual(sorted(plain), sorted(lettered))
        for k, box in plain.items():
            for a, b in zip(box, lettered[k]):
                self.assertAlmostEqual(a, b, delta=0.5,
                                       msg=f"word {k} moved: {box} -> {lettered[k]}")

    def test_41_letters_inside_highlight_and_error(self):
        """letters= combines with highlight=/error= on the same words"""
        self.set_attrs(sura=1, aya="2-4", highlight="1-2", error="4", letters="1:3, 4:3")
        cls = self.web_driver.execute_script(
            "return Array.from(document.querySelectorAll('.quran-madina-html-letter'))"
            ".map(s => s.parentElement.className);")
        self.assertIn("quran-madina-html-word-highlight", cls[0])
        self.assertIn("quran-madina-html-word-error", cls[1])

    def test_42_letters_follow_words_and_page_counting(self):
        """Word numbers count like highlight=: from the words= start, and from a page's first
        aya (Al-Baqara's basmala on page 2)"""
        words = aya_word_list(self.db["suras"][0]["ayas"][2])          # Al-Fatiha 1
        self.set_attrs(sura=1, aya=1, words="2:3", letters="2:1")
        self.assertEqual([(w, t) for w, t, _ in self.letter_marks()],
                         [(2, letters_of(words[1])[0])])
        basmala = aya_word_list(self.db["suras"][1]["ayas"][1])
        self.set_attrs(page=2, letters="1:1")
        self.assertEqual([(w, t) for w, t, _ in self.letter_marks()],
                         [(1, letters_of(basmala[0])[0])])

    def test_43_letters_malformed_ignored(self):
        """A malformed letters= marks nothing and the verse renders as usual"""
        self.set_attrs(sura=1, aya=1, letters="abc")
        self.assertEqual(self.letter_marks(), [])
        self.assertEqual(self.visible_words(), aya_word_list(self.db["suras"][0]["ayas"][2]))


class FontSizeTest(unittest.TestCase):
    """v2 sizes everything in em: any data-font-size gives the same layout, scaled. The tag is
    line_width (em) x size wide, and each justified line is its row's width (w) x size."""

    test_file = os.path.join("template", "render_test.html")
    test_url = "http://localhost:8000/" + test_file
    PAGE = 25  # the template's default page: deep inside Al-Baqara, all 15 lines justified

    @classmethod
    def setUpClass(cls):
        chrome_options = Options()
        for option in ["--headless", "--disable-gpu", "--ignore-certificate-errors",
                       "--disable-extensions", "--no-sandbox", "--disable-dev-shm-usage"]:
            chrome_options.add_argument(option)
        cls.web_driver = webdriver.Chrome(options=chrome_options)
        with open(cls.test_file, encoding="utf8") as tpl:
            cls.original_template = tpl.read()
        with open(DEFAULT_DB, encoding="utf8") as db:
            cls.db = json.load(db)

    @classmethod
    def tearDownClass(cls):
        """Restore the template and close the browser."""
        with open(cls.test_file, "w", encoding="utf8") as tpl:
            tpl.write(cls.original_template)
        cls.web_driver.quit()

    def load_with_font_size(self, size):
        """Rewrite the template's script tag with data-font-size and load page PAGE."""
        soup = BeautifulSoup(self.original_template, 'html.parser')
        soup.find("script")["data-font-size"] = str(size)  # type: ignore
        soup.find("quran-madina-html")["page"] = str(self.PAGE)  # type: ignore
        with open(self.test_file, "w", encoding="utf8") as tpl:
            tpl.write(str(soup))
        self.web_driver.get(self.test_url)
        WebDriverWait(self.web_driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "quran-madina-html-line")))
        time.sleep(1)

    def assert_geometry(self, size):
        """Tag and line widths at `size`px, from the DB's em values."""
        probe = self.web_driver.execute_script(
            "var t=document.querySelector('quran-madina-html');"
            "return {width:t.style.width, fontSize:getComputedStyle(t).fontSize,"
            " lines:Array.from(t.querySelectorAll('quran-madina-html-line')).map("
            "function(l){return l.offsetWidth;})};")
        self.assertAlmostEqual(float(probe["width"].rstrip("px")), self.db["line_width"] * size + 10,
                               delta=0.01, msg=f"@{size}px the page width must be line_width*size+10")
        self.assertEqual(probe["fontSize"], f"{size}px")
        rows = self.db["lines"][self.PAGE - 1]
        self.assertEqual(len(probe["lines"]), len(rows), f"page {self.PAGE} renders all lines")
        for i, (actual, row) in enumerate(zip(probe["lines"], rows)):
            self.assertAlmostEqual(actual, row["w"] * size, delta=1.0,
                                   msg=f"@{size}px line {i + 1}: {actual}px")

    def test_0_size_20(self):
        """20px: every line is its em width x 20"""
        self.load_with_font_size(20)
        self.assert_geometry(20)

    def test_1_size_33(self):
        """33px: any size works, no pre-built DB needed"""
        self.load_with_font_size(33)
        self.assert_geometry(33)


if __name__ == '__main__':
    unittest.main()
