<?php
/**
 * Plugin Name:       Quran Madina Html
 * Plugin URI:        https://tarekeldeeb.github.io/quran-madina-html/docs/getting-started/wordpress/
 * Description:       Quran pages that look like the printed Madina Mushaf, as real text: a [quran] shortcode and a Quran block for pages, verses, highlighted words and emphasised letters.
 * Version:           2.1.1
 * Requires at least: 6.3
 * Requires PHP:      7.4
 * Author:            Tarek Eldeeb
 * Author URI:        https://github.com/tarekeldeeb
 * License:           GPLv2 or later, or Waqf General Public License 2.0
 * License URI:       https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain:       quran-madina-html
 *
 * Dual licensed: GPL-2.0-or-later, or the "Waqf" General Public License 2.0, at your choice.
 * See LICENSE.txt. The library it loads stays under the Waqf General Public License 2.0.
 *
 * @package QuranMadinaHtml
 */

defined( 'ABSPATH' ) || exit;

/** This plugin's version, which is also the quran-madina-html library version it loads. */
define( 'QMH_VERSION', '2.1.1' );
define( 'QMH_FILE', __FILE__ );

require_once __DIR__ . '/includes/render.php';
require_once __DIR__ . '/includes/local-copy.php';
require_once __DIR__ . '/includes/settings.php';
