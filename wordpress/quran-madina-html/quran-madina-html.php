<?php
/**
 * Plugin Name:       Quran Madina Html
 * Plugin URI:        https://tarekeldeeb.github.io/quran-madina-html/docs/getting-started/wordpress/
 * Description:       Quran pages that look like the printed Madina Mushaf, as real text: a [quran] shortcode and a Quran block for pages, verses, highlighted words and emphasised letters.
 * Version:           2.1.3
 * Requires at least: 6.3
 * Requires PHP:      7.4
 * Author:            Tarek Eldeeb
 * Author URI:        https://github.com/tarekeldeeb
 * License:           GPLv2 or later
 * License URI:       https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain:       quran-madina-html
 *
 * Dual licensed: GPL-2.0-or-later, or the "Waqf" General Public License 2.0, at your choice.
 * This covers the copy of the quran-madina-html library in library/; see LICENSE.txt.
 *
 * @package QuranMadinaHtml
 */

defined( 'ABSPATH' ) || exit;

/** This plugin's version, which is also the version of the quran-madina-html library it carries. */
define( 'QMHTML_VERSION', '2.1.3' );
define( 'QMHTML_FILE', __FILE__ );

require_once __DIR__ . '/includes/render.php';
require_once __DIR__ . '/includes/settings.php';
