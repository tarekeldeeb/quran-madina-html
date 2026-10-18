"""Render the README animation (docs/assets/img/showcase.gif) from the current build.

    npm run build && npm run start      # serves the repo on localhost:8000
    python scripts/readme_gif.py

Each scene is one small page (written to demo/, removed afterwards) holding a tag, its title and
its code, captured at 2x pixel density. The blink scene steps the letter animation through its
cycle frame by frame. Needs Selenium + Chrome (as the render tests do) and Pillow.
"""
import html
import io
import os
import time

from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
BASE = "http://localhost:8000/demo/"
OUT = os.path.join(ROOT, "docs", "assets", "img", "showcase.gif")
WIDTH = 720              # GIF width in pixels (frames are captured at 2x, then scaled down)
HOLD_MS = 2400           # how long a still scene stays on screen
BLINK_PERIOD_MS = 1400   # .quran-madina-html-letter-blink in the CSS
BLINK_FRAMES = 14        # frames per blink cycle
BLINK_CYCLES = 2

PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<script src="../dist/quran-madina-html.js" data-cdn="../" data-layout="{layout}"
        data-font-size="{size}"></script>
<style>
  body {{ margin: 0; background: #fff; }}
  #stage {{ width: 640px; height: 440px; box-sizing: border-box; padding: 18px 22px;
           background: #fffdf8; color: #20201d; display: flex; flex-direction: column;
           font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }}
  .title {{ font-size: 17px; font-weight: 600; color: #00796b; }}
  .view {{ flex: 1; display: flex; align-items: center; justify-content: center; }}
  .code {{ margin: 0; padding: 9px 12px; background: #f1eee6; border-radius: 6px;
          font: 12.5px/1.45 ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace;
          color: #3d3a33; white-space: pre-wrap; direction: ltr; }}
  .code b {{ color: #00796b; font-weight: 600; }}
</style></head>
<body><div id="stage">
  <div class="title">{title}</div>
  <div class="view" dir="rtl">{tag}</div>
  <pre class="code">{code}</pre>
</div></body></html>"""


def tag(**attrs):
    """<quran-madina-html a="b" ...></quran-madina-html>"""
    joined = " ".join(f'{k}="{v}"' for k, v in attrs.items())
    return f"<quran-madina-html {joined}></quran-madina-html>"


def code(snippet, highlight=()):
    """The caption: the snippet, HTML-escaped, with the given substrings in bold."""
    out = html.escape(snippet)
    for part in highlight:
        escaped = html.escape(part)
        out = out.replace(escaped, f"<b>{escaped}</b>")
    return out


LETTERS = "1:3 blink, 4:3+5 lapis blink, 6:4 emerald blink"
SCENES = [
    # (title, layout, font size, tag attributes, caption, bold parts of the caption, blink?)
    ("A whole page, as real text", "1441H", 18, {"page": 1},
     '<quran-madina-html page="1"></quran-madina-html>', ['page="1"'], False),
    ("Any verse range", "1441H", 20, {"sura": 2, "aya": 255},
     '<quran-madina-html sura="2" aya="255"></quran-madina-html>', ['sura="2" aya="255"'], False),
    ("Highlight words, mark mistakes", "1441H", 20,
     {"sura": 2, "aya": 255, "highlight": "5-8", "error": 1},
     '<quran-madina-html sura="2" aya="255" highlight="5-8" error="1">',
     ['highlight="5-8"', 'error="1"'], False),
    ("Emphasise single letters, with an optional blink", "1441H", 34,
     {"sura": 1, "aya": "2-4", "highlight": 1, "error": 4, "letters": LETTERS},
     f'<quran-madina-html sura="1" aya="2-4" highlight="1" error="4"\n'
     f'  letters="{LETTERS}">', [f'letters="{LETTERS}"'], True),
    ("Any words, even across suras", "1441H", 20, {"sura": 1, "aya": 7, "words": "1-14"},
     '<quran-madina-html sura="1" aya="7" words="1-14">', ['words="1-14"'], False),
    ("Three prints: the old Madina Mushaf (1405H)", "1405H", 20, {"sura": 2, "aya": 255},
     '<script src="https://unpkg.com/quran-madina-html@2" data-layout="1405H">',
     ['data-layout="1405H"'], False),
    ("Three prints: the 15-line IndoPak", "IndoPak", 20, {"sura": 2, "aya": 255},
     '<script src="https://unpkg.com/quran-madina-html@2" data-layout="IndoPak">',
     ['data-layout="IndoPak"'], False),
]


def capture(driver, element):
    """The element as a PIL image."""
    return Image.open(io.BytesIO(element.screenshot_as_png)).convert("RGB")


def wait_rendered(driver):
    """Wait for the tag to render and its font to load."""
    for _ in range(100):
        ready = driver.execute_script(
            "var t = document.querySelector('quran-madina-html');"
            "return document.fonts.status === 'loaded' && t && t.getBoundingClientRect().height > 20;")
        if ready:
            break
        time.sleep(0.1)
    time.sleep(0.6)


def main():
    """Capture every scene and write the GIF."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--force-device-scale-factor=2")
    options.add_argument("--window-size=900,800")
    options.add_argument("--hide-scrollbars")
    driver = webdriver.Chrome(options=options)
    frames, durations = [], []
    path = os.path.join(ROOT, "demo", "_gif_scene.html")
    try:
        for title, layout, size, attrs, caption, bold, blink in SCENES:
            with open(path, "w", encoding="utf-8") as page:
                page.write(PAGE.format(layout=layout, size=size, title=html.escape(title),
                                       tag=tag(**attrs), code=code(caption, bold)))
            driver.get(BASE + "_gif_scene.html")
            wait_rendered(driver)
            stage = driver.find_element(By.ID, "stage")
            if not blink:
                frames.append(capture(driver, stage))
                durations.append(HOLD_MS)
                continue
            step = BLINK_PERIOD_MS / BLINK_FRAMES
            for _ in range(BLINK_CYCLES):
                for i in range(BLINK_FRAMES):
                    driver.execute_script(
                        "var t = arguments[0]; document.getAnimations().forEach(function(a){"
                        " a.pause(); a.currentTime = t; });", i * step)
                    time.sleep(0.15)
                    frames.append(capture(driver, stage))
                    durations.append(int(step))
            durations[-1] += 600  # a short rest before the next scene
    finally:
        driver.quit()
        if os.path.exists(path):
            os.remove(path)

    height = round(frames[0].height * WIDTH / frames[0].width)
    small = [f.resize((WIDTH, height), Image.LANCZOS) for f in frames]
    paletted = [f.quantize(colors=256, method=Image.Quantize.MAXCOVERAGE, dither=Image.Dither.NONE)
                for f in small]
    paletted[0].save(OUT, save_all=True, append_images=paletted[1:], duration=durations,
                     loop=0, optimize=True, disposal=1)
    print(f"{OUT}: {len(frames)} frames, {os.path.getsize(OUT) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
