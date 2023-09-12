"""Builds the JSON DB for Quran-Madina-HTML-No-Images project
    It downloads all dependencies, process the Quran String, OCR data
    and finally spits out the JSON DB.

    Raises:
        Exception: Unexpected Quran Content from DB

    Returns:
        None
"""
import os
import time
import math
from functools import reduce
from typing import List
import json
import re
import argparse
import sqlite3
import requests
import tqdm
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Internal Constants: Do not edit!
CDN = 'https://www.unpkg.com/quran-madina-html/'
REPO = CDN #'https://raw.githubusercontent.com/tarekeldeeb/quran-madina-html-no-images/main/'
DEFAULTS = {'name':'Madina05', 'published': 1405,
           'title':"مصحف المدينة الإصدار القديم - مجمع الملك فهد لطباعة المصحف الشريف",
           'font_family':'Hafs',
           'font_url':REPO+'assets/fonts/Hafs.woff2',
           'font_size':16, 'line_width':275}

class LineCursor:
    """Part of the global DbBuilder, points to the current point in DB"""
    def __init__(self, page, line):
        self.page = page
        self.line = line
    def __le__(self, other):
        if self.page<other.page:
            return True
        if self.page == other.page:
            return self.line <= other.line
        return False
    def next_line(self):
        """Move the cursor forward 1 line"""
        if self.line == 15:
            self.page = self.page + 1
        self.line = 1 if self.line == 15 else self.line + 1

class Part:
    """Aya Part, may be a line or less"""
    def __init__(self, line, text, width):
        self.line = line
        self.text = text
        self.width = width
        self.offset = None
        self.stretch = None
    def to_json(self):
        """Returns a JSON-ready Object"""
        return {"l":self.line, "t":self.text,"o":self.offset, "s": self.stretch}

class QuranLine:
    """Temp Class that holds a single line, with multiple aya parts"""
    STRETCH_ROUNDING = 3
    def __init__(self, page, parts):
        self.page = page
        self.parts = parts
    def previous_widths(self, parts, stretch)-> int:
        """Offset each aya by sum of widths of previous ayas on the same line"""
        if len(parts)==0:
            return 0
        if len(parts)==1:
            return math.ceil(parts[0].width * stretch)
        return math.ceil(reduce(lambda a,b: (a.width*stretch if hasattr(a,'width') else a)
                                +b.width*stretch, parts))
    def update_parts(self, line_width: int)->List[Part]:
        """Apply stretch and offset calculations to all line parts"""
        initial_width = 0
        for part in self.parts:
            initial_width = initial_width + part.width
        stretch = line_width/initial_width
        DbBuilder.dbg_line_widths.append(initial_width)
        for part_index, part in enumerate(self.parts):
            part.stretch = round(stretch, self.STRETCH_ROUNDING) if self.page>2 and stretch<1.5 \
                           else -1
            part.offset = self.previous_widths(self.parts[0:part_index], stretch)
        return self.parts

