<?php
/**
 * The [quran] shortcode, the Quran block, and loading the library.
 *
 * @package QuranMadinaHtml
 */

defined( 'ABSPATH' ) || exit;

/** Attributes the <quran-madina-html> tag takes, in the order they are written. */
const QMH_ATTRIBUTES = array( 'page', 'sura', 'aya', 'words', 'highlight', 'error', 'letters', 'headless', 'notitle', 'quotes', 'inline' );

/** Attributes that are on or off. */
const QMH_FLAGS = array( 'headless', 'notitle' );

/** The library's layouts, by the name data-layout takes. */
const QMH_LAYOUTS = array(
	'1441H'   => 'Madina Mushaf, 1441H',
	'1405H'   => 'Madina Mushaf, 1405H',
	'IndoPak' => 'IndoPak, 15 lines',
);

/**
 * The plugin's settings, with defaults.
 *
 * @return array{layout:string,font_size:float,source:string}
 */
function qmh_settings() {
	$saved = get_option( 'qmh_settings', array() );
	return wp_parse_args(
		is_array( $saved ) ? $saved : array(),
		array(
			'layout'    => '1441H',
			'font_size' => 16,
			'source'    => 'unpkg',
		)
	);
}

/**
 * Where the library loads from: the copy on this site when chosen and present, otherwise unpkg,
 * pinned to the version this plugin was released with.
 *
 * @return array{src:string,cdn:string,local:bool}
 */
function qmh_library_urls() {
	if ( 'local' === qmh_settings()['source'] && qmh_local_ready() ) {
		$base = qmh_local_url();
		return array(
			'src'   => $base . 'dist/quran-madina-html.min.js',
			'cdn'   => $base,
			'local' => true,
		);
	}
	$base = 'https://unpkg.com/quran-madina-html@' . QMH_VERSION . '/';
	return array(
		'src'   => $base . 'dist/quran-madina-html.min.js',
		'cdn'   => $base,
		'local' => false,
	);
}

/**
 * Register the library script. It loads in the footer, on pages that show Quran text only.
 */
function qmh_register_script() {
	wp_register_script( 'quran-madina-html', qmh_library_urls()['src'], array(), null, array( 'in_footer' => true ) ); // phpcs:ignore WordPress.WP.EnqueuedResourceParameters.MissingVersion -- the URL carries the version.
}
add_action( 'init', 'qmh_register_script' );

/**
 * The library reads its options from its own <script> tag: add them there.
 *
 * @param string $tag    The <script> tag WordPress prints.
 * @param string $handle Its handle.
 * @return string
 */
function qmh_script_attributes( $tag, $handle ) {
	if ( 'quran-madina-html' !== $handle ) {
		return $tag;
	}
	$settings = qmh_settings();
	$attrs    = sprintf(
		' data-cdn="%s" data-layout="%s" data-font-size="%s"',
		esc_url( qmh_library_urls()['cdn'] ),
		esc_attr( $settings['layout'] ),
		esc_attr( (string) $settings['font_size'] )
	);
	return preg_replace( '/<script\b/', '<script' . $attrs, $tag, 1 );
}
add_filter( 'script_loader_tag', 'qmh_script_attributes', 10, 2 );

/** Attributes that take a number or a range: 255, 8-10, 1:2. */
const QMH_RANGES = array( 'page', 'sura', 'aya', 'words', 'highlight', 'error' );

/**
 * One attribute value as the tag takes it, or '' when it isn't valid for that attribute:
 * numbers and ranges for the range attributes, a known word for quotes/inline, and for letters
 * only what a letters list and a CSS colour can contain.
 *
 * @param string $name  The attribute.
 * @param mixed  $value The raw value.
 * @return string
 */
function qmh_clean_value( $name, $value ) {
	if ( true === $value ) {
		return 'true';
	}
	$value = trim( wp_strip_all_tags( (string) $value ) );
	if ( in_array( $name, QMH_RANGES, true ) ) {
		return preg_match( '/^\d+(\s*[-:]\s*\d+)?$/', $value ) ? preg_replace( '/\s+/', '', $value ) : '';
	}
	if ( in_array( $name, array( 'quotes', 'inline' ), true ) ) {
		$value = strtolower( $value );
		return in_array( $value, array( 'no', 'yes', 'auto', 'false', 'true' ), true ) ? $value : '';
	}
	if ( 'letters' === $name ) {
		return preg_replace( '/[^0-9A-Za-z\s:,+\-#.()%]/', '', $value );
	}
	return $value; // flags: read by the caller
}

/**
 * The <quran-madina-html> tag for the given attributes, and the library queued for the page.
 *
 * @param array $atts Attribute values by name; others are ignored.
 * @return string
 */
function qmh_tag( $atts ) {
	if ( isset( $atts['page'] ) && '' !== qmh_clean_value( 'page', $atts['page'] ) ) {
		unset( $atts['sura'], $atts['aya'], $atts['words'] ); // a page wins, as in the other wrappers
	}
	$html = '<quran-madina-html';
	foreach ( QMH_ATTRIBUTES as $name ) {
		if ( ! isset( $atts[ $name ] ) ) {
			continue;
		}
		$value = qmh_clean_value( $name, $atts[ $name ] );
		if ( in_array( $name, QMH_FLAGS, true ) ) {
			if ( in_array( strtolower( $value ), array( 'true', '1', 'yes', 'on' ), true ) ) {
				$html .= ' ' . $name . '="true"';
			}
			continue;
		}
		if ( '' !== $value ) {
			$html .= sprintf( ' %s="%s"', $name, esc_attr( $value ) );
		}
	}
	$html .= '></quran-madina-html>';
	wp_enqueue_script( 'quran-madina-html' );
	return $html;
}

/**
 * [quran sura="2" aya="255" highlight="5-8"]: every tag attribute works as a shortcode attribute.
 *
 * @param array|string $atts Shortcode attributes.
 * @return string
 */
function qmh_shortcode( $atts ) {
	$atts = shortcode_atts( array_fill_keys( QMH_ATTRIBUTES, null ), (array) $atts, 'quran' );
	return qmh_tag( array_filter( $atts, 'is_scalar' ) );
}
add_shortcode( 'quran', 'qmh_shortcode' );
add_shortcode( 'quran_madina', 'qmh_shortcode' );

/**
 * The Quran block: the same tag, with its settings in the block sidebar.
 */
function qmh_register_block() {
	register_block_type(
		dirname( __DIR__ ) . '/block',
		array( 'render_callback' => 'qmh_render_block' )
	);
}
add_action( 'init', 'qmh_register_block' );

/**
 * Render the Quran block.
 *
 * @param array $attributes Block attributes.
 * @return string
 */
function qmh_render_block( $attributes ) {
	$wrapper = get_block_wrapper_attributes();
	return sprintf( '<div %s>%s</div>', $wrapper, qmh_tag( (array) $attributes ) );
}

/**
 * The block editor shows the text live, so it needs the library too.
 */
function qmh_editor_library() {
	if ( is_admin() ) {
		wp_enqueue_script( 'quran-madina-html' );
	}
}
add_action( 'enqueue_block_assets', 'qmh_editor_library' );
