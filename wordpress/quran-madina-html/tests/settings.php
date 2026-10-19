<?php
/**
 * Test: save settings the way the settings page does.
 *
 * @package QuranMadinaHtml
 */

$_SERVER['HTTP_HOST'] = 'localhost';
require $argv[1] . '/wp-load.php';

// Settings saved by 2.1.x, under the old option name, still apply.
update_option( 'qmh_settings', array( 'layout' => '1405H', 'font_size' => 18, 'source' => 'local' ) );
if ( array( 'layout' => '1405H', 'font_size' => 18 ) !== qmhtml_settings() ) {
	fwrite( STDERR, 'old settings not migrated: ' . wp_json_encode( qmhtml_settings() ) . "\n" );
	exit( 1 );
}
update_option( 'qmhtml_settings', qmhtml_sanitize_settings( array( 'layout' => 'IndoPak', 'font_size' => '20', 'source' => 'unpkg' ) ) );
$qmhtml_saved = get_option( 'qmhtml_settings' );
if ( array( 'layout' => 'IndoPak', 'font_size' => 20.0 ) !== $qmhtml_saved ) {
	fwrite( STDERR, 'unexpected settings: ' . wp_json_encode( $qmhtml_saved ) . "\n" );
	exit( 1 );
}
