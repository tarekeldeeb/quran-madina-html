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
$qmhtml_result = activate_plugin( 'quran-madina-html/quran-madina-html.php' );
if ( is_wp_error( $qmhtml_result ) ) {
	fwrite( STDERR, $qmhtml_result->get_error_message() . "\n" );
	exit( 1 );
}
delete_option( 'qmhtml_settings' );
delete_option( 'qmh_settings' );
$qmhtml_posts = array(
	'shortcodes' => "<p>Inline: [quran sura=\"112\" aya=\"1\"] in a sentence.</p>\n[quran sura=\"2\" aya=\"255\" highlight=\"5-8\" error=\"1\"]\n[quran sura=\"1\" aya=\"2-4\" headless=\"true\" letters=\"1:3 blink, 4:3+5 lapis\"]\n[quran sura=\"1\" aya=\"1\" onclick=\"alert(1)\" words=\"1:2<script>alert(2)</script>\"]",
	'block'      => '<!-- wp:quran-madina-html/quran {"sura":"2","aya":"1-5","highlight":"3"} /-->' . "\n" . '<!-- wp:quran-madina-html/quran {"page":"50","headless":true} /-->',
	'plain'      => 'No Quran here.',
);
foreach ( $qmhtml_posts as $qmhtml_slug => $qmhtml_content ) {
	$qmhtml_existing = get_page_by_path( $qmhtml_slug, OBJECT, 'post' );
	wp_insert_post(
		array(
			'ID'           => $qmhtml_existing ? $qmhtml_existing->ID : 0,
			'post_title'   => $qmhtml_slug,
			'post_name'    => $qmhtml_slug,
			'post_content' => $qmhtml_content,
			'post_status'  => 'publish',
		)
	);
}
echo "WordPress ready, plugin active\n";
