<?php
/**
 * Remove the plugin's settings and its copy of the library.
 *
 * @package QuranMadinaHtml
 */

defined( 'WP_UNINSTALL_PLUGIN' ) || exit;

delete_option( 'qmh_settings' );

$qmh_dir = trailingslashit( wp_upload_dir( null, false )['basedir'] ) . 'quran-madina-html/';
if ( is_dir( $qmh_dir ) ) {
	$qmh_items = new RecursiveIteratorIterator(
		new RecursiveDirectoryIterator( $qmh_dir, FilesystemIterator::SKIP_DOTS ),
		RecursiveIteratorIterator::CHILD_FIRST
	);
	foreach ( $qmh_items as $qmh_item ) {
		$qmh_item->isDir() ? rmdir( $qmh_item->getPathname() ) : unlink( $qmh_item->getPathname() ); // phpcs:ignore WordPress.WP.AlternativeFunctions
	}
	rmdir( $qmh_dir ); // phpcs:ignore WordPress.WP.AlternativeFunctions
}
