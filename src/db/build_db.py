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
TMP = "tmp_download"
DB_OUT = "assets/db"
DB = "AyahInfo_1024.db"
TXT = "Uthmani.txt"
TEST_HTML_TEMPLATE = "src/template/part_width_test.html"
STRETCH_ROUNDING = 3
CDN = 'https://www.unpkg.com/quran-madina-html/'
REPO = CDN #'https://raw.githubusercontent.com/tarekeldeeb/quran-madina-html-no-images/main/'
DEFAULTS = {'name':'Madina', 'published': 1985,
           'title':"مصحف المدينة الإصدار القديم - مجمع الملك فهد لطباعة المصحف الشريف",
           'font_family':'Amiri Quran Colored',
           'font_url':REPO+'assets/fonts/AmiriQuranColored.woff2',
           'font_size':16, 'line_width':275}
FIRST_LINE_PAGE1 = 1
FIRST_LINE_PAGE2 = 1
# Runtime globals
JSON_HEADER = "{}"
BASE_DIR = ""
DBG_LINE_WIDTHS = []

def _query(query):
    conn = sqlite3.connect(os.path.join(TMP,DB))
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return result

def _get_aya_data(sura, ayah):
    result = _query(f'select page_number, line_number from glyphs '
                    f'where sura_number={sura} and ayah_number={ayah}')
    return list(map(list, result))

def _get_test_filename(font, size):
    suffix = f'-{font}-{size}'
    return os.path.join(BASE_DIR,"src/db/test"+suffix+".html")

def _get_surah_name(sura_id, decorate = False):
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
      "الفلق", "الناس"
    ]
    sura_name = "سورة " + __name[sura_id]
    if decorate:
        return "🙮 " + sura_name + " 🙬"
    else:
        return sura_name

def _make_html(font, font_url, font_sz, line_width):
    with open(TEST_HTML_TEMPLATE, "r", encoding="utf8") as template:
        soup = BeautifulSoup(template.read(), 'html.parser')
    style_elem = soup.find("style").string # type: ignore
    style_elem = style_elem.replace("me_quran", font) # type: ignore
    style_elem = style_elem.replace("Amiri Quran Colored", font)
    style_elem = re.sub(r"https.*woff", font_url, style_elem)
    style_elem = style_elem.replace("260", str(line_width))
    style_elem = style_elem.replace("16", str(font_sz))
    soup.find("style").string = style_elem # type: ignore
    with open(_get_test_filename(font, font_sz), 'w', encoding="utf8") as file:
        file.write(str(soup))

def _update_html_text(web_driver, text):
    web_driver.execute_script(f'document.getElementById(\'test\').textContent = \'{text}\'')

def _ensure_page_has_loaded(web_driver, url):
    time.sleep(5) # Hack!
    try:
        WebDriverWait(web_driver, 5).until(EC.url_to_be(url))
    except TimeoutException:
        pass
        #print(f'URL ({url}) was not rendered with in allocated time')
        #print(f'Current: {web_driver.current_url}')

def _get_aya01(sura_id, page, line):
    title_page = 1 if sura_id == 0 else page+1 if line==15 else page
    if sura_id == 0:
        title_line = FIRST_LINE_PAGE1
    elif sura_id == 1:
        title_line = FIRST_LINE_PAGE2
    else:
        title_line = 1 if  line==15 else line+1
    bsm_page = title_page+1 if title_line==15 else title_page
    bsm_line = 1 if title_line==15 else title_line+1
    aya01 = [{ "p": title_page,
              "r": [{"l": title_line, "t": _get_surah_name(sura_id, True), "o": 0, "s": -1}]},
            { "p": bsm_page,
              "r": [{"l": bsm_line, "t": "﷽", "o": 0, "s": -1}]}]
    if sura_id == 0:
        aya01.pop()
        aya01.insert(0, { "p": title_page,  #Empty aya: Ensures correct numbers
                       "r": [{"l": title_page, "t": "", "o": 0, "s": -1}]}) 
    return aya01

def _get_width(aya_text, web_driver):
    _update_html_text(web_driver, aya_text)
    return web_driver.execute_script("return document.getElementById('test')"
                                     ".getBoundingClientRect().width")

