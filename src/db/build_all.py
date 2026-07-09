"""Iterates over build_db.py with multiple configurations
   Fonts covered: Uthman, Amiri Quran Colored
   Font Sizes: Multiple

   Builds are run sequentially, one config at a time, in this single process: each config
   drives its own single headless Chrome instance (opened and closed within DbBuilder.run()),
   so running configs in parallel would multiply that footprint per worker and risk OOM.
   Sequential execution also keeps only one rich Progress/Live display active at a time (only one
   may ever be live in a terminal), which is shared across all configs here so the whole build
   renders as one coherent multi-line display instead of each config fighting over the terminal.

   Returns:
        None
"""
from argparse import Namespace
from rich.progress import Progress
from build_db import DbBuilder, DEFAULTS

# font_url is stored relative (see DEFAULTS in build_db.py); the runtime resolves it against its
# `cdn` base and the builder makes it absolute only for width measurement.

hafs24 = DEFAULTS.copy()
hafs24['font_size'] = 24
hafs24['line_width'] = 410

amiri16 = DEFAULTS.copy()
amiri16['font_family'] = 'Amiri Quran'
amiri16['font_url'] = 'assets/fonts/AmiriQuran.woff2'
amiri16['line_width'] = 270

amiri24 = amiri16.copy()
amiri24['font_size'] = 24
amiri24['line_width'] = 410

amiri_color16 = DEFAULTS.copy()
amiri_color16['font_family'] = 'Amiri Quran Colored'
amiri_color16['font_url'] = 'assets/fonts/AmiriQuranColored.woff2'
amiri_color16['line_width'] = 270


amiri_color24 = amiri_color16.copy()
amiri_color24['font_size']=24
amiri_color24['line_width']=410

uthman16 = DEFAULTS.copy()
uthman16['font_family'] = 'Uthman'
uthman16['font_url'] = "assets/fonts/UthmanTN_v2-0.woff2"
uthman16['line_width'] = 270

uthman24 = uthman16.copy()
uthman24['font_size'] = 24
uthman24['line_width'] = 400

me_quran16 = DEFAULTS.copy()
me_quran16['font_family'] = 'me_quran'
me_quran16['font_url'] = "assets/fonts/me_quran-Regular.woff2"
me_quran16['line_width'] = 300

me_quran24 = me_quran16.copy()
me_quran24['font_size'] = 24
me_quran24['line_width'] = 450


configs = [ DEFAULTS, hafs24, amiri16, amiri24, uthman16, uthman24, amiri_color16, 
           amiri_color24, me_quran16, me_quran24]

if __name__ == '__main__':
    with Progress(*DbBuilder.PROGRESS_COLUMNS, console=DbBuilder.console) as progress:
        overall = progress.add_task("Fonts built", total=len(configs))
        for config in configs:
            progress.update(overall,
                description=f"Fonts built ({config['font_family']} {config['font_size']}px)")
            DbBuilder.run(Namespace(**config), progress=progress)
            progress.update(overall, advance=1)
        progress.update(overall, description="Fonts built")
