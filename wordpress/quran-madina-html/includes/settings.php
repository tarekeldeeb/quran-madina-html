<?php
/**
 * Settings → Quran Madina: the print, the size, and where the library loads from.
 *
 * @package QuranMadinaHtml
 */

defined( 'ABSPATH' ) || exit;

/**
 * Register the settings.
 */
function qmh_register_settings() {
	register_setting(
		'qmh',
		'qmh_settings',
		array(
			'type'              => 'array',
			'sanitize_callback' => 'qmh_sanitize_settings',
			'default'           => array(),
		)
	);
}
add_action( 'admin_init', 'qmh_register_settings' );

/**
 * Keep only valid settings.
 *
 * @param mixed $input Submitted values.
 * @return array
 */
function qmh_sanitize_settings( $input ) {
	$input = is_array( $input ) ? $input : array();
	$size  = isset( $input['font_size'] ) ? (float) $input['font_size'] : 16;
	return array(
		'layout'    => isset( $input['layout'] ) && array_key_exists( $input['layout'], QMH_LAYOUTS ) ? $input['layout'] : '1441H',
		'font_size' => max( 6, min( 100, $size ? $size : 16 ) ),
		'source'    => isset( $input['source'] ) && 'local' === $input['source'] ? 'local' : 'unpkg',
	);
}

/**
 * Add the page under Settings.
 */
function qmh_add_settings_page() {
	add_options_page(
		__( 'Quran Madina Html', 'quran-madina-html' ),
		__( 'Quran Madina', 'quran-madina-html' ),
		'manage_options',
		'quran-madina-html',
		'qmh_render_settings_page'
	);
}
add_action( 'admin_menu', 'qmh_add_settings_page' );

/**
 * A "Settings" link on the Plugins screen.
 *
 * @param array $links The plugin's action links.
 * @return array
 */
function qmh_settings_link( $links ) {
	$url = admin_url( 'options-general.php?page=quran-madina-html' );
	array_unshift( $links, '<a href="' . esc_url( $url ) . '">' . esc_html__( 'Settings', 'quran-madina-html' ) . '</a>' );
	return $links;
}
add_filter( 'plugin_action_links_' . plugin_basename( QMH_FILE ), 'qmh_settings_link' );

/**
 * Copy the library to this site (the button on the settings page).
 */
function qmh_handle_download() {
	if ( ! current_user_can( 'manage_options' ) ) {
		wp_die( esc_html__( 'You are not allowed to do this.', 'quran-madina-html' ) );
	}
	check_admin_referer( 'qmh_download' );
	$result = qmh_download_library();
	$args   = is_wp_error( $result )
		? array( 'qmh_error' => rawurlencode( $result->get_error_message() ) )
		: array( 'qmh_copied' => (int) $result );
	wp_safe_redirect( add_query_arg( $args, admin_url( 'options-general.php?page=quran-madina-html' ) ) );
	exit;
}
add_action( 'admin_post_qmh_download', 'qmh_handle_download' );

/**
 * The settings page.
 */
function qmh_render_settings_page() {
	if ( ! current_user_can( 'manage_options' ) ) {
		return;
	}
	$s     = qmh_settings();
	$ready = qmh_local_ready();
	// phpcs:disable WordPress.Security.NonceVerification.Recommended -- messages after our own redirect.
	if ( isset( $_GET['qmh_copied'] ) ) {
		echo '<div class="notice notice-success is-dismissible"><p>' . esc_html(
			sprintf(
				/* translators: 1: number of files, 2: version */
				__( 'Copied %1$d files of quran-madina-html %2$s to this site.', 'quran-madina-html' ),
				absint( $_GET['qmh_copied'] ),
				QMH_VERSION
			)
		) . '</p></div>';
	}
	if ( isset( $_GET['qmh_error'] ) ) {
		echo '<div class="notice notice-error"><p>' . esc_html__( 'The library could not be copied:', 'quran-madina-html' ) . ' '
			. esc_html( sanitize_text_field( wp_unslash( $_GET['qmh_error'] ) ) ) . '</p></div>';
	}
	// phpcs:enable
	if ( 'local' === $s['source'] && ! $ready ) {
		echo '<div class="notice notice-warning"><p>' . esc_html__( 'The library isn\'t on this site yet, so pages load it from unpkg. Use "Copy to this site" below.', 'quran-madina-html' ) . '</p></div>';
	}
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
			<?php settings_fields( 'qmh' ); ?>
			<table class="form-table" role="presentation">
				<tr>
					<th scope="row"><label for="qmh-layout"><?php esc_html_e( 'Print', 'quran-madina-html' ); ?></label></th>
					<td>
						<select id="qmh-layout" name="qmh_settings[layout]">
							<?php foreach ( QMH_LAYOUTS as $value => $label ) : ?>
								<option value="<?php echo esc_attr( $value ); ?>" <?php selected( $s['layout'], $value ); ?>><?php echo esc_html( $label ); ?></option>
							<?php endforeach; ?>
						</select>
						<p class="description"><?php esc_html_e( 'Used by every Quran block and shortcode on the site.', 'quran-madina-html' ); ?></p>
					</td>
				</tr>
				<tr>
					<th scope="row"><label for="qmh-size"><?php esc_html_e( 'Font size', 'quran-madina-html' ); ?></label></th>
					<td>
						<input id="qmh-size" name="qmh_settings[font_size]" type="number" min="6" max="100" step="0.5" value="<?php echo esc_attr( (string) $s['font_size'] ); ?>" class="small-text"> px
					</td>
				</tr>
				<tr>
					<th scope="row"><?php esc_html_e( 'Load the library from', 'quran-madina-html' ); ?></th>
					<td>
						<fieldset>
							<label><input type="radio" name="qmh_settings[source]" value="unpkg" <?php checked( $s['source'], 'unpkg' ); ?>> <?php esc_html_e( 'unpkg.com (nothing to set up)', 'quran-madina-html' ); ?></label><br>
							<label><input type="radio" name="qmh_settings[source]" value="local" <?php checked( $s['source'], 'local' ); ?>> <?php esc_html_e( 'This site (no outside requests; copy it below first)', 'quran-madina-html' ); ?></label>
						</fieldset>
					</td>
				</tr>
			</table>
			<?php submit_button(); ?>
		</form>

		<h2><?php esc_html_e( 'Library on this site', 'quran-madina-html' ); ?></h2>
		<p>
			<?php
			if ( $ready ) {
				/* translators: %s: version */
				echo esc_html( sprintf( __( 'quran-madina-html %s is on this site, in the uploads folder.', 'quran-madina-html' ), QMH_VERSION ) );
			} else {
				esc_html_e( 'Not copied yet. Copying downloads the library, its texts and fonts for all three prints (about 11 MB) from npm into the uploads folder.', 'quran-madina-html' );
			}
			?>
		</p>
		<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
			<input type="hidden" name="action" value="qmh_download">
			<?php wp_nonce_field( 'qmh_download' ); ?>
			<?php submit_button( $ready ? __( 'Copy again', 'quran-madina-html' ) : __( 'Copy to this site', 'quran-madina-html' ), 'secondary', 'submit', false ); ?>
		</form>
	</div>
	<?php
}
