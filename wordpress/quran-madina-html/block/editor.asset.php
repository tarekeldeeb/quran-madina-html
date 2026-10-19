<?php
/**
 * Dependencies of the block's editor script (plain JavaScript, no build step).
 *
 * @package QuranMadinaHtml
 */

return array(
	'dependencies' => array( 'wp-blocks', 'wp-element', 'wp-block-editor', 'wp-components', 'wp-i18n' ),
	'version'      => filemtime( __DIR__ . '/editor.js' ),
);
