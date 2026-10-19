<?php
/**
 * Test setup: install WordPress, activate the plugin, create the test posts.
 *
 * @package QuranMadinaHtml
 */

define( 'WP_INSTALLING', true );
$_SERVER['HTTP_HOST'] = 'localhost';
require __DIR__ . '/wp-load.php';
require_once ABSPATH . 'wp-admin/includes/upgrade.php';
require_once ABSPATH . 'wp-admin/includes/plugin.php';
if ( ! is_blog_installed() ) {
	wp_install( 'QMH test', 'admin', 'admin@example.com', true, '', 'admin' );
}
$qmh_result = activate_plugin( 'quran-madina-html/quran-madina-html.php' );
if ( is_wp_error( $qmh_result ) ) {
	fwrite( STDERR, $qmh_result->get_error_message() . "\n" );
	exit( 1 );
}
delete_option( 'qmh_settings' );
$qmh_posts = array(
	'shortcodes' => "<p>Inline: [quran sura=\"112\" aya=\"1\"] in a sentence.</p>\n[quran sura=\"2\" aya=\"255\" highlight=\"5-8\" error=\"1\"]\n[quran sura=\"1\" aya=\"2-4\" headless=\"true\" letters=\"1:3 blink, 4:3+5 lapis\"]\n[quran sura=\"1\" aya=\"1\" onclick=\"alert(1)\" words=\"1:2<script>alert(2)</script>\"]",
	'block'      => '<!-- wp:quran-madina-html/quran {"sura":"2","aya":"1-5","highlight":"3"} /-->' . "\n" . '<!-- wp:quran-madina-html/quran {"page":"50","headless":true} /-->',
	'plain'      => 'No Quran here.',
);
foreach ( $qmh_posts as $qmh_slug => $qmh_content ) {
	$qmh_existing = get_page_by_path( $qmh_slug, OBJECT, 'post' );
	wp_insert_post(
		array(
			'ID'           => $qmh_existing ? $qmh_existing->ID : 0,
			'post_title'   => $qmh_slug,
			'post_name'    => $qmh_slug,
			'post_content' => $qmh_content,
			'post_status'  => 'publish',
		)
	);
}
echo "WordPress ready, plugin active\n";
