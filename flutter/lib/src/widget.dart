import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

import 'page.dart';

/// Renders Quran text like the printed Madina Mushaf: a WebView holding one
/// `<quran-madina-html>` tag. Same options as the React wrapper.
///
/// ```dart
/// QuranMadinaHtml(page: 106)
/// QuranMadinaHtml(sura: 2, aya: '255', highlight: '5-8', error: '1')
/// QuranMadinaHtml(sura: 1, aya: '2-4', letters: '1:3, 4:3-5 emerald blink')
/// ```
///
/// `page` and `sura`/`aya` are mutually exclusive (`page` wins if both are given). Changing a
/// tag option re-renders in place; changing a loader option ([layout], [fontSize], [src], [cdn],
/// [textColor], [backgroundColor]) reloads the WebView. The widget takes the height of the
/// rendered text unless [height] is given.
class QuranMadinaHtml extends StatefulWidget {
  const QuranMadinaHtml({
    super.key,
    this.page,
    this.sura,
    this.aya,
    this.words,
    this.highlight,
    this.error,
    this.letters,
    this.headless,
    this.quotes,
    this.inline,
    this.notitle,
    this.layout,
    this.fontSize,
    this.src = kDefaultSrc,
    this.cdn = kDefaultCdn,
    this.textColor,
    this.backgroundColor,
    this.height,
    this.onOpenUrl,
  });

  /// Full Mushaf page (1-604; IndoPak 1-610).
  final int? page;

  /// Sura number (1-114), with [aya].
  final int? sura;

  /// Aya number or range, e.g. '255' or '8-10'.
  final String? aya;

  /// Restrict to a 1-based word range, e.g. '1:2', '3-10' or '5'.
  final String? words;

  /// 1-based word range to mark soft yellow (same format as [words]).
  final String? highlight;

  /// 1-based word range to mark soft red; wins over [highlight] on overlap.
  final String? error;

  /// Letters to emphasise inside words: "word:letters colour blink" groups, e.g.
  /// '1:3, 4:3-5 emerald blink'. Colour optional (crimson by default), blink optional.
  final String? letters;

  /// Drop the header (sura name, copy/translate icons) and render only the text.
  final bool? headless;

  /// 'no' drops the quote marks of inline (single-line) renders.
  final String? quotes;

  /// 'no' forces the multiline layout even when the selection fits one line.
  final String? inline;

  /// With [words] crossing into a new sura: hide its name, keep the decorated line.
  final bool? notitle;

  /// Layout: '1441H' (default), '1405H' or 'IndoPak'.
  final String? layout;

  /// Font size in logical pixels (default 16). Any size works.
  final num? fontSize;

  /// URL of the library script (default: latest 2.x on unpkg).
  final String src;

  /// Base URL for the library's CSS, databases and fonts (self-host for offline use).
  final String cdn;

  /// CSS colour of the text, e.g. '#ece6d6' on a dark page (default near-black).
  final String? textColor;

  /// CSS colour behind the text (default transparent).
  final String? backgroundColor;

  /// Fixed height; by default the widget takes the height of the rendered text.
  final double? height;

  /// Called with links the library opens (the translate buttons, to quran.com). Open them with
  /// url_launcher, for example; by default they are ignored.
  final void Function(String url)? onOpenUrl;

  Map<String, String> get _attributes => tagAttributes(
        page: page,
        sura: sura,
        aya: aya,
        words: words,
        highlight: highlight,
        error: error,
        letters: letters,
        headless: headless,
        quotes: quotes,
        inline: inline,
        notitle: notitle,
      );

  QuranLoader get _loader => QuranLoader(
        src: src,
        cdn: cdn,
        layout: layout,
        fontSize: fontSize,
        textColor: textColor,
        backgroundColor: backgroundColor,
      );

  @override
  State<QuranMadinaHtml> createState() => _QuranMadinaHtmlState();
}

class _QuranMadinaHtmlState extends State<QuranMadinaHtml> {
  late final WebViewController _controller;
  late Map<String, String> _shown;
  double _height = 1;

  @override
  void initState() {
    super.initState();
    _shown = widget._attributes;
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..addJavaScriptChannel(kChannel, onMessageReceived: _onMessage)
      ..setNavigationDelegate(NavigationDelegate(
        // the page itself is loaded from a string; any other navigation is a link
        onNavigationRequest: (request) {
          if (request.url.startsWith('about:') || request.url.startsWith('data:') ||
              request.url == widget.cdn) {
            return NavigationDecision.navigate;
          }
          widget.onOpenUrl?.call(request.url);
          return NavigationDecision.prevent;
        },
      ));
    try {
      _controller.setBackgroundColor(Colors.transparent);
    } catch (_) {
      // not supported on every platform (e.g. macOS); the page background is transparent anyway
    }
    _load();
  }

  void _load() {
    _controller.loadHtmlString(buildPage(widget._loader, _shown), baseUrl: widget.cdn);
  }

  void _onMessage(JavaScriptMessage message) {
    final Object? data;
    try {
      data = jsonDecode(message.message);
    } on FormatException {
      return;
    }
    if (data is! Map) return;
    if (data['kind'] == 'height' && data['value'] is num) {
      final h = (data['value'] as num).toDouble();
      if (mounted && h > 0 && (h - _height).abs() >= 1) setState(() => _height = h);
    } else if (data['kind'] == 'open' && data['value'] is String) {
      widget.onOpenUrl?.call(data['value'] as String);
    }
  }

  @override
  void didUpdateWidget(QuranMadinaHtml old) {
    super.didUpdateWidget(old);
    final next = widget._attributes;
    if (widget._loader != old._loader) {
      _shown = next;
      _load();
      return;
    }
    final updates = attributeUpdates(_shown, next);
    if (updates.isNotEmpty) {
      _shown = next;
      _controller.runJavaScript(updateScript(updates));
    }
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: widget.height ?? _height,
      child: WebViewWidget(controller: _controller),
    );
  }
}
