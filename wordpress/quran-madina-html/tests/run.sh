#!/usr/bin/env bash
# Runs the plugin in a real WordPress (SQLite, PHP's built-in server) and checks what it outputs.
#   wordpress/quran-madina-html/tests/run.sh [work-dir]
# Needs php (with pdo_sqlite, phar, zlib), git and curl. Downloads WordPress and the SQLite
# plugin from GitHub, and the library from npm (for the "copy to this site" check).
set -euo pipefail
PLUGIN="$(cd "$(dirname "$0")/.." && pwd)"
WORK="${1:-$(mktemp -d)}"
PORT="${QMH_PORT:-8686}"
WP="$WORK/wp"
SITE="http://localhost:$PORT"

if [ ! -f "$WP/wp-settings.php" ]; then
  tag=$(git ls-remote --tags https://github.com/WordPress/WordPress.git \
        | grep -oE 'refs/tags/[0-9]+\.[0-9]+(\.[0-9]+)?$' | sed 's#refs/tags/##' | sort -V | tail -1)
  echo "WordPress $tag"
  git clone -q --depth 1 --branch "$tag" https://github.com/WordPress/WordPress.git "$WP"
  sqlite=$(git ls-remote --tags https://github.com/WordPress/sqlite-database-integration.git \
        | grep -oE 'refs/tags/v?[0-9.]+$' | sed 's#refs/tags/##' | sort -V | tail -1)
  git clone -q --depth 1 --branch "$sqlite" https://github.com/WordPress/sqlite-database-integration.git "$WORK/sqlite"
  P="$WP/wp-content/plugins/sqlite-database-integration"
  cp -r "$WORK/sqlite/packages/plugin-sqlite-database-integration" "$P"
  rm -rf "$P/wp-includes/database"
  cp -r "$WORK/sqlite/packages/mysql-on-sqlite/src" "$P/wp-includes/database"
  sed -e "s#{SQLITE_IMPLEMENTATION_FOLDER_PATH}#$P#" -e "s#{SQLITE_PLUGIN}#sqlite-database-integration/load.php#g" \
      "$P/db.copy" > "$WP/wp-content/db.php"
fi
cat > "$WP/wp-config.php" <<CONFIG
<?php
define( 'DB_NAME', 'wp' ); define( 'DB_USER', '' ); define( 'DB_PASSWORD', '' ); define( 'DB_HOST', '' );
define( 'DB_CHARSET', 'utf8' ); define( 'DB_COLLATE', '' );
define( 'DB_DIR', __DIR__ . '/wp-content/database/' ); define( 'DB_FILE', '.ht.sqlite' );
foreach ( array( 'AUTH_KEY', 'SECURE_AUTH_KEY', 'LOGGED_IN_KEY', 'NONCE_KEY', 'AUTH_SALT', 'SECURE_AUTH_SALT', 'LOGGED_IN_SALT', 'NONCE_SALT' ) as \$k ) { define( \$k, 'test' ); }
define( 'WP_DEBUG', true ); define( 'WP_DEBUG_LOG', true ); define( 'WP_DEBUG_DISPLAY', false );
define( 'WP_HOME', '$SITE' ); define( 'WP_SITEURL', '$SITE' );
\$table_prefix = 'wp_';
if ( ! defined( 'ABSPATH' ) ) { define( 'ABSPATH', __DIR__ . '/' ); }
require_once ABSPATH . 'wp-settings.php';
CONFIG
ln -sfn "$PLUGIN" "$WP/wp-content/plugins/quran-madina-html"
if [ -n "${QMH_CA_BUNDLE:-}" ]; then  # behind a proxy with its own CA: trust it for downloads
  mkdir -p "$WP/wp-content/mu-plugins"
  echo "<?php add_filter( 'http_request_args', function ( \$a ) { \$a['sslcertificates'] = '$QMH_CA_BUNDLE'; return \$a; } );" \
    > "$WP/wp-content/mu-plugins/test-ca.php"
fi
cp "$PLUGIN/tests/setup.php" "$WP/qmh-test-setup.php"
php "$WP/qmh-test-setup.php"

php -S "localhost:$PORT" -t "$WP" >/dev/null 2>&1 &
SERVER=$!
trap 'kill $SERVER' EXIT
sleep 2

fail=0
page() { curl -fsS "$SITE/?name=$1"; }
expect() {  # expect <post slug> <grep -E pattern> <description>
  local html; html=$(page "$1")
  if grep -qE "$2" <<<"$html"; then echo "ok   $3"; else echo "FAIL $3"; fail=1; fi
}
reject() {
  local html; html=$(page "$1")
  if grep -qE "$2" <<<"$html"; then
    echo "FAIL $3:"; grep -oE ".{0,60}($2).{0,40}" <<<"$html" | head -3; fail=1
  else echo "ok   $3"; fi
}
expect shortcodes '<quran-madina-html sura="2" aya="255" highlight="5-8" error="1">' "shortcode with marks"
expect shortcodes '<quran-madina-html sura="112" aya="1">' "inline shortcode"
expect shortcodes 'letters="1:3 blink, 4:3\+5 lapis" headless="true"' "letters and headless"
reject shortcodes 'onclick|alert' "unknown attributes and scripts are dropped"
expect shortcodes '<quran-madina-html sura="1" aya="1"></quran-madina-html>' "a malformed range is left out"
expect shortcodes '<script[^>]*data-cdn="https://unpkg.com/quran-madina-html@[0-9.]+/"[^>]*data-layout="1441H"' "library script with its options"
expect block '<quran-madina-html sura="2" aya="1-5" highlight="3">' "block"
expect block '<quran-madina-html page="50" headless="true">' "block page wins over the default verse"
reject plain 'quran-madina-html' "no library on posts without Quran text"

php "$PLUGIN/tests/copy.php" "$WP"
expect shortcodes "<script[^>]*data-cdn=\"$SITE/wp-content/uploads/quran-madina-html/[0-9.]+/\"[^>]*data-layout=\"IndoPak\"[^>]*data-font-size=\"20\"" "library from this site, with the saved settings"
html=$(page shortcodes)
url=$(grep -oE "$SITE/wp-content/uploads/quran-madina-html/[0-9.]+/" <<<"$html" | head -1)
for f in dist/quran-madina-html.js dist/quran-madina-html.css assets/db/v2/IndoPak-15/manifest.json assets/db/v2/indopak-qmh.woff2; do
  if curl -fsS -o /dev/null "$url$f"; then echo "ok   serves $f"; else echo "FAIL serves $f"; fail=1; fi
done

if grep -iE 'qmh|quran-madina' "$WP/wp-content/debug.log" 2>/dev/null; then echo "FAIL PHP notices from the plugin"; fail=1; fi
exit $fail