def _print_dbg_widths():
    print(f'Non-Stretched Line widths:: Avg: {sum(DBG_LINE_WIDTHS) / len(DBG_LINE_WIDTHS)}, '
           f'Max:{max(DBG_LINE_WIDTHS)}, Min:{min(DBG_LINE_WIDTHS)}')

def _update_line_data(work_pointer, cfg):
    """Calculate the stretching factor (s), then apply to all previous line
    parts and updates their offsets (o).
    Finally, the returns (s,o) for the last part to be written later.

    Args: work_pointer
        suras (JSON): with complete Ayas
        parts (list): parts of an Aya
        sura (int): Current Surah number
        aya (int): Current Ayah number
        current_line (int): Line Number to update in page
        current_line_width (float): Sum of widths of all line parts
    """
    suras, parts, page, sura, aya, current_line, current_line_width = work_pointer
    look_back = 5
    if current_line_width<cfg.line_width/4:
        if aya <= 1: #Skip empty lines at Sura start
            return suras, parts
        _save_json(JSON_HEADER, suras, cfg)
        raise ValueError(f'Problem with aya={aya} of sura={sura} at line={current_line}'
                         f'[short: {current_line_width}px]')
    line_too_short = current_line_width<cfg.line_width*0.5 or page<=2
    DBG_LINE_WIDTHS.append(current_line_width)
    if line_too_short:
        stretch = -1
    else:
        stretch = cfg.line_width/(current_line_width) if page>2 else 1
    aya_look_back = aya-look_back if aya>look_back else 1
    offset = 0
    if aya > 1:
        search_ayas = filter(lambda a: a["p"] == page, suras[sura-1]['ayas'][aya_look_back+1:aya+1])
        for search_aya in search_ayas:
            for search_aya_part in search_aya['r']:
                if search_aya_part['l'] == int(current_line):
                    tmp = search_aya_part['o']*abs(stretch)
                    search_aya_part['o'] = math.ceil(offset)
                    offset = offset + tmp
                    search_aya_part['s'] = round(stretch, STRETCH_ROUNDING)
    if len(parts) > 0:
        parts[-1]["o"] = math.ceil(offset)
        parts[-1]["s"] = round(stretch, STRETCH_ROUNDING)
    return suras, parts

def _get_json_filename(cfg):
    json_file = f'{cfg.name}-{cfg.font_family.split()[0]}-{cfg.font_size}px.json'
    return os.path.join(DB_OUT, json_file)

def _save_json(header, suras, cfg):
    j = json.loads(header)
    j.update({"suras":suras})
    with open(_get_json_filename(cfg), 'w', encoding="utf-8") as json_file:
        json.dump(j, json_file, ensure_ascii = False, indent=2)
    print(f'Saved: {_get_json_filename(cfg)}')

