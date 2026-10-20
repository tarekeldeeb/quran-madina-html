/**
 * The Quran block in the editor: the text renders live (the library is loaded in the editor
 * too), and the block sidebar holds its settings. The front end is rendered in PHP.
 */
( function ( blocks, element, blockEditor, components, i18n ) {
	var el = element.createElement;
	var __ = i18n.__;

	var TEXT_FIELDS = [
		[ 'page', __( 'Page', 'quran-madina-html' ), __( 'A whole page: 1 to 604 (IndoPak 610). Leave empty to show verses.', 'quran-madina-html' ) ],
		[ 'sura', __( 'Sura', 'quran-madina-html' ), __( '1 to 114', 'quran-madina-html' ) ],
		[ 'aya', __( 'Verses', 'quran-madina-html' ), __( 'One verse (255) or a range (8-10)', 'quran-madina-html' ) ],
		[ 'words', __( 'Only these words', 'quran-madina-html' ), __( 'A word range, e.g. 1-5. Counting starts at the first verse.', 'quran-madina-html' ) ],
		[ 'highlight', __( 'Highlight (yellow)', 'quran-madina-html' ), __( 'A word range, e.g. 5-8', 'quran-madina-html' ) ],
		[ 'error', __( 'Mistake (red)', 'quran-madina-html' ), __( 'A word range, e.g. 3', 'quran-madina-html' ) ],
		[ 'letters', __( 'Letters', 'quran-madina-html' ), __( 'word:letters, colour, blink. E.g. 1:3, 4:3-5 emerald blink', 'quran-madina-html' ) ],
		[ 'actions', __( 'Verse actions', 'quran-madina-html' ), __( 'What a click on a verse offers: e.g. copy, or none for plain text. Empty: all.', 'quran-madina-html' ) ]
	];
	var ATTRIBUTES = [ 'page', 'sura', 'aya', 'words', 'highlight', 'error', 'letters', 'quotes', 'inline', 'actions' ];

	/** The tag's attributes for the block's settings. */
	function tagAttributes( a ) {
		var out = {};
		ATTRIBUTES.forEach( function ( name ) {
			if ( a[ name ] ) {
				out[ name ] = String( a[ name ] );
			}
		} );
		if ( out.page ) {
			delete out.sura;
			delete out.aya;
			delete out.words;
		}
		if ( a.headless ) {
			out.headless = 'true';
		}
		if ( a.notitle ) {
			out.notitle = 'true';
		}
		return out;
	}

	blocks.registerBlockType( 'quran-madina-html/quran', {
		edit: function ( props ) {
			var a = props.attributes;
			var set = function ( name ) {
				return function ( value ) {
					var change = {};
					change[ name ] = value;
					props.setAttributes( change );
				};
			};
			var attrs = tagAttributes( a );
			var ready = attrs.page || ( attrs.sura && attrs.aya );

			var fields = TEXT_FIELDS.map( function ( f ) {
				return el( components.TextControl, {
					key: f[ 0 ],
					label: f[ 1 ],
					help: f[ 2 ],
					value: a[ f[ 0 ] ] || '',
					onChange: set( f[ 0 ] ),
					__nextHasNoMarginBottom: true,
					__next40pxDefaultSize: true
				} );
			} );
			fields.push(
				el( components.ToggleControl, {
					key: 'headless',
					label: __( 'Hide the header', 'quran-madina-html' ),
					help: __( 'Show only the Quran text, without the sura name, copy and translate.', 'quran-madina-html' ),
					checked: !! a.headless,
					onChange: set( 'headless' ),
					__nextHasNoMarginBottom: true
				} )
			);

			// key: re-create the tag when the selection changes, so it always renders fresh
			var preview = ready
				? el( 'quran-madina-html', Object.assign( { key: JSON.stringify( attrs ) }, attrs ) )
				: el( 'p', null, __( 'Choose a sura and verses, or a page, in the block settings.', 'quran-madina-html' ) );

			return el(
				element.Fragment,
				null,
				el(
					blockEditor.InspectorControls,
					null,
					el( components.PanelBody, { title: __( 'Quran', 'quran-madina-html' ) }, fields )
				),
				el( 'div', blockEditor.useBlockProps(), preview )
			);
		},
		save: function () {
			return null; // rendered in PHP
		}
	} );
}( window.wp.blocks, window.wp.element, window.wp.blockEditor, window.wp.components, window.wp.i18n ) );
