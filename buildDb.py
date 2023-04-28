import sqlite3
import requests, os, tqdm
import json

TMP = "temp"
DB = "AyahInfo_1024.db"
TXT = "Uthmani.txt"

def query(query):
    conn = sqlite3.connect(os.path.join(TMP,DB))
    c = conn.cursor()
    c.execute(query)
    result = c.fetchall()
    c.close()
    return result

def get_aya_data(sura, ayah):
    result = query("select page_number, line_number, min_x, max_x from glyphs where sura_number={} and ayah_number={}".format(sura, ayah))
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

if __name__ == '__main__':
    try:
        os.mkdir(TMP)
        # Start with downloading the Glyph DB
        URL = "https://raw.githubusercontent.com/murtraja/quran-android-images-helper/master/static/databases/" + DB.lower()
        response = requests.get(URL)
        open(os.path.join(TMP,DB), "wb").write(response.content)
        print("Downloaded Quran DataBase")
        #
        # Then download the text from Tanzil.net
        txt_url = "https://tanzil.net/pub/download/index.php?marks=true&sajdah=true&rub=true&tatweel=true&quranType=uthmani&outType=txt-2&agree=true"
        req = requests.get(txt_url, allow_redirects=True)
        text = req.content
        open(os.path.join(TMP,TXT), "wb").write(text)
        print("Downloaded Quran Text file.")
    except OSError as error:
        print("Skipping download ..")
    json_header = '{"title": "مصحف المدينة الإصدار القديم - مجمع الملك فهد لطباعة المصحف الشريف",\
        "published": 1985,\
        "font": "https://fonts.googleapis.com/css?family=Amiri Quran"}'
    suras = []
    print("Processing ..")
    with tqdm.tqdm(total=os.path.getsize(os.path.join(TMP,TXT))) as pbar:
        with open(os.path.join(TMP,TXT), encoding="utf8") as f:
            for aya_line in f:
                pbar.update(len(aya_line.encode('utf-8')))
                tokens = aya_line.strip().split('|')
                if len(tokens) == 3:
                    sura, aya, aya_text = tokens
                    aya_text = aya_text
                    sura = int(sura)
                    aya = int(aya)
                    #Add a Sura
                    if len(suras)<sura:
                        suras.append({"name": get_surah_name(sura-1), "ayas":[]})
                    #Add an Aya
                    if aya>1:
                        prev_aya_data = ayah_data
                    else:
                        prev_aya_data = ""
                    ayah_data = get_aya_data(sura, aya)
                    ayah_data = list(filter(lambda a: a[3]-a[2] > 30, ayah_data))
                    page = ayah_data[0][0]
                    lines = {}
                    parts = [] # Break each ayah into parts/lines
                    for glyph in ayah_data:
                        if str(glyph[1]) not in lines:
                            lines.update({str(glyph[1]):1})
                        else:
                            lines[str(glyph[1])] = lines[str(glyph[1])] + 1
                    if aya==1 and sura!=1 and sura!=9:
                        skip_words = 4 #Skip Basmala from first aya
                    else:
                        skip_words = 0 
                    for l in lines.keys():
                        parts.append({"l":int(l), "t":" ".join(aya_text.split()[skip_words:(skip_words+lines[l])]), "o":20, "s": .23})
                        skip_words = skip_words + lines[l]
                    ## TODO: Find a way to calculate the stretching factor for each line
                    aya_obj = {"p":page, "r":parts}
                    suras[sura-1]["ayas"].append(aya_obj)
        f.close()
    j = json.loads(json_header)
    j.update({"suras":suras})
    json_file = open('Madina-Amiri.json', 'w', encoding="utf-8")
    json.dump(j, json_file, ensure_ascii = False, indent=2)
    json_file.close()