def run(cfg):
    """Runs the build_db module
    """
    global BASE_DIR # type: ignore
    BASE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../..")
    try:
        os.mkdir(TMP)
        # Start with downloading the Glyph DB
        url = "https://raw.githubusercontent.com/murtraja/quran-android-images-helper"\
            "/master/static/databases/" + DB.lower()
        response = requests.get(url, timeout=500)
        with open(os.path.join(TMP,DB), "wb") as file_db:
            file_db.write(response.content)
        print("Downloaded Quran DataBase")
        #
        # Then download the text from Tanzil.net
        txt_url = "https://tanzil.net/pub/download/index.php?marks=true&sajdah=true"\
                    "&rub=true&tatweel=true&quranType=uthmani&outType=txt-2&agree=true"
        req = requests.get(txt_url, timeout=500, allow_redirects=True)
        text = req.content
        with open(os.path.join(TMP,TXT), "wb") as file_txt:
            file_txt.write(text)
        print("Downloaded Quran Text file.")
    except OSError:
        print("Skipping download ..")
    _make_html(cfg.font_family, cfg.font_url, cfg.font_size, cfg.line_width)
    #
    # Finally Load the Html Template and Driver
    chrome_options = Options()
    chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
    web_driver = webdriver.Chrome(options=chrome_options)
    test_url = "file://" + _get_test_filename(cfg.font_family, cfg.font_size)
    web_driver.get(test_url)
    _ensure_page_has_loaded(web_driver, test_url)
    # Lets start building the json output ..
    global JSON_HEADER # type: ignore
    JSON_HEADER = f'\
        {{"title": "{cfg.title}",\
        "published": {cfg.published},\
        "font_family": "{cfg.font_family}",\
        "font_url": "{cfg.font_url}",\
        "font_size": {cfg.font_size},\
        "line_width": {cfg.line_width}}}'
    suras = parts = []
    page = aya = current_line_width = current_line = 0
    print("Processing ..")
    with tqdm.tqdm(total=os.path.getsize(os.path.join(TMP,TXT)), leave=False) as progress_bar:
        with open(os.path.join(TMP,TXT), encoding="utf8") as file_txt:
            for aya_line in file_txt:
                progress_bar.update(len(aya_line.encode('utf-8')))
                tokens = aya_line.strip().split('|')
                if len(tokens) == 3:
                    prev_aya = aya
                    sura, aya, aya_text = tokens
                    if "Amiri" in cfg.font_family:
                        aya_text = aya_text + f' \u06DD{aya}'
                    else:
                        aya_text = aya_text.replace("ٱ", "ا") + f' \uFD3F{aya}\uFD3E'
                    sura = int(sura)
                    aya = int(aya)
                    lines = {} # Key=LineNumber, Value=Number of glyphs
                    prev_parts = parts
                    parts = [] # Break each ayah into parts/lines
                    #Add a Sura
                    if len(suras)<sura:
                        suras.append({"name": _get_surah_name(sura-1),
                                      "ayas":_get_aya01(sura-1, page, current_line)})
                    ayah_data = _get_aya_data(sura, aya)
                    if page < ayah_data[0][0]: #new page
                        prev_line = current_line
                        prev_line_width = current_line_width
                        prev_sura = sura-1 if aya==1 else sura
                        if page == 0:
                            current_line = FIRST_LINE_PAGE1
                        elif page == 1:
                            current_line = FIRST_LINE_PAGE2
                        else:
                            current_line = 1
                        current_line_width = 0
                        page = ayah_data[0][0]
                        new_page = page>0
                    else:
                        new_page = False
                    for glyph in ayah_data:
                        if str(glyph[1]) not in lines:
                            lines.update({str(glyph[1]):1})
                        else:
                            lines[str(glyph[1])] = lines[str(glyph[1])] + 1
                    if aya==1 and sura!=1 and sura!=9:
                        skip_words = 4 #Skip Basmala from first aya. TODO: Add Basmala Manually
                    else:
                        skip_words = 0
                    if len(ayah_data) != len(aya_text.split())-skip_words:
                        print(f'Mismatch at {sura}-{aya}: Glyphs={len(ayah_data)} for:{aya_text}')
                    for line_index, line in lines.items():
                        if line_index != str(current_line): #new line
                            #Override (o,s) of previous line parts
                            if new_page:
                                work_pointer = (suras, prev_parts, page-1, prev_sura, # type: ignore
                                                prev_aya, prev_line, prev_line_width) # type: ignore
                                suras, prev_parts = _update_line_data(work_pointer, cfg)
                            work_pointer = (suras, parts, page, sura, aya,
                                            current_line, current_line_width)
                            suras, parts = _update_line_data(work_pointer, cfg)
                            current_line_width = 0
                        current_line = int(line_index)
                        aya_text_part = " ".join(aya_text.split()
                                                 [skip_words:skip_words+line])
                        if current_line_width > 0: #Need an extra space after the prev aya
                            aya_text_part = " " + aya_text_part
                        aya_part_width = _get_width(aya_text_part, web_driver)
                        current_line_width = current_line_width + aya_part_width
                        parts.append({"l":int(line_index), "t":aya_text_part,
                                      "o":aya_part_width, "s": 1.0})
                        skip_words = skip_words + line
                    suras[sura-1]["ayas"].append({"p":page, "r":parts}) # New completed ayah
    print("Closing Chrome ..")
    web_driver.close()
    os.remove(_get_test_filename(cfg.font_family, cfg.font_size))
    _save_json(JSON_HEADER, suras, cfg)
    _print_dbg_widths()

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
    run(parser.parse_args())