class Ayah:
    """Quran Aya"""
    def __init__(self, sura_index, index, text, prev_line_end):
        self.sura_index = sura_index
        self.index = index
        self.page = 0
        self.parts = []
        self.line_start = None
        self.line_end = None
        self.prev_line_end = prev_line_end
        if "Amiri" in DbBuilder.cfg.font_family:
            self.text = text + f' \u06DD{index}'
        else:
            self.text = text + f' \uFD3F{self.get_hindi_numbers(index)}\uFD3E'
        if "Uthman" in DbBuilder.cfg.font_family:
            self.text = self.text.replace("ٱ", "ا")
    @classmethod
    def create_centered(cls, text, page, line):
        """Create an Aya Centered Object from 1-line text"""
        instance = cls(0,0,text,0)
        instance.page = page
        instance.line_start = line
        part = Part(line, text, 100)
        part.offset = 0 # type: ignore
        part.stretch = -1  # type: ignore
        part.text = text
        instance.parts = [part]
        return instance
    def get_hindi_numbers (self, number):
        """Remap all numeric characters to hindi """
        table = str.maketrans('0123456789',
                              '\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669')
        return str(number).translate(table)

    def update_json(self):
        """returns the json string of this object"""
        return {"p": self.page, "r": list(map(lambda part: part.to_json(), self.parts))}
    def process(self):
        """Process the aya to create a json-ready object"""
        ayah_data = DbReader.get_aya_data(self.sura_index+1, self.index)
        self.page = ayah_data[0][0]
        self.line_start = ayah_data[0][1]
        self.line_end = ayah_data[-1][1]
        words_in_lines = {} # Key=LineNumber, Value=Number of glyphs/words
        for glyph in ayah_data:
            if str(glyph[1]) not in words_in_lines:
                words_in_lines.update({str(glyph[1]):1})
            else:
                words_in_lines[str(glyph[1])] = words_in_lines[str(glyph[1])] + 1
        if self.index==1 and self.sura_index!=0 and self.sura_index!=8:
            skip_words = 4 #Skip Basmala from first aya.
        else:
            skip_words = 0
        if len(ayah_data) != len(self.text.split())-skip_words:
            DbBuilder.error_logger.add_message(f'Mismatch at {self.sura_index}-{self.index}: '
                  f'Glyphs={len(ayah_data)} for:{self.text}')
        for line_index, line in words_in_lines.items():
            aya_text_part = " ".join(self.text.split()
                                        [skip_words:skip_words+line])
            if int(line_index) == self.prev_line_end:
                aya_text_part = " " + aya_text_part # Add a space after prev aya on the same line
            aya_part_width = DbBuilder.html_helper.get_width(aya_text_part)
            self.parts.append(Part(int(line_index), aya_text_part, aya_part_width))
            skip_words = skip_words + line
        DbBuilder.cursor.page = self.page
        DbBuilder.cursor.line = self.line_end
        DbBuilder.progress.update(len(self.text.encode('utf-8'))+2)
        return self

