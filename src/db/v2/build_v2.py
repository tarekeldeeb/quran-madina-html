"""Build a v2 DB: Tanzil text on a DigitalKhatt layout, justified by stretching
letters, plus the matching patched font.

    python src/db/v2/build_v2.py --layout 1441H \\
        --tanzil tmp_download/Uthmani.txt --dk-src path/to/digitalkhatt.org/ClientApp/src \\
        --out assets/db/v2

Steps:
  1. read Tanzil ("sura|aya|text" lines; aya 1 carries the basmala)
  2. tokens: words, aya numbers; pause marks attached to their word
  3. convert to the font's encoding (tanzil_encoding.py); 1441H takes the
     1441H print's pause marks
  4. place tokens on the page lines: the 1441H print's own line breaks
     (data/print-1441H-lines.json, extract_print_lines.py), else the
     DigitalKhatt layout text (layout_lines.py)
  5. justify every text line with HarfBuzz (justify.py), record per-word
     position features (font_patch.py), then write the patched font
  6. write the DB JSON (schema below) and a report

DB schema (version 2) — all widths in em, so any font size works:
  {
    "version": 2, "layout": "1441H", "title", "published",
    "font_family", "font_url", "line_width": <em>,
    "lines": [ [ {"k": "text"|"sura"|"bism", "w": <line width em>,
                  "z": <page font factor if < 1>, "s": [space widths, em of the line's
                  font; may be negative: boxes overlap, ink never), "x": <scaleX if < 1>,
                  "c": <scaleX of each word, aya numbers excluded, if < 1>} ... ] ... 604 pages ],
    "suras": [ {"name", "ayas": [ {"p": page, "r": [ {"l": line, "t": text,
                 "f": ["jp04=3,jp06=1" | "" per word of t]} ] } ] } ]
  }
  Each sura's ayas[0] is its title and ayas[1] its basmala (v1 invariant).
"""
# pylint: disable=too-many-locals,too-many-branches,too-many-statements
# pylint: disable=too-many-arguments,too-many-positional-arguments
# (one build routine kept in one piece; imports follow the sys.path setup)
# pylint: disable=wrong-import-position
import argparse
import json
import os
import re
import sys
import time
import unicodedata
from collections import defaultdict

import uharfbuzz as hb
from fontTools.ttLib import TTFont

sys.path.insert(0, os.path.dirname(__file__))
import font_patch
import justify
import layout_lines
import tanzil_encoding as enc

PAUSE_MARKS = set("ۖۗۘۙۚۛۜ")

LAYOUTS = {
    "1441H": {"text": "app/services/quran_text_madina.ts", "font": "assets/fonts/hb/madina.otf",
              "page_width": 16200, "widths": "newMadinaLineWidths", "pause_marks_from_print": True,
              "print_lines": "data/print-1441H-lines.json",
              "family": "QMH New Madina", "title": "مصحف المدينة - الإصدار الجديد ١٤٤١هـ",
              "published": 1441},
    "1405H": {"text": "app/services/quran_text_old_madinah.ts",
              "font": "assets/fonts/hb/oldmadina.otf",
              "page_width": 16400, "widths": "oldMadinaLineWidths", "pause_marks_from_print": False,
              "family": "QMH Old Madina", "title": "مصحف المدينة - الإصدار القديم ١٤٠٥هـ",
              "published": 1405},
    # IndoPak spelling differs from Tanzil's Uthmani text (no Tanzil IndoPak edition):
    # the layout's own text is used, numbered with the Kufan count (layout_lines.layout_tokens)
    "IndoPak": {"text": "app/services/quran_text_indopak_15.ts",
                "font": "assets/fonts/hb/indopak.otf",
                "page_width": 16400, "widths": "indoPak15LineWidths",
                "pause_marks_from_print": False,
                "text_source": "layout", "justifier": "simple", "stem": "IndoPak-15",
                "family": "QMH IndoPak", "title": "مصحف ١٥ سطرًا - الخط الهندي (IndoPak)",
                "published": None},
}
MARGIN, PAGE_WIDTH = 400, 17000          # DigitalKhatt page geometry (font units)


