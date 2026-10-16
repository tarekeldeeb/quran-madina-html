"""Retake the README screenshots (demo/img/*.png) from the current build.

    npm run build && npm run start      # serves the repo on localhost:8000
    python scripts/readme_screenshots.py

Each shot is one small page (written to demo/, removed afterwards) holding the tag, captured at
2x pixel density. Needs Selenium + Chrome (as the render tests do).
"""
import base64
import os
import time

from selenium import webdriver

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
BASE = "http://localhost:8000/demo/"
PAGE = """<!DOCTYPE html>
<html dir="rtl" lang="ar"><head><meta charset="utf-8">
<script src="../dist/quran-madina-html.js" data-cdn="../" data-layout="{layout}"
        data-font-size="{size}"></script>
<style>
  body {{ margin: 0; background: #fff; color: #20201d; }}
  #shot {{ display: inline-block; padding: 8px; background: #fff; }}
  {css}
</style></head>
<body><div id="shot">{tag}</div></body></html>"""



def tag(**attrs):
    """<quran-madina-html a="b" ...></quran-madina-html>"""
    joined = " ".join(f'{k}="{v}"' for k, v in attrs.items())
    return f"<quran-madina-html {joined}></quran-madina-html>"


SHOTS = [
    # (file, layout, font size, tag, extra css)
    ("v2-p50-1441H", "1441H", 22, tag(page=50, headless="true"), ""),
    ("v2-p50-1405H", "1405H", 22, tag(page=50, headless="true"), ""),
    ("v2-p50-IndoPak", "IndoPak", 22, tag(page=50, headless="true"), ""),
    ("p106-1405H", "1405H", 22, tag(page=106, headless="true"), ""),
    ("verse-default", "1441H", 22, tag(sura=5, aya="1-2"), ""),
    ("verse-headless", "1441H", 22, tag(sura=5, aya="1-2", headless="true"), ""),
    ("words-inline", "1441H", 22, tag(sura=1, aya=1, words="1:2"), ""),
    ("words-multiline", "1441H", 22, tag(sura=1, aya=7, words="1-14"), ""),
    ("highlight", "1441H", 22, tag(sura=1, aya=1, highlight="2-3"), ""),
    ("letters", "1441H", 22,
     tag(sura=1, aya="2-4", headless="true", highlight="1", error="4",
         letters="1:3, 4:3+5 lapis, 6:4 emerald"),
     # the still frame: the blink only adds a halo, so this is how print and screenshots look
     ".quran-madina-html-letter { animation: none !important; }"),
]


def main():
    """Write each shot's page, load it, capture #shot."""
    opts = webdriver.ChromeOptions()
    for arg in ("--headless", "--no-sandbox", "--disable-dev-shm-usage", "--hide-scrollbars",
                "--window-size=900,1400"):
        opts.add_argument(arg)
    driver = webdriver.Chrome(options=opts)
    try:
        for name, layout, size, html, css in SHOTS:
            page = os.path.join(ROOT, "demo", f"_shot-{name}.html")
            with open(page, "w", encoding="utf-8") as fh:
                fh.write(PAGE.format(layout=layout, size=size, tag=html, css=css))
            try:
                driver.get(BASE + os.path.basename(page))
                for _ in range(80):              # rendered and the font loaded
                    if driver.execute_script(
                            "return document.querySelectorAll('quran-madina-html-line').length > 0"
                            " && document.fonts.status === 'loaded'"):
                        break
                    time.sleep(0.25)
                time.sleep(1.0)
                out = os.path.join(ROOT, "demo", "img", name + ".png")
                rect = driver.execute_script(
                    "var r = document.getElementById('shot').getBoundingClientRect();"
                    "return {x: r.left + scrollX, y: r.top + scrollY,"
                    "        width: r.width, height: r.height}")
                png = driver.execute_cdp_cmd("Page.captureScreenshot", {
                    "clip": dict(rect, scale=2), "captureBeyondViewport": True})["data"]
                with open(out, "wb") as fh:
                    fh.write(base64.b64decode(png))
                print("wrote", os.path.relpath(out, ROOT))
            finally:
                os.remove(page)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
