"""Split a monolithic Madina DB JSON into a small manifest + 30 juz' shards for lazy loading.

Output layout (under <out>/<db-stem>/):
  manifest.json   header + per-sura {name, aya-count} skeleton + 30 juz' start points
  juz-01.json ... juz-30.json   the render data (ayas) belonging to each juz'

The manifest's `juz` table is the (sura,aya)->juz and page->juz mapper source used by the runtime.
Shards carry each aya's (suraIdx, ayaIdx) so the runtime can merge partial suras into place.

Usage: python src/db/shard_db.py assets/db/Madina05-me_quran-16px.json <out_dir>
"""
import json
import os
import sys

# Standard juz' start points, 1-based (sura, aya).
JUZ_STARTS_1B = [
    (1, 1), (2, 142), (2, 253), (3, 93), (4, 24), (4, 148), (5, 82), (6, 111),
    (7, 88), (8, 41), (9, 93), (11, 6), (12, 53), (15, 1), (17, 1), (18, 75),
    (21, 1), (23, 1), (25, 21), (27, 56), (29, 46), (33, 31), (36, 28), (39, 32),
    (41, 47), (46, 1), (51, 31), (58, 1), (67, 1), (78, 1),
]
# Internal indexing: sura is 0-based; each sura's ayas[] has 2 decoration slots (0=title,
# 1=name/basmala) before real aya 1 at index 2, so real aya A lives at index A+1.
JUZ_STARTS = [(s - 1, a + 1) for (s, a) in JUZ_STARTS_1B]


def juz_of(sura0, aya_idx):
    """Juz' (0-based 0..29) that an aya belongs to. Decoration slots (idx 0/1) inherit aya 1's
    juz' so a sura that opens a juz' keeps its title/basmala in the new juz'."""
    pos = (sura0, max(aya_idx, 2))
    j = 0
    for k, start in enumerate(JUZ_STARTS):
        if start <= pos:
            j = k
        else:
            break
    return j


def main():
    src, out_root = sys.argv[1], sys.argv[2]
    db = json.load(open(src, encoding="utf8"))
    stem = os.path.splitext(os.path.basename(src))[0]
    out = os.path.join(out_root, stem)
    os.makedirs(out, exist_ok=True)

    shards = [[] for _ in range(30)]          # shards[j] = list of [suraIdx, ayaIdx, page, parts]
    juz_start_page = [None] * 30
    for s0, sura in enumerate(db["suras"]):
        for ai, aya in enumerate(sura["ayas"]):
            j = juz_of(s0, ai)
            shards[j].append([s0, ai, aya["p"], aya["r"]])
            # first (min) page seen opening each juz'
            if juz_start_page[j] is None:
                juz_start_page[j] = aya["p"]

    manifest = {k: db[k] for k in
                ("title", "published", "font_family", "font_url", "font_size", "line_width")}
    manifest["suras"] = [[s["name"], len(s["ayas"])] for s in db["suras"]]
    manifest["juz"] = [[JUZ_STARTS[j][0], JUZ_STARTS[j][1], juz_start_page[j]] for j in range(30)]

    # Page -> [sura_from, aya_from, sura_to, aya_to], replicating the runtime's page scan exactly so
    # the sharded lookup returns identical boundaries. Lets the page render skip scanning (which is
    # impossible once ayas load lazily) and pick the shards it needs.
    suras = db["suras"]
    last_page = max(a["p"] for s in suras for a in s["ayas"])
    pages = []
    for page in range(1, last_page + 1):
        sura_from = 0
        while suras[sura_from]["ayas"][-1]["p"] < page:
            sura_from += 1
        sura_to = sura_from
        while sura_to < len(suras) and suras[sura_to]["ayas"][0]["p"] <= page:
            sura_to += 1
        sura_to -= 1
        aya_from = 0
        while suras[sura_from]["ayas"][aya_from]["p"] < page:
            aya_from += 1
        aya_to = len(suras[sura_to]["ayas"]) - 1
        while suras[sura_to]["ayas"][aya_to]["p"] > page:
            aya_to -= 1
        pages.append([sura_from, aya_from, sura_to, aya_to])
    manifest["pages"] = pages

    def dump(obj, path):
        with open(path, "w", encoding="utf8") as f:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        return os.path.getsize(path)

    total = dump(manifest, os.path.join(out, "manifest.json"))
    for j in range(30):
        total += dump({"j": j, "d": shards[j]}, os.path.join(out, f"juz-{j + 1:02d}.json"))

    # ---- lossless round-trip check: reassemble the original suras from manifest + shards ----
    rebuilt = [{"name": name, "ayas": [None] * n} for name, n in manifest["suras"]]
    for j in range(30):
        shard = json.load(open(os.path.join(out, f"juz-{j + 1:02d}.json"), encoding="utf8"))
        for s0, ai, page, parts in shard["d"]:
            rebuilt[s0]["ayas"][ai] = {"p": page, "r": parts}
    assert rebuilt == db["suras"], "round-trip mismatch!"
    print(f"{stem}: manifest + 30 shards, reassembles losslessly. total on disk={total} bytes")


if __name__ == "__main__":
    main()