class Surah:
    """Quran Surah/Chapter"""
    def __init__(self, index, lines):
        self.index = index
        self.lines = lines
        self.name = self.get_surah_name(index)
        self.ayas = []
    @staticmethod
    def get_surah_name(sura_id, decorate = False):
        """Returns a Sura Name String"""
        __name = ["الفاتحة", "البقرة", "آل عمران",
                "النساء", "المائدة", "الأنعام", "الأعراف", "الأنفال", "التوبة",
                "يونس", "هود", "يوسف", "الرعد", "إبراهيم", "الحجر", "النحل",
                "الإسراء", "الكهف", "مريم", "طه", "الأنبياء", "الحج", "المؤمنون",
                "النور", "الفرقان", "الشعراء", "النمل", "القصص", "العنكبوت",
                "الروم", "لقمان", "السجدة", "الأحزاب", "سبأ", "فاطر", "يس",
                "الصافات", "ص", "الزمر", "غافر", "فصلت", "الشورى", "الزخرف",
                "الدخان", "الجاثية", "الأحقاف", "محمد", "الفتح", "الحجرات", "ق",
                "الذاريات", "الطور", "النجم", "القمر", "الرحمن", "الواقعة",
                "الحديد", "المجادلة", "الحشر", "الممتحنة", "الصف", "الجمعة",
                "المنافقون", "التغابن", "الطلاق", "التحريم", "الملك", "القلم",
                "الحاقة", "المعارج", "نوح", "الجن", "المزمل", "المدثر", "القيامة",
                "الإنسان", "المرسلات", "النبأ", "النازعات", "عبس", "التكوير",
                "الانفطار", "المطففين", "الانشقاق", "البروج", "الطارق", "الأعلى",
                "الغاشية", "الفجر", "البلد", "الشمس", "الليل", "الضحى", "الشرح",
                "التين", "العلق", "القدر", "البينة", "الزلزلة", "العاديات",
                "القارعة", "التكاثر", "العصر", "الهمزة", "الفيل", "قريش",
                "الماعون", "الكوثر", "الكافرون", "النصر", "المسد", "الإخلاص",
                "الفلق", "الناس"]
        sura_name = "سورة " + __name[sura_id]
        if decorate:
            decorated = "▓▓▓▒▒▒░░░ "
            return decorated + sura_name + decorated[::-1]
        return sura_name
    def get_aya01(self):
        """Returns a list of 2 ayas:"""
        page = DbBuilder.cursor.page
        line = DbBuilder.cursor.line
        title_page = 1 if self.index == 0 else \
                    2 if self.index == 1 else \
                    page+1 if line==15 else \
                    page
        title_line = 1 if  line==15 or self.index<=1 else line+1
        bsm_page = title_page+1 if title_line==15 else title_page
        bsm_line = 1 if title_line==15 else title_line+1
        aya0 = Ayah.create_centered(Surah.get_surah_name(self.index, True),
                                    title_page, title_line)
        aya1 = Ayah.create_centered("﷽", bsm_page, bsm_line)
        aya_empty = Ayah.create_centered("", title_page, title_line)

        if self.index == 0:
            return [aya_empty,aya0]
        return [aya0, aya1]
    def process(self):
        """Process the surah to create a json-ready object"""
        self.ayas = self.get_aya01()
        prev_line_end = 0
        for line in self.lines:
            aya = Ayah(self.index, int(line[0]), line[1], prev_line_end).process()
            self.ayas.append(aya)
            prev_line_end = aya.line_end
        return self
    def update_json(self):
        """returns the json string of this object"""
        return {"name": self.name,
                "ayas": list(map(lambda aya: aya.update_json(), self.ayas))}
    def align_lines(self):
        """Ensure All Line widths are equal
            <Aya.Part-0>----------           => Handled with previous Aya(s), ignore part
            <    Aya.Part-1      >           => Handle Alone in 1-line
            --------< Aya.Part-2 >           => Handle + Read Next Aya(s)
        """
        for aya_index, aya in enumerate(self.ayas):
            for part_index, part in enumerate(aya.parts):
                if part.offset is None: # Ignore already processed part
                    if part_index<len(aya.parts)-1: # Complete Line
                        part = QuranLine(aya.page, [part]).update_parts(DbBuilder.cfg.line_width)[0]
                    else:
                        line_parts = [part]
                        search_index = aya_index +1
                        while search_index<len(self.ayas) and\
                            self.ayas[search_index].parts[0].line == part.line:
                            line_parts.append(self.ayas[search_index].parts[0])
                            search_index = search_index + 1
                        line_parts = QuranLine(aya.page,line_parts)\
                            .update_parts(DbBuilder.cfg.line_width)
        return self.update_json()

class Mushaf:
    """Quran book, has a configuration parameter to define the rendering font"""
    def __init__(self, cfg, file_txt):
        self.cfg = cfg
        self.file_txt = file_txt
        self.suras = []
        self.suras_json = []
    def process(self):
        """Process the Mushaf to create a json-ready object"""
        sura_lines = []
        for aya_line in self.file_txt:
            tokens = aya_line.strip().split('|')
            if len(tokens) == 3:
                sura, aya, aya_text = tokens
                if len(self.suras) == int(sura)-1:
                    sura_lines.append((aya, aya_text))
                else:
                    self.suras.append(Surah(len(self.suras), sura_lines).process())
                    sura_lines = [(aya, aya_text)]
        self.suras.append(Surah(len(self.suras), sura_lines).process())  #Last Sura
        for sura in self.suras: #second scan for alignment and json conversion
            self.suras_json.append(sura.align_lines())
        return self.suras_json

class DbReader:
    """SQLITE DB Handler"""
    TMP = "tmp_download"
    DB_OUT = "assets/db"
    DB = "AyahInfo_1024.db"
    @staticmethod
    def __query(query):
        conn = sqlite3.connect(os.path.join(DbReader.TMP,DbReader.DB))
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return result
    @staticmethod
    def get_aya_data(sura, ayah):
        """Returns Aya glyphs as rows, with page, line as columns"""
        result = DbReader.__query(f'select page_number, line_number from glyphs '
                        f'where sura_number={sura} and ayah_number={ayah}')
        return list(map(list, result))