# ----------------------------------------------------------------- Tanzil
def read_tanzil(path):
    """[(sura, aya, text)] from a Tanzil 'sura|aya|text' file."""
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("|")
            if len(parts) == 3 and parts[0].isdigit():
                out.append((int(parts[0]), int(parts[1]), parts[2]))
    return out


def tanzil_from_v1_db(path):
    """Development fallback when tanzil.net is unreachable: rebuild Tanzil's
    aya texts from a v1 DB (removing its aya ornaments and build-inserted
    tatweels; Tanzil only uses a tatweel to carry a following mark)."""
    with open(path, encoding="utf-8") as fh:
        db = json.load(fh)
    out = []
    for si, sura in enumerate(db["suras"]):
        basmala = " ".join(p["t"] for p in sura["ayas"][1]["r"]).strip() if si not in (0, 8) else ""
        if si in (94, 96):           # v1 strips the idgham shadda of these basmalas
            basmala = "بّ" + basmala[1:]
        for ai, aya in enumerate(sura["ayas"][2:], start=1):
            text = " ".join(p["t"].strip() for p in aya["r"])
            text = "".join(c for i, c in enumerate(text) if c != "ـ" or (
                i + 1 < len(text) and unicodedata.category(text[i + 1]) == "Mn"))
            text = re.sub(r"\s*(﴿[٠-٩]+﴾|۝\d+)\s*$", "", text)
            if ai == 1 and basmala:
                text = basmala + " " + text
            out.append((si + 1, ai, text))
    return out


def tanzil_tokens(ayas):
    """Token stream + per-token (sura, aya, kind). Pause marks are attached to
    the previous word; each aya ends with its number token."""
    tokens, meta = [], []
    for sura, aya, text in ayas:
        words = text.split()
        n_bism = 4 if aya == 1 and sura not in (1, 9) else 0
        for i, w in enumerate(words):
            if w in PAUSE_MARKS and tokens and meta[-1][:2] == (sura, aya):
                tokens[-1] += w
                continue
            tokens.append(w)
            meta.append((sura, aya, "bism" if i < n_bism else "word"))
        tokens.append(enc.aya_number(aya))
        meta.append((sura, aya, "marker"))
    return tokens, meta


def convert(tokens, meta):
    """Font encoding; ۞ joins the next word, ۩ the previous one."""
    conv = [t if enc.is_marker(t) else enc.convert_word(t, enc.next_word(tokens, i))
            for i, t in enumerate(tokens)]
    out_t, out_m = [], []
    pending_rub = ""
    for t, m in zip(conv, meta):
        if t == enc.RUB_EL_HIZB:
            pending_rub = t
            continue
        if t == enc.SAJDA and out_t:
            out_t[-1] += t
            continue
        out_t.append(pending_rub + t)
        out_m.append(m)
        pending_rub = ""
    return out_t, out_m


# ----------------------------------------------------------------- layout
def line_width_ratios(dk_src, layout):
    """{(page, line): ratio} as DigitalKhatt's QuranTextService computes them."""
    with open(os.path.join(dk_src, "app/services/qurantext.service.ts"), encoding="utf-8") as fh:
        source = fh.read()
    block = re.search(LAYOUTS[layout]["widths"] + r" = new Map\(\[(.*?)\]\);", source,
                      re.DOTALL).group(1)
    ratios = {}
    for page, line, ratio in re.findall(r"\[(\d+) \* 15 \+ (\d+), ([\d.]+)\]", block):
        ratios[(int(page), int(line))] = float(ratio)
    if layout == "IndoPak":
        return ratios                  # DigitalKhatt sets no page 1-2 widths for IndoPak
    if layout == "1405H":
        r, first = 0.9, (0.5, 0.43)
    else:
        r, first = 0.95, (0.5, 0.45)
    for page in (1, 2):
        for line, f in ((2, first[page - 1]), (3, 0.7), (4, 0.9), (5, 1), (6, 0.9), (7, 0.7),
                        (8, 0.4)):
            ratios[(page, line)] = r * f
    return ratios


