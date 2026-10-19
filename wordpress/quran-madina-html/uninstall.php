<?php
/**
 * Remove the plugin's settings, and the copy of the library that versions before 2.1.4 could
 * save in the uploads folder.
 *
 * @package QuranMadinaHtml
 */

defined( 'WP_UNINSTALL_PLUGIN' ) || exit;

delete_option( 'qmhtml_settings' );
delete_option( 'qmh_settings' ); // the option's name before 2.1.4

$qmhtml_dir = trailingslashit( wp_upload_dir( null, false )['basedir'] ) . 'quran-madina-html/';
if ( is_dir( $qmhtml_dir ) ) {
	require_once ABSPATH . 'wp-admin/includes/file.php';
	if ( WP_Filesystem() ) {
		global $wp_filesystem;
		$wp_filesystem->delete( $qmhtml_dir, true );
	}
}