class JsonHelper:
    """A collection of Json helper functions"""
    def __init__(self, cfg):
        self.cfg = cfg
        self.header = self.get_json_header(self.cfg)

    def get_json_header(self, cfg):
        """Returns a Json String of the Db header object"""
        if cfg:
            return f'\
                {{"title": "{cfg.title}",\
                "published": {cfg.published},\
                "font_family": "{cfg.font_family}",\
                "font_url": "{cfg.font_url}",\
                "font_size": {cfg.font_size},\
                "line_width": {cfg.line_width}}}'
        return ""

    def get_json_filename(self):
        """Get Json filename String according to config"""
        json_file = f'{self.cfg.name}-{self.cfg.font_family.replace(" ","_")}' \
                    f'-{self.cfg.font_size}px.json'
        return os.path.join(DbReader.DB_OUT, json_file)

    def save_json(self, suras):
        """Save Db as a Json file"""
        j = json.loads(self.header)
        j.update({"suras":suras})
        with open(self.get_json_filename(), 'w', encoding="utf-8") as json_file:
            json.dump(j, json_file, ensure_ascii = False, indent=2)
        print(f'Saved: {self.get_json_filename()}')

class HtmlHelper:
    """A Collection of Html Helper Functions"""
    TEST_HTML_TEMPLATE = "template/part_width_test.html"
    @staticmethod
    def make_html_test():
        """Edit the html test template according to cfg"""
        font = DbBuilder.cfg.font_family
        font_url = DbBuilder.cfg.font_url
        font_sz = DbBuilder.cfg.font_size
        line_width = DbBuilder.cfg.line_width
        with open(HtmlHelper.TEST_HTML_TEMPLATE, "r", encoding="utf8") as template:
            soup = BeautifulSoup(template.read(), 'html.parser')
        style_elem = soup.find("style").string # type: ignore
        style_elem = style_elem.replace("me_quran", font) # type: ignore
        style_elem = style_elem.replace("Amiri Quran Colored", font)
        style_elem = re.sub(r"https.*woff", font_url, style_elem)
        style_elem = style_elem.replace("260", str(line_width))
        style_elem = style_elem.replace("16", str(font_sz))
        soup.find("style").string = style_elem # type: ignore
        with open(DbBuilder.get_test_filename(), 'w', encoding="utf8") as file:
            file.write(str(soup))
    @staticmethod
    def update_html_text(text):
        """Updates the text of the test template"""
        DbBuilder.web_driver.execute_script(f'document.getElementById(\'test\')' \
                                          f'.textContent = \'{text}\'')
    @staticmethod
    def ensure_page_has_loaded(url):
        """Blocks process till web_driver has fully rendered a page with url"""
        time.sleep(5) # Hack!
        try:
            WebDriverWait(DbBuilder.web_driver, 5).until(EC.url_to_be(url))
        except TimeoutException:
            pass
            #print(f'URL ({url}) was not rendered with in allocated time')
            #print(f'Current: {web_driver.current_url}')
    @staticmethod
    def get_width(aya_text):
        """Get Browser rendered text width in pixels"""
        HtmlHelper.update_html_text(aya_text)
        return DbBuilder.web_driver.execute_script("return document.getElementById('test')"
                                        ".getBoundingClientRect().width")

class ErrorLogger:
    """A simple deferred Error Logger"""
    def __init__(self):
        self.logs = []
    def add_message(self, line):
        """Add an error message to be displayed later"""
        self.logs.append(line)
    def flush(self):
        """Display all added error messages"""
        if self.logs:
            print("Errors Encountered while processing:")
            for index, line in enumerate(self.logs):
                print(f"| E{index}:\t{line}")
            self.logs.clear()