# ----------------------------------------------------------------- build
def build(args):
    """Build one layout's DB, patched font and woff2 into args.out."""
    cfg = LAYOUTS[args.layout]
    t0 = time.time()
    pages = layout_lines.load_dk_pages(os.path.join(args.dk_src, cfg["text"]))
    print_lines = None
    if cfg.get("text_source") == "layout":
        tokens, meta, lines = layout_lines.layout_tokens(pages)
        print(f"{len(tokens)} tokens from the layout text on {len(lines)} lines")
    else:
        if not (args.tanzil or args.from_v1_db):
            sys.exit(f"{args.layout} needs --tanzil (or --from-v1-db)")
        ayas = read_tanzil(args.tanzil) if args.tanzil else tanzil_from_v1_db(args.from_v1_db)
        tokens, meta = convert(*tanzil_tokens(ayas))
        # a Tanzil text downloaded without marks (marks=false) has only the 2 sakta signs
        bare = sum(1 for t in tokens if PAUSE_MARKS & set(t)) < 100
        if cfg["pause_marks_from_print"] or bare:
            ref = [w for p in pages for line in p if not line.startswith(layout_lines.SURA_PREFIX)
                   for w in line.split()]
            tokens, changed = enc.apply_pause_marks(tokens, ref, signs=bare)
            what = "pause marks, ۞ and ۩" if bare else "pause marks"
            print(f"{what} from the {args.layout} print: {changed} tokens"
                  + (" (the Tanzil text has none: downloaded without marks)" if bare else ""))
            if bare:
                n_rub = sum(t.count(enc.RUB_EL_HIZB) for t in tokens)
                n_sajda = sum(t.count(enc.SAJDA) for t in tokens)
                print(f"  ۞ {n_rub}, ۩ {n_sajda}")
        print_lines = cfg.get("print_lines") if args.line_breaks == "print" else None
        if print_lines:
            with open(os.path.join(os.path.dirname(__file__), print_lines), encoding="utf-8") as fh:
                print_pages = json.load(fh)["pages"]
            lines, problems = layout_lines.place_tokens_print(tokens, meta, pages, print_pages)
            print(f"{len(tokens)} tokens on {len(lines)} print lines; problems: {problems[:5]}")
            if problems:
                sys.exit("line placement failed")
        else:
            lines, unmatched = layout_lines.place_tokens(tokens, pages)
            print(f"{len(tokens)} tokens on {len(lines)} lines; unmatched: {len(unmatched)}")
    font_path = os.path.join(args.dk_src, cfg["font"])
    with open(font_path, "rb") as fh:
        font = hb.Font(hb.Face(fh.read()))
    ratios = line_width_ratios(args.dk_src, args.layout)
    full = cfg["page_width"] * (1 - 2 * MARGIN / PAGE_WIDTH)
    table, positions = font_patch.AlternateTable(), 1
    n_lines = defaultdict(int)
    for ln in lines:
        n_lines[ln.page] = max(n_lines[ln.page], ln.line)
    page_rows = [[None] * n_lines[p + 1] for p in range(len(n_lines))]

    natural_ratio = {}

    def width_ratio(ln):
        if print_lines:
            return ln.width or 1.0
        if cfg.get("text_source") == "layout" and ln.page <= 2 and ln.kind == "text":
            # IndoPak pages 1-2: DigitalKhatt gives no widths, and a full-width line of 3-4
            # words would gape; the lines keep their natural width (plus a little), centered
            key = (ln.page, ln.line)
            if key not in natural_ratio:
                text = " ".join(tokens[i] for i in ln.tokens)
                natural = justify.natural_width(font, text) * args.page_scale_min
                natural_ratio[key] = min(1.0, 1.04 * natural / full)
            return natural_ratio[key]
        return ratios.get((ln.page, ln.line), 1.0)
    word_css = {}                       # token index -> css string
    fit_stats = []
    # Page font factor (hybrid fitting): the page's text may shrink uniformly, by at
    # most PAGE_SCALE_MIN, so its widest line fits without distorting letters; the
    # rest of an overfull line is then squeezed (scaleX) by the justifier.
    page_scale = {}
    for ln in lines:
        if ln.kind != "text":
            continue
        desired = full * width_ratio(ln)
        natural = justify.natural_width(font, " ".join(tokens[i] for i in ln.tokens))
        page_scale[ln.page] = min(page_scale.get(ln.page, 1.0), desired / natural)
    page_scale = {p: max(args.page_scale_min, min(1.0, z)) for p, z in page_scale.items()}
    if args.fit == "print":
        # print model: the text keeps one size (the print's), lines are fitted
        # by the words themselves (fit_line_print)
        page_scale = {p: args.page_scale_min for p in page_scale}
    if args.page_scale == "global":
        # one factor for the whole mushaf: same text size on every page
        z_all = min(page_scale.values())
        page_scale = {p: z_all for p in page_scale}
    for ln in lines:
        ratio = width_ratio(ln)
        row = {"k": ln.kind, "w": round(full * ratio / 1000, 4)}
        page_rows[ln.page - 1][ln.line - 1] = row
        if ln.kind != "text":
            continue
        z = page_scale[ln.page]
        if z < 1:
            row["z"] = round(z, 4)
        text = " ".join(tokens[i] for i in ln.tokens)
        # justified at the page's font size: the line is 1/z wider in that font's units
        info = justify.analyze_line(text)
        if args.fit == "print":
            res = justify.fit_line_print(font, text, full * ratio / z, full / z,
                                         exhaustive=args.exhaustive,
                                         simple=cfg.get("justifier") == "simple")
            row["s"] = [round(sp / 1000, 4) for sp in res.dom_spaces()]
            if res.word_scale < 1:
                row["c"] = round(res.word_scale, 4)
            fit_stats.append((res.word_scale, res.x_scale))
        else:
            res = justify.justify_line(font, text, full * ratio / z,
                                       space_stretch=args.space_stretch,
                                       exhaustive=args.exhaustive)
            row["s"] = [round((res.aya_spacing if info.spaces[k] == "aya"
                               else res.simple_spacing) / 1000, 4)
                        for k in sorted(info.spaces)]
        if res.x_scale < 1:
            row["x"] = round(res.x_scale, 4)
        for wi, word in enumerate(info.words):
            css = {}
            css.update(getattr(res, 'word_features', {}).get(wi, {}))
            feats = justify.to_hb_features(res.features, word.start, word.start, word.end)
            if feats:
                reps = font_patch.word_replacements(font, word.text, feats)
                css.update(font_patch.css_for(reps, table))
                if reps:
                    positions = max(positions, max(p for p, _, _ in reps) + 1)
            if css:
                word_css[ln.tokens[wi]] = ",".join(f"{k}={v}" for k, v in sorted(css.items()))

    # suras / ayas / parts (v1 shape + per-word features)
    owner = {}
    for li, ln in enumerate(lines):
        for i in ln.tokens:
            owner[i] = li
    title_lines = [ln for ln in lines if ln.kind == "sura"]
    bism_lines = [ln for ln in lines if ln.kind == "bism"]
    by_aya = defaultdict(list)
    for i, (sura, aya, kind) in enumerate(meta):
        by_aya[(sura, aya, kind == "bism")].append(i)
    suras = []
    sura_names = [ln.text for ln in title_lines]
    bism_iter = iter(bism_lines)
    n_suras = max(m[0] for m in meta)
    for s in range(1, n_suras + 1):
        title = title_lines[s - 1]
        title_slot = {"p": title.page, "r": [{"l": title.line, "t": title.text, "f": []}]}
        if s == 1:
            ayas_json = [{"p": title.page, "r": [{"l": title.line, "t": "", "f": []}]}, title_slot]
        elif s == 9:
            ayas_json = [title_slot, {"p": title.page, "r": [{"l": title.line, "t": "", "f": []}]}]
        else:
            bl = next(bism_iter)
            ayas_json = [title_slot, {"p": bl.page, "r": [{"l": bl.line, "t": bl.text,
                                                            "f": [""] * len(bl.text.split())}]}]
        a = 1
        while (s, a, False) in by_aya:
            idxs = by_aya[(s, a, False)]
            parts, cur = [], {}
            for i in idxs:
                ln = lines[owner[i]]
                if not cur or cur["l"] != ln.line or cur["_p"] != ln.page:
                    cur = {"_p": ln.page, "l": ln.line, "t": [], "f": []}
                    parts.append(cur)
                cur["t"].append(tokens[i])
                cur["f"].append(word_css.get(i, ""))
            ayas_json.append({"p": parts[0]["_p"], "r": [
                {"l": p["l"], "t": " ".join(p["t"]), "f": p["f"]} for p in parts]})
            a += 1
        suras.append({"name": sura_names[s - 1], "ayas": ayas_json})

    os.makedirs(args.out, exist_ok=True)
    stem = f"{os.path.splitext(os.path.basename(cfg['font']))[0]}-qmh"
    font_out = os.path.join(args.out, stem + ".otf")
    font_patch.patch_font(font_path, font_out, table, positions, cfg["family"])
    font_name = stem + ".woff2"                     # what the browser loads
    woff2 = TTFont(font_out)
    woff2.flavor = "woff2"
    woff2.save(os.path.join(args.out, font_name))
    db = {"version": 2, "layout": args.layout, "title": cfg["title"], "published": cfg["published"],
          "font_family": cfg["family"], "font_url": f"assets/db/v2/{font_name}",
          "line_width": round(full / 1000, 4), "lines": page_rows, "suras": suras}
    db_path = os.path.join(args.out, cfg.get("stem", f"Madina-{args.layout}") + ".json")
    with open(db_path, "w", encoding="utf-8") as fh:
        json.dump(db, fh, ensure_ascii=False, separators=(",", ":"))
    if fit_stats:
        cs = sorted(c for c, _ in fit_stats)
        print(f"lines {len(cs)}: narrower words {sum(c < 1 for c in cs)} "
              f"(<0.9: {sum(c < 0.9 for c in cs)}, at {justify.MIN_WORD_SCALE}: "
              f"{sum(c <= justify.MIN_WORD_SCALE for c in cs)}), "
              f"line scaleX {sum(x < 1 for _, x in fit_stats)}")
    stretched = sum(1 for v in word_css.values() if "jp" in v)
    print(f"stretched words {stretched}, jp01..jp{positions:02d}, "
          f"{sum(len(v) for v in table.alts.values())} variants")
    print(f"wrote {db_path} ({os.path.getsize(db_path) // 1024} KB) and {font_out} "
          f"in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n", maxsplit=1)[0])
    ap.add_argument("--layout", choices=sorted(LAYOUTS), default="1441H")
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--tanzil", help="Tanzil Uthmani 'sura|aya|text' file")
    src.add_argument("--from-v1-db", help="development fallback: a v1 JSON DB")
    ap.add_argument("--dk-src", required=True, help="digitalkhatt.org/ClientApp/src")
    ap.add_argument("--out", default="assets/db/v2")
    ap.add_argument("--space-stretch", type=float, default=0.5)
    ap.add_argument("--exhaustive", action=argparse.BooleanOptionalAction, default=True)
    ap.add_argument("--line-breaks", choices=("print", "dk"), default="print",
                    help="print: the KFGQPC print's line breaks where the layout has them "
                         "(1441H); dk: the DigitalKhatt text's")
    ap.add_argument("--fit", choices=("print", "dk"), default="print",
                    help="print: fixed print-like gaps, words stretch or narrow (justify."
                         "fit_line_print); dk: DigitalKhatt's spaces-first justifier + shrink")
    ap.add_argument("--page-scale-min", type=float, default=0.92,
                    help="smallest font factor before lines get squeezed (1 = never)")
    ap.add_argument("--page-scale", choices=("global", "page"), default="global",
                    help="global: one factor for all pages (consistent size); page: per page")
    build(ap.parse_args())
