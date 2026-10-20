#!/usr/bin/env bash
# Builds the WordPress plugin: copies the library (script, CSS, images, and every print's texts and
# fonts) into wordpress/quran-madina-html/library/, and with --zip also writes the plugin zip.
#   wordpress/build.sh [--zip out.zip]
# WordPress.org plugins may not load scripts from a CDN, so the plugin carries its own copy.
# Run `npm run build` first (dist/ is generated).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN="$ROOT/wordpress/quran-madina-html"
LIB="$PLUGIN/library"

for f in dist/quran-madina-html.js dist/quran-madina-html.css; do
  [ -f "$ROOT/$f" ] || { echo "$f is missing: run npm run build first" >&2; exit 1; }
done
rm -rf "$LIB"
mkdir -p "$LIB/dist" "$LIB/assets/db/v2"
cp "$ROOT/dist/quran-madina-html.js" "$ROOT/dist/quran-madina-html.css" "$LIB/dist/"
cp -r "$ROOT/assets/img" "$LIB/assets/"
cp "$ROOT"/assets/db/v2/*-qmh.woff2 "$LIB/assets/db/v2/"
for stem in Madina-1441H Madina-1405H IndoPak-15; do
  cp -r "$ROOT/assets/db/v2/$stem" "$LIB/assets/db/v2/"
done
echo "library: $(find "$LIB" -type f | wc -l) files, $(du -sh "$LIB" | cut -f1)"

if [ "${1:-}" = "--zip" ]; then
  out="$(cd "$(dirname "${2:?--zip needs a file name}")" && pwd)/$(basename "$2")"
  rm -f "$out"
  (cd "$ROOT/wordpress" && zip -qr "$out" quran-madina-html -x 'quran-madina-html/tests/*')
  echo "zip: $out ($(du -h "$out" | cut -f1))"
fi