class DbBuilder:
    """Aggregates all needed Helper Classes to run"""
    web_driver = webdriver.Chrome()
    cursor = LineCursor(0,0)
    progress = tqdm.tqdm()
    cfg = argparse.Namespace()
    base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../..")
    json_helper = JsonHelper(None)
    error_logger = ErrorLogger()
    text = "Uthmani.txt"
    dbg_line_widths = []

    @staticmethod
    def get_test_filename():
        """returns the Html file name to be used for testing/web_driver"""
        suffix = f'-{DbBuilder.cfg.font_family}-{DbBuilder.cfg.font_size}' # type: ignore
        return os.path.join(DbBuilder.base_dir,"src/db/test"+suffix+".html")
    @staticmethod
    def print_dbg_widths():
        """Stats for Quran line widths"""
        if DbBuilder.dbg_line_widths:
            print(f'Non-Stretched Line widths:: '
                  f'Avg:{sum(DbBuilder.dbg_line_widths)/len(DbBuilder.dbg_line_widths)}, '
                  f'Max:{max(DbBuilder.dbg_line_widths)}, Min:{min(DbBuilder.dbg_line_widths)}')
    @staticmethod
    def run(cfg):
        """Entry Point for the build_db module"""
        DbBuilder.cfg = cfg
        DbBuilder.cursor = LineCursor(0, 0)
        DbBuilder.json_helper = JsonHelper(cfg)
        DbBuilder.html_helper = HtmlHelper()
        DbBuilder.error_logger = ErrorLogger()
        try:
            os.mkdir(DbReader.TMP)
            # Start with downloading the Glyph DB
            url = "https://raw.githubusercontent.com/murtraja/quran-android-images-helper"\
                "/master/static/databases/" + DbReader.DB.lower()
            response = requests.get(url, timeout=500)
            with open(os.path.join(DbReader.TMP,DbReader.DB), "wb") as file_db:
                file_db.write(response.content)
            print("Downloaded Quran DataBase")
            #
            # Then download the text from Tanzil.net
            txt_url = "https://tanzil.net/pub/download/index.php?marks=true&sajdah=true"\
                        "&rub=true&tatweel=true&quranType=uthmani&outType=txt-2&agree=true"
            req = requests.get(txt_url, timeout=500, allow_redirects=True)
            text = req.content
            with open(os.path.join(DbReader.TMP,DbBuilder.text), "wb") as file_txt:
                file_txt.write(text)
            print("Downloaded Quran Text file.")
        except OSError:
            print("Skipping download ..")
        DbBuilder.html_helper.make_html_test()
        #
        # Finally Load the Html Template and Driver
        chrome_options = Options()
        chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
        chrome_options.add_argument("--headless")
        DbBuilder.web_driver = webdriver.Chrome(options=chrome_options)
        test_url = "file://" + DbBuilder.get_test_filename()
        DbBuilder.web_driver.get(test_url)
        DbBuilder.html_helper.ensure_page_has_loaded(test_url)
        suras = []
        print("Processing ..")
        with tqdm.tqdm(total=os.path.getsize(os.path.join(DbReader.TMP,DbBuilder.text)),\
                       leave=False) as progress_bar:
            DbBuilder.progress = progress_bar
            with open(os.path.join(DbReader.TMP, DbBuilder.text), encoding="utf8") as file_txt:
                suras = Mushaf(DbBuilder.cfg, file_txt).process()
        print("Closing Chrome ..")
        DbBuilder.web_driver.close()
        os.remove(DbBuilder.get_test_filename())
        DbBuilder.json_helper.save_json(suras)
        DbBuilder.error_logger.flush()
        DbBuilder.print_dbg_widths()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build JSON DB for HTML Quran Rendering.')
    parser.add_argument("--name", required=False, default=DEFAULTS["name"],
                        help="Mus'haf Short Name")
    parser.add_argument("--title", required=False, default=DEFAULTS["title"],
                        help="Mus'haf Long Name")
    parser.add_argument("--published", type=int, required=False, default=DEFAULTS["published"],
                        help="Mus'haf Publish Date")
    parser.add_argument("--font_family", required=False, default=DEFAULTS["font_family"],
                        help="Font Family")
    parser.add_argument("--font_url", required=False, default=DEFAULTS["font_url"],
                        help="Font URL to use")
    parser.add_argument("--font_size", type=int, required=False, default=DEFAULTS["font_size"],
                        help="Font Size to render")
    parser.add_argument("--line_width", type=int, required=False, default=DEFAULTS["line_width"],
                        help="Page width to render")
    DbBuilder().run(parser.parse_args())
