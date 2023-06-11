"""Builds the JSON DB for Quran-Madina-HTML-No-Images project
    It downloads all dependencies, process the Quran String, OCR data
    and finally spits out the JSON DB.

    Raises:
        Exception: Unexpected Quran Content from DB

    Returns:
        None
"""
import os
import math
import json
import sqlite3
import requests
import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

TMP = "temp"
DB = "AyahInfo_1024.db"
TXT = "Uthmani.txt"
WIDTH_TEST_HTML = "part_width_test.html"
DB_JSON_FILE = 'Madina-Amiri.json'
LINE_WIDTH = 400
STRETCH_ROUNDING = 3

def _query(query):
    conn = sqlite3.connect(os.path.join(TMP,DB))
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return result

def _get_aya_data(sura, ayah):
    result = _query(f'select page_number, line_number, min_x, max_x, min_y, max_y from glyphs '
                    f'where sura_number={sura} and ayah_number={ayah}')
    return list(map(list, result))

def _get_surah_name(sura_id):
    sura_name = ["الفاتحة", "البقرة", "آل عمران",
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
    return "سورة " + sura_name[sura_id]

def _update_html_text(web_driver, text):
    web_driver.execute_script(f'document.getElementById(\'test\').textContent = \'{text}\'')

def _get_width(web_driver):
    return web_driver.execute_script("return document.getElementById('test')"
                                     ".getBoundingClientRect().width")

def _update_line_data(work_pointer):
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
    if current_line_width<20:
        _save_json("", suras)
        raise ValueError(f'Problem with [short] aya={aya} of sura={sura} at line={current_line}')
    stretch = LINE_WIDTH/(current_line_width) if page>2 else 1
    aya_look_back = aya-look_back if aya>look_back else 1
    offset = 0
    if aya > 1:
        search_ayas = suras[sura-1]['ayas'][aya_look_back-1:aya-1]
        for search_aya in search_ayas:
            for search_aya_part in search_aya['r']:
                if search_aya_part['l'] == int(current_line):
                    tmp = search_aya_part['o']*stretch
                    search_aya_part['o'] = math.ceil(offset)
                    offset = offset + tmp
                    search_aya_part['s'] = round(stretch, STRETCH_ROUNDING)
    if len(parts) > 0:
        parts[-1]["o"] = math.ceil(offset*stretch)
        parts[-1]["s"] = round(stretch, STRETCH_ROUNDING)
    return suras, parts

def _preprocess_text(txt):
    return txt.replace(" ۖ "," ۖ")

def _save_json(json_header, suras):
    j = json.loads(json_header)
    j.update({"suras":suras})
    with open(DB_JSON_FILE, 'w', encoding="utf-8") as json_file:
        json.dump(j, json_file, ensure_ascii = False, indent=2)
    print(f'Saved: {DB_JSON_FILE}')

def run():
    """Runs the build_db module
    """
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
    #
    # Finally Load the Html Template and Driver
    chrome_options = Options()
    chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
    web_driver = webdriver.Chrome(options=chrome_options)
    dir_path = os.path.dirname(os.path.realpath(__file__))
    web_driver.get("file://" + os.path.join(dir_path,WIDTH_TEST_HTML))
    # Lets start building the json output ..
    json_header = f'\
        {{"title": "مصحف المدينة الإصدار القديم - مجمع الملك فهد لطباعة المصحف الشريف",\
        "published": 1985,\
        "font_family": "Amiri Quran",\
        "font_url":\
            "https://fonts.gstatic.com/s/amiriquran/v7/_Xmo-Hk0rD6DbUL4_vH8Zp5v5i2ssg.woff2",\
        "font_size": 24,\
        "line_width": {LINE_WIDTH}}}'
    suras = []
    page = aya = current_line_width = current_line = 0
    print("Processing ..")
    with tqdm.tqdm(total=os.path.getsize(os.path.join(TMP,TXT))) as progress_bar:
        with open(os.path.join(TMP,TXT), encoding="utf8") as file_txt:
            for aya_line in file_txt:
                progress_bar.update(len(aya_line.encode('utf-8')))
                tokens = aya_line.strip().split('|')
                if len(tokens) == 3:
                    prev_aya = aya
                    sura, aya, aya_text = tokens
                    #aya_text = _preprocess_text(aya_text)
                    sura = int(sura)
                    aya = int(aya)
                    #Add a Sura
                    if len(suras)<sura:
                        suras.append({"name": _get_surah_name(sura-1), "ayas":[]})
                    ayah_data = _get_aya_data(sura, aya)
                    #ayah_data = list(filter(lambda a: a[3]-a[2] > 8 or a[5]-a[4] > 23, ayah_data))
                    if page < ayah_data[0][0]: #new page
                        prev_line = current_line
                        prev_line_width = current_line_width
                        prev_sura = sura-1 if aya==1 else sura
                        current_line = 1 if page>1 else 3 if page==1 else 2 #first line in page
                        current_line_width = 0
                        page = ayah_data[0][0]
                        new_page = page>0
                    else:
                        new_page = False
                    lines = {} # Key=LineNumber, Value=Number of glyphs
                    parts = [] # Break each ayah into parts/lines
                    for glyph in ayah_data:
                        if str(glyph[1]) not in lines:
                            lines.update({str(glyph[1]):1})
                        else:
                            lines[str(glyph[1])] = lines[str(glyph[1])] + 1
                    if aya==1 and sura!=1 and sura!=9:
                        skip_words = 4 #Skip Basmala from first aya. TODO: Add Basmala Manually
                    else:
                        skip_words = 0
                    if len(ayah_data)-1 != len(aya_text.split())-skip_words:
                        print(f'Mismatch at {sura}-{aya}: Glyphs={len(ayah_data)} for:{aya_text}')    
                    for line in lines:
                        if line != str(current_line): #new line
                            #Override (o,s) of line parts
                            if new_page:
                                work_pointer = (suras, parts, page, prev_sura,
                                                prev_aya, prev_line, prev_line_width)
                            else:
                                work_pointer = (suras, parts, page, sura, aya,
                                                current_line, current_line_width)
                            suras, parts = _update_line_data(work_pointer)
                            current_line_width = 0
                        current_line = int(line)
                        aya_text_part = " ".join(aya_text.split()
                                                 [skip_words:skip_words+lines[line]])
                        if line == list(lines.keys())[-1]:
                            aya_text_part = aya_text_part + f' \uFD3F{aya}\uFD3E'
                        _update_html_text(web_driver, aya_text_part)
                        aya_part_width = _get_width(web_driver)
                        current_line_width = current_line_width + aya_part_width
                        parts.append({"l":int(line), "t":aya_text_part,
                                      "o":aya_part_width, "s": 1.0})
                        skip_words = skip_words + lines[line]
                    suras[sura-1]["ayas"].append({"p":page, "r":parts}) # New completed ayah
    print("Closing Chrome ..")
    web_driver.close()
    _save_json(json_header, suras)

if __name__ == '__main__':
    run()
