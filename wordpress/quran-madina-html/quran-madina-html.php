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
 * License:           Waqf General Public License 2.0
 * License URI:       https://github.com/ojuba-org/waqf/tree/master/2.0
 * Text Domain:       quran-madina-html
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
