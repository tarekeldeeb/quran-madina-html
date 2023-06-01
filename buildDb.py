"""Builds the JSON DB for Quran-Madina-HTML-No-Images project
    It downloads all dependencies, process the Quran String, OCR data
    and finally spits out the JSON DB.

    Raises:
        Exception: Unexpected Quran Content from DB

    Returns:
        None
"""
import sqlite3
import requests, os, tqdm
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

TMP = "temp"
DB = "AyahInfo_1024.db"
TXT = "Uthmani.txt"
WIDTH_TEST_HTML = "part_width_test.html"
DB_JSON_FILE = 'Madina-Amiri.json'
LINE_WIDTH = 400

def query(query):
    conn = sqlite3.connect(os.path.join(TMP,DB))
    c = conn.cursor()
    c.execute(query)
    result = c.fetchall()
    c.close()
    return result

def get_aya_data(sura, ayah):
    result = query("select page_number, line_number, min_x, max_x from glyphs\
                    where sura_number={} and ayah_number={}".format(sura, ayah))
    return list(map(lambda x: list(x), result))

def get_surah_name(sura_id):
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

def updateHtmlText(wd, text, skip):
    wd.execute_script("document.getElementById('test').textContent = '{}'".format(text))

def getWidth(wd):
    return wd.execute_script("return document.getElementById('test').getBoundingClientRect().width")

def updateLineData(suras, parts, sura, aya, current_line, current_line_width):
    """Calculate the stretching factor (s), then apply to all previous line 
    parts and updates their offsets (o).
    Finally, the returns (s,o) for the last part to be written later.
    
    Args:
        suras (JSON): with complete Ayas
        parts (list): parts of an Aya
        sura (int): Current Surah number
        aya (int): Current Ayah number
        current_line (int): Line Number to update in page
        current_line_width (float): Sum of widths of all line parts
    """
    LOOK_BACK = 5
    if current_line_width<20:
        save_json(suras)
        raise Exception("Problem with [short] aya={} of sura={} at line={}\
                        ".format(aya, sura, current_line))
    stretch = LINE_WIDTH/(current_line_width) if page>2 else 1
    aya_look_back = aya-LOOK_BACK if aya>LOOK_BACK else 1
    offset = 0
    if aya > 1:
        search_ayas = suras[sura-1]['ayas'][aya_look_back-1:aya-1]
        for a in search_ayas:
            for r in a['r']:
                if r['l'] == int(current_line):
                    tmp = r['o']*stretch
                    r['o'] = offset
                    offset = offset + tmp
                    r['s'] = stretch
    if len(parts) > 0:
        parts[-1]["o"] = offset*stretch
        parts[-1]["s"] = stretch
    return suras, parts

def save_json(suras):
    j = json.loads(json_header)
    j.update({"suras":suras})
    json_file = open(DB_JSON_FILE, 'w', encoding="utf-8")
    json.dump(j, json_file, ensure_ascii = False, indent=2)
    print("Saved: {}".format(DB_JSON_FILE) )
    json_file.close()

if __name__ == '__main__':
    try:
        os.mkdir(TMP)
        # Start with downloading the Glyph DB
        URL = "https://raw.githubusercontent.com/murtraja/quran-android-images-helper\
            /master/static/databases/" + DB.lower()
        response = requests.get(URL)
        open(os.path.join(TMP,DB), "wb").write(response.content)
        print("Downloaded Quran DataBase")
        #
        # Then download the text from Tanzil.net
        txt_url = "https://tanzil.net/pub/download/index.php?marks=true&sajdah=true\
                    &rub=true&tatweel=true&quranType=uthmani&outType=txt-2&agree=true"
        req = requests.get(txt_url, allow_redirects=True)
        text = req.content
        open(os.path.join(TMP,TXT), "wb").write(text)
        print("Downloaded Quran Text file.")
    except OSError as error:
        print("Skipping download ..")
    #
    # Finally Load the Html Template and Driver   
    chrome_options = Options()
    chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
    wd = webdriver.Chrome(options=chrome_options)
    dir_path = os.path.dirname(os.path.realpath(__file__))
    wd.get("file://" + os.path.join(dir_path,WIDTH_TEST_HTML))
    # Lets start building the json output ..
    json_header = '\
        {{"title": "مصحف المدينة الإصدار القديم - مجمع الملك فهد لطباعة المصحف الشريف",\
        "published": 1985,\
        "font_family": "Amiri Quran",\
        "font_url": "https://fonts.gstatic.com/s/amiriquran/v7/\
            _Xmo-Hk0rD6DbUL4_vH8Zp5v5i2ssg.woff2",\
        "font_size": 24,\
        "line_width": {}}}'.format(LINE_WIDTH)
    suras = []
    page = aya = current_line_width = current_line = 0
    print("Processing ..")
    with tqdm.tqdm(total=os.path.getsize(os.path.join(TMP,TXT))) as progress_bar:
        with open(os.path.join(TMP,TXT), encoding="utf8") as f:
            for aya_line in f:
                progress_bar.update(len(aya_line.encode('utf-8')))
                tokens = aya_line.strip().split('|')
                if len(tokens) == 3:
                    prev_aya = aya
                    sura, aya, aya_text = tokens
                    sura = int(sura)
                    aya = int(aya)
                    #Add a Sura
                    if len(suras)<sura:
                        suras.append({"name": get_surah_name(sura-1), "ayas":[]})
                    ayah_data = get_aya_data(sura, aya)
                    ayah_data = list(filter(lambda a: a[3]-a[2] > 30, ayah_data))
                    if page < ayah_data[0][0]: #new page
                        prev_line = current_line
                        prev_line_width = current_line_width
                        prev_sura = sura-1 if aya==1 else sura
                        current_line = 1 if page>1 else 3 if page==1 else 2 #first line in page
                        current_line_width = 0
                        page = ayah_data[0][0]
                        new_page = True if page>0 else False
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
                    for l in lines.keys():
                        if l != str(current_line): #new line
                            #Override (o,s) of line parts
                            if new_page:
                                suras, parts = updateLineData(suras, parts, prev_sura, prev_aya,
                                                               prev_line, prev_line_width)
                            else:
                                suras, parts = updateLineData(suras, parts, sura, aya,
                                                               current_line, current_line_width)
                            current_line_width = 0
                        current_line = int(l)
                        aya_text_part = " ".join(aya_text.split()[skip_words:(skip_words+lines[l])])
                        if l == list(lines.keys())[-1]:
                            aya_text_part = aya_text_part + " \uFD3F{}\uFD3E".format(aya)
                        updateHtmlText(wd, aya_text_part, 0)
                        aya_part_width = getWidth(wd)
                        current_line_width = current_line_width + aya_part_width
                        parts.append({"l":int(l), "t":aya_text_part, "o":aya_part_width, "s": 1.0}) 
                        skip_words = skip_words + lines[l]
                    suras[sura-1]["ayas"].append({"p":page, "r":parts}) # New completed ayah
        f.close()
    print("Closing Chrome ..")
    wd.close()
    save_json(suras)
