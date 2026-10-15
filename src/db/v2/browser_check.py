"""Phase 1 browser check: can the DOM reproduce HarfBuzz's justified lines?

For each line, every character that carries justification features is wrapped
in its own <span style="font-feature-settings: ..."> inside the word. The
browser's word widths are compared with uharfbuzz's, and a screenshot is
taken so letter joining can be checked by eye.

Usage:
  python src/db/v2/browser_check.py FONT.otf DK_TEXT.ts PAGE OUT_DIR [--browser chromium]
Requires: playwright (with a browser installed), uharfbuzz.
"""
import argparse
import html
import json
import os
import re
import shutil
import sys

import uharfbuzz as hb
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(__file__))
import justify

FONT_PX = 40
LINE_WIDTH = 16400


def css_features(feats):
    return ", ".join(f'"{tag}" {value}' for tag, value in sorted(feats.items()))


def line_html(line, result, mode="char"):
    """Words as spans. mode "char": characters with features get nested spans;
    mode "word": features are keyed by word index and set on the word span."""
    out = []
    for wi, word in enumerate(line.words):
        if wi:
            sp = result.aya_spacing if line.spaces[word.start - 1] == "aya" else \
                result.simple_spacing
            out.append(f'<span class="sp" style="width:{sp / 1000:.4f}em"></span>')
        if mode == "word":
            feats = result.features.get(wi)
            style = f' style=\'font-feature-settings: {css_features(feats)}\'' if feats else ""
            out.append(f'<span class="w"{style}>{html.escape(word.text)}</span>')
            continue
        chunks, run = [], ""
        for idx in range(word.start, word.end + 1):
            ch, feats = line.text[idx], result.features.get(idx)
            if feats:
                if run:
                    chunks.append(html.escape(run))
                    run = ""
                chunks.append(f'<span style=\'font-feature-settings: {css_features(feats)}\'>'
                              f'{html.escape(ch)}</span>')
            else:
                run += ch
        if run:
            chunks.append(html.escape(run))
        out.append(f'<span class="w" data-i="{wi}">{"".join(chunks)}</span>')
    return "".join(out)


def build_page(font_file, lines):
    rows = "\n".join(f'<div class="line" data-l="{n}">{body}</div>'
                     for n, body in enumerate(lines))
    return f"""<!doctype html><meta charset="utf-8">
<style>
@font-face {{ font-family: dk; src: url("{font_file}"); }}
body {{ margin: 20px; background: #fffdf6; }}
.line {{ font: {FONT_PX}px/1.9 dk; direction: rtl; white-space: nowrap;
        width: fit-content; margin-left: auto; }}
.sp {{ display: inline-block; }}
</style>
{rows}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("font")
    ap.add_argument("dk_text")
    ap.add_argument("page", type=int)
    ap.add_argument("out_dir")
    ap.add_argument("--browser", default="chromium")
    ap.add_argument("--mode", choices=("char", "word"), default="char",
                    help="char: per-letter cvNN (justify_line); word: per-word jt/dc/kt")
    a = ap.parse_args()

    with open(a.font, "rb") as fh:
        font = hb.Font(hb.Face(fh.read()))
    with open(a.dk_text, encoding="utf-8") as fh:
        src = fh.read()
    pages = re.findall(r"\[\s*((?:'[^']*',?\s*)+)\]", src)
    texts = re.findall(r"'([^']*)'", pages[a.page - 1])

    lines, results, expected = [], [], []
    for text in texts:
        line = justify.analyze_line(text)
        if a.mode == "word":
            res = justify.justify_words(font, text, LINE_WIDTH)
            char_feats = justify.word_to_char_features(text, res.features)
        else:
            res = justify.justify_line(font, text, LINE_WIDTH, space_stretch=0.5,
                                       exhaustive=True)
            char_feats = res.features
        lines.append(line_html(line, res, a.mode))
        results.append(res)
        expected.append([justify.width(font, w.text, justify.to_hb_features(
            char_feats, w.start, w.start, w.end)) * FONT_PX / 1000 for w in line.words])

    os.makedirs(a.out_dir, exist_ok=True)
    shutil.copy(a.font, os.path.join(a.out_dir, "font.otf"))
    page_path = os.path.join(a.out_dir, "check.html")
    with open(page_path, "w", encoding="utf-8") as fh:
        fh.write(build_page("font.otf", lines))

    with sync_playwright() as pw:
        browser = getattr(pw, a.browser).launch()
        page = browser.new_page(viewport={"width": 760, "height": 600}, device_scale_factor=2)
        page.goto("file://" + os.path.abspath(page_path))
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(300)
        measured = page.evaluate("""() => [...document.querySelectorAll('.line')].map(l =>
            ({width: l.getBoundingClientRect().width,
              words: [...l.querySelectorAll('.w')].map(w => w.getBoundingClientRect().width)}))""")
        page.screenshot(path=os.path.join(a.out_dir, f"{a.browser}-{a.mode}.png"),
                        full_page=True)
        browser.close()

    report = []
    worst = 0.0
    for n, (m, exp, res) in enumerate(zip(measured, expected, results), start=1):
        diffs = [abs(b - e) for b, e in zip(m["words"], exp)]
        worst = max(worst, max(diffs))
        report.append({"line": n, "browser_px": round(m["width"], 2),
                       "harfbuzz_px": round(res.final_width * FONT_PX / 1000, 2),
                       "max_word_diff_px": round(max(diffs), 3),
                       "stretched": len(res.features)})
    print(json.dumps(report, indent=1, ensure_ascii=False))
    print(f"worst word width difference: {worst:.3f}px at {FONT_PX}px font size")


if __name__ == "__main__":
    main()
