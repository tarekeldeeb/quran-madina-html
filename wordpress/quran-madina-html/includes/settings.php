<?php
/**
 * Settings → Quran Madina: the print and the size.
 *
 * @package QuranMadinaHtml
 */

defined( 'ABSPATH' ) || exit;

/**
 * Register the settings.
 */
function qmhtml_register_settings() {
	register_setting(
		'qmhtml',
		'qmhtml_settings',
		array(
			'type'              => 'array',
			'sanitize_callback' => 'qmhtml_sanitize_settings',
			'default'           => array(),
		)
	);
}
add_action( 'admin_init', 'qmhtml_register_settings' );

/**
 * Keep only valid settings.
 *
 * @param mixed $input Submitted values.
 * @return array
 */
function qmhtml_sanitize_settings( $input ) {
	$input = is_array( $input ) ? $input : array();
	$size  = isset( $input['font_size'] ) ? (float) $input['font_size'] : 16;
	return array(
		'layout'    => isset( $input['layout'] ) && array_key_exists( $input['layout'], QMHTML_LAYOUTS ) ? $input['layout'] : '1441H',
		'font_size' => max( 6, min( 100, $size ? $size : 16 ) ),
	);
}

/**
 * Add the page under Settings.
 */
function qmhtml_add_settings_page() {
	add_options_page(
		__( 'Quran Madina Html', 'quran-madina-html' ),
		__( 'Quran Madina', 'quran-madina-html' ),
		'manage_options',
		'quran-madina-html',
		'qmhtml_render_settings_page'
	);
}
add_action( 'admin_menu', 'qmhtml_add_settings_page' );

/**
 * A "Settings" link on the Plugins screen.
 *
 * @param array $links The plugin's action links.
 * @return array
 */
function qmhtml_settings_link( $links ) {
	$url = admin_url( 'options-general.php?page=quran-madina-html' );
	array_unshift( $links, '<a href="' . esc_url( $url ) . '">' . esc_html__( 'Settings', 'quran-madina-html' ) . '</a>' );
	return $links;
}
add_filter( 'plugin_action_links_' . plugin_basename( QMHTML_FILE ), 'qmhtml_settings_link' );

/**
 * The settings page.
 */
function qmhtml_render_settings_page() {
	if ( ! current_user_can( 'manage_options' ) ) {
		return;
	}
	$s = qmhtml_settings();
	?>
	<div class="wrap">
		<h1><?php esc_html_e( 'Quran Madina Html', 'quran-madina-html' ); ?></h1>
		<p>
			<?php esc_html_e( 'Show Quran text with the Quran block, or with a shortcode in any post or page:', 'quran-madina-html' ); ?>
			<code>[quran sura="2" aya="255"]</code>
			<code>[quran page="1"]</code>
			<code>[quran sura="1" aya="2-4" highlight="1" letters="1:3 emerald blink"]</code>
			<a href="https://tarekeldeeb.github.io/quran-madina-html/docs/getting-started/wordpress/" target="_blank" rel="noopener"><?php esc_html_e( 'All options', 'quran-madina-html' ); ?></a>
		</p>
		<form method="post" action="options.php">
			<?php settings_fields( 'qmhtml' ); ?>
			<table class="form-table" role="presentation">
				<tr>
					<th scope="row"><label for="qmh-layout"><?php esc_html_e( 'Print', 'quran-madina-html' ); ?></label></th>
					<td>
						<select id="qmh-layout" name="qmhtml_settings[layout]">
							<?php foreach ( QMHTML_LAYOUTS as $value => $label ) : ?>
								<option value="<?php echo esc_attr( $value ); ?>" <?php selected( $s['layout'], $value ); ?>><?php echo esc_html( $label ); ?></option>
							<?php endforeach; ?>
						</select>
						<p class="description"><?php esc_html_e( 'Used by every Quran block and shortcode on the site.', 'quran-madina-html' ); ?></p>
					</td>
				</tr>
				<tr>
					<th scope="row"><label for="qmh-size"><?php esc_html_e( 'Font size', 'quran-madina-html' ); ?></label></th>
					<td>
						<input id="qmh-size" name="qmhtml_settings[font_size]" type="number" min="6" max="100" step="0.5" value="<?php echo esc_attr( (string) $s['font_size'] ); ?>" class="small-text"> px
					</td>
				</tr>
			</table>
			<?php submit_button(); ?>
		</form>
	</div>
	<?php
}
