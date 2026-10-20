import 'dart:convert';

import 'package:flutter/foundation.dart' show listEquals;
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

import 'bundle_server.dart';
import 'page.dart';
import 'widget.dart';

/// Android, iOS and macOS: the tag lives in the platform's own WebView.
State<QuranMadinaFlutter> createQuranState() => _WebViewQuranState();

class _WebViewQuranState extends State<QuranMadinaFlutter> {
  late final WebViewController _controller;
  late Map<String, String> _shown;
  late List<QuranAyaAction> _shownActions;
  QuranLoader? _loaded; // the loader with the bundle resolved, once the page is loading
  int _loads = 0;
  double _height = 1;

  @override
  void initState() {
    super.initState();
    _shown = attributesOf(widget);
    _shownActions = widget.ayaActions;
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..addJavaScriptChannel(kChannel, onMessageReceived: _onMessage)
      ..setNavigationDelegate(NavigationDelegate(
        // the page itself is loaded from a string; any other navigation is a link
        onNavigationRequest: (request) {
          final url = request.url;
          if (url.startsWith('about:') || url.startsWith('data:') || url == _loaded?.cdn) {
            return NavigationDecision.navigate;
          }
          widget.onOpenUrl?.call(url);
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

  Future<void> _load() async {
    final load = ++_loads;
    var loader = loaderOf(widget);
    if (loader.bundled) {
      final base = await BundleServer.instance.baseUrl();
      if (!mounted || load != _loads) return; // a newer load started meanwhile
      loader = loader.resolveBundle(base);
    }
    _loaded = loader;
    _shownActions = widget.ayaActions;
    await _controller.loadHtmlString(buildPage(loader, _shown, actions: _shownActions),
        baseUrl: loader.cdn);
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
    } else if (data['kind'] == 'action') {
      final selection = QuranAyaSelection.fromJson(data['value']);
      if (selection != null) widget.onAyaAction?.call(selection);
    }
  }

  @override
  void didUpdateWidget(QuranMadinaFlutter old) {
    super.didUpdateWidget(old);
    final next = attributesOf(widget);
    if (loaderOf(widget) != loaderOf(old)) {
      _shown = next;
      _load();
      return;
    }
    final updates = attributeUpdates(_shown, next);
    if (updates.isNotEmpty) {
      _shown = next;
      _controller.runJavaScript(updateScript(updates));
    }
    if (!listEquals(_shownActions, widget.ayaActions)) {
      _shownActions = widget.ayaActions;
      _controller.runJavaScript(actionsScript(_shownActions));
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
