"""Iterates over build_db.py with multiple configurations
   Fonts covered: Uthman, Amiri Quran Colored
   Font Sizes: Multiple

   Builds are run sequentially, one config at a time, in this single process: each config
   drives its own single headless Chrome instance (opened and closed within DbBuilder.run()),
   so running configs in parallel would multiply that footprint per worker and risk OOM.
   Sequential execution also keeps only one tqdm progress bar live at a time, avoiding the
   corrupted/interleaved output multiple processes writing to the same terminal would cause.

   Returns:
        None
"""
from argparse import Namespace
from tqdm import tqdm
from build_db import DbBuilder, DEFAULTS

# font_url is stored relative (see DEFAULTS in build_db.py); the runtime resolves it against its
# `cdn` base and the builder makes it absolute only for width measurement.

hafs24 = DEFAULTS.copy()
hafs24['font_size'] = 24
hafs24['line_width'] = 410

amiri16 = DEFAULTS.copy()
amiri16['font_family'] = 'Amiri Quran'
amiri16['font_url'] = 'assets/fonts/AmiriQuran.woff2'
amiri16['line_width'] = 320

amiri24 = amiri16.copy()
amiri24['font_size'] = 24
amiri24['line_width'] = 410

amiri_color16 = DEFAULTS.copy()
amiri_color16['font_family'] = 'Amiri Quran Colored'
amiri_color16['font_url'] = 'assets/fonts/AmiriQuranColored.woff2'
amiri_color16['line_width'] = 330


amiri_color24 = amiri_color16.copy()
amiri_color24['font_size']=24
amiri_color24['line_width']=410

uthman16 = DEFAULTS.copy()
uthman16['font_family'] = 'Uthman'
uthman16['font_url'] = "assets/fonts/UthmanTN_v2-0.woff2"
uthman16['line_width'] = 330

uthman24 = uthman16.copy()
uthman24['font_size'] = 24
uthman24['line_width'] = 420

me_quran16 = DEFAULTS.copy()
me_quran16['font_family'] = 'me_quran'
me_quran16['font_url'] = "assets/fonts/me_quran-Regular.woff2"
me_quran16['line_width'] = 330

me_quran24 = me_quran16.copy()
me_quran24['font_size'] = 24
me_quran24['line_width'] = 420


configs = [ DEFAULTS, hafs24, amiri16, amiri24, uthman16, uthman24, amiri_color16, 
           amiri_color24, me_quran16, me_quran24]

if __name__ == '__main__':
    for config in tqdm(configs):
        DbBuilder.run(Namespace(**config))
