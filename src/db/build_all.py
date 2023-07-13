"""Iterates over build_db.py with multiple configurations
   Fonts covered: Uthman, Amiri Quran Colored
   Font Sizes: Multiple

   Returns:
        None
"""
from multiprocessing import Pool
from argparse import Namespace
from tqdm import tqdm
from build_db import run, DEFAULTS, CDN

amiri24 = DEFAULTS.copy()
amiri24['font_size']=24
amiri24['line_width']=400

uthman16 = DEFAULTS.copy()
uthman16['font_family'] = 'Uthman'
uthman16['font_url'] = CDN+"assets/fonts/UthmanTN_v2-0.woff2"

uthman14 = uthman16.copy()
uthman14['font_size'] = 14
uthman14['line_width'] = 240

configs = [ DEFAULTS, amiri24, uthman16, uthman14 ]

if __name__ == '__main__':
    #TODO: Fix the nested progress bar
    with Pool(4) as p:
        r = list(tqdm(p.imap(run, list(map(lambda x: Namespace(**x) ,configs))),
                      total=len(configs)))
