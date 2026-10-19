<?php
/**
 * A copy of the library on this site (in the uploads folder), so pages don't load anything
 * from unpkg. Downloaded once from npm, for the version this plugin was released with.
 *
 * @package QuranMadinaHtml
 */

defined( 'ABSPATH' ) || exit;

/** The library's layouts and their database folders, as in the npm package. */
const QMH_LAYOUT_STEMS = array( 'Madina-1441H', 'Madina-1405H', 'IndoPak-15' );

/**
 * The folder holding the copy for this plugin's version.
 *
 * @return string
 */
function qmh_local_dir() {
	return trailingslashit( wp_upload_dir( null, false )['basedir'] ) . 'quran-madina-html/' . QMH_VERSION . '/';
}

/**
 * The URL of that folder.
 *
 * @return string
 */
function qmh_local_url() {
	return trailingslashit( wp_upload_dir( null, false )['baseurl'] ) . 'quran-madina-html/' . QMH_VERSION . '/';
}

/**
 * Whether the copy for this plugin's version is there.
 *
 * @return bool
 */
function qmh_local_ready() {
	return file_exists( qmh_local_dir() . 'dist/quran-madina-html.js' );
}

/**
 * Whether a path inside the npm package (relative to package/) belongs in the copy: the script,
 * its CSS, the images, and each layout's sharded database and font.
 *
 * @param string $path Path relative to the package root, with forward slashes.
 * @return bool
 */
function qmh_wanted_file( $path ) {
	// The script and its CSS, and their 2.x .min.* copies (older packages only have those).
	if ( preg_match( '#^dist/quran-madina-html(\.min)?\.(js|css)$#', $path ) ) {
		return true;
	}
	if ( 0 === strpos( $path, 'assets/img/' ) ) {
		return true;
	}
	if ( preg_match( '#^assets/db/v2/[a-z]+-qmh\.woff2$#', $path ) ) {
		return true;
	}
	foreach ( QMH_LAYOUT_STEMS as $stem ) {
		if ( 0 === strpos( $path, 'assets/db/v2/' . $stem . '/' ) ) {
			return true;
		}
	}
	return false;
}

/**
 * Copy the wanted files of an npm package archive (.tgz) into a folder.
 *
 * @param string $archive Path to the .tgz file.
 * @param string $dest    Folder to write into (created if missing), ending in '/'.
 * @return int|WP_Error Number of files written.
 */
function qmh_extract_package( $archive, $dest ) {
	if ( ! class_exists( 'PharData' ) ) {
		return new WP_Error( 'qmh_no_phar', __( 'PHP\'s Phar extension is needed to unpack the library.', 'quran-madina-html' ) );
	}
	try {
		$phar  = new PharData( $archive );
		$root  = 'phar://' . $phar->getPath() . '/package/';
		$count = 0;
		foreach ( new RecursiveIteratorIterator( $phar ) as $file ) {
			$full = str_replace( '\\', '/', $file->getPathname() );
			if ( 0 !== strpos( $full, $root ) ) {
				continue;
			}
			$path = substr( $full, strlen( $root ) );
			if ( ! qmh_wanted_file( $path ) || false !== strpos( $path, '..' ) ) {
				continue;
			}
			$target = $dest . $path;
			if ( ! is_dir( dirname( $target ) ) && ! mkdir( dirname( $target ), 0755, true ) ) { // phpcs:ignore WordPress.WP.AlternativeFunctions
				return new WP_Error( 'qmh_mkdir', __( 'Could not create the folder for the library.', 'quran-madina-html' ) );
			}
			if ( false === file_put_contents( $target, file_get_contents( $file->getPathname() ) ) ) { // phpcs:ignore WordPress.WP.AlternativeFunctions
				return new WP_Error( 'qmh_write', __( 'Could not write the library files.', 'quran-madina-html' ) );
			}
			++$count;
		}
	} catch ( Exception $e ) {
		return new WP_Error( 'qmh_unpack', $e->getMessage() );
	}
	foreach ( array( 'js', 'css' ) as $ext ) { // an older package only has the .min names
		$file = $dest . 'dist/quran-madina-html.' . $ext;
		$min  = $dest . 'dist/quran-madina-html.min.' . $ext;
		if ( ! file_exists( $file ) && file_exists( $min ) ) {
			copy( $min, $file );
		}
	}
	if ( ! file_exists( $dest . 'dist/quran-madina-html.js' ) ) {
		return new WP_Error( 'qmh_incomplete', __( 'The downloaded package does not contain the library.', 'quran-madina-html' ) );
	}
	return $count;
}

/**
 * Download this plugin's library version from npm into the uploads folder, replacing older
 * copies.
 *
 * @return int|WP_Error Number of files written.
 */
function qmh_download_library() {
	require_once ABSPATH . 'wp-admin/includes/file.php';
	$url = 'https://registry.npmjs.org/quran-madina-html/-/quran-madina-html-' . QMH_VERSION . '.tgz';
	$tmp = download_url( $url, 120 );
	if ( is_wp_error( $tmp ) ) {
		return $tmp;
	}
	$archive = $tmp . '.tgz'; // PharData recognises the archive by its extension
	rename( $tmp, $archive ); // phpcs:ignore WordPress.WP.AlternativeFunctions
	$parent = dirname( qmh_local_dir() ) . '/';
	qmh_remove_dir( $parent ); // older versions, and a half-written copy
	$result = qmh_extract_package( $archive, qmh_local_dir() );
	wp_delete_file( $archive );
	if ( is_wp_error( $result ) ) {
		qmh_remove_dir( $parent );
	}
	return $result;
}

/**
 * Remove a folder and everything in it.
 *
 * @param string $dir The folder.
 */
function qmh_remove_dir( $dir ) {
	if ( ! is_dir( $dir ) ) {
		return;
	}
	$items = new RecursiveIteratorIterator(
		new RecursiveDirectoryIterator( $dir, FilesystemIterator::SKIP_DOTS ),
		RecursiveIteratorIterator::CHILD_FIRST
	);
	foreach ( $items as $item ) {
		$item->isDir() ? rmdir( $item->getPathname() ) : wp_delete_file( $item->getPathname() ); // phpcs:ignore WordPress.WP.AlternativeFunctions
	}
	rmdir( $dir ); // phpcs:ignore WordPress.WP.AlternativeFunctions
}
