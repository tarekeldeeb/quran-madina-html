<?php
/**
 * Test: copy the library to the site, then switch the site to it (IndoPak, size 20).
 *
 * @package QuranMadinaHtml
 */

$_SERVER['HTTP_HOST'] = 'localhost';
require $argv[1] . '/wp-load.php';
$qmh_result = qmh_download_library();
if ( is_wp_error( $qmh_result ) ) {
	fwrite( STDERR, 'copy failed: ' . $qmh_result->get_error_message() . "\n" );
	exit( 1 );
}
echo "ok   copied $qmh_result files of the library\n";
update_option( 'qmh_settings', qmh_sanitize_settings( array( 'layout' => 'IndoPak', 'font_size' => 20, 'source' => 'local' ) ) );
