"""Iterates over build_db.py with multiple configurations
   Fonts covered: Uthman, Amiri Quran Colored
   Font Sizes: Multiple

   Returns:
        None
"""
from multiprocessing import Pool
from argparse import Namespace
from tqdm import tqdm
from build_db import DbBuilder, DEFAULTS, CDN

amiri16 = DEFAULTS.copy()
amiri16['font_family'] = 'Amiri Quran'
amiri16['font_url'] = CDN+'assets/fonts/AmiriQuran.woff2'

amiri_color16 = DEFAULTS.copy()
amiri_color16['font_family'] = 'Amiri Quran Colored'
amiri_color16['font_url'] = CDN+'assets/fonts/AmiriQuranColored.woff2'

amiri_color24 = amiri_color16.copy()
amiri_color24['font_size']=24
amiri_color24['line_width']=410

uthman16 = DEFAULTS.copy()
uthman16['font_family'] = 'Uthman'
uthman16['font_url'] = CDN+"assets/fonts/UthmanTN_v2-0.woff2"

configs = [ DEFAULTS, amiri16, uthman16, amiri_color16, amiri_color24]

if __name__ == '__main__':
    with Pool(4) as p:
        r = list(tqdm(p.imap(DbBuilder.run, list(map(lambda x: Namespace(**x) ,configs))),
                      total=len(configs)))
