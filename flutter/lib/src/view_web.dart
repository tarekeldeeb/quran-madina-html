import 'dart:js_interop';
import 'dart:ui_web' as ui_web;

import 'package:flutter/widgets.dart';
import 'package:web/web.dart' as web;

import 'page.dart';
import 'widget.dart';

/// Web: no WebView needed. The tag goes straight into the page, as a platform view, and the
/// library script is added to the document once.
State<QuranMadinaFlutter> createQuranState() => _WebQuranState();

QuranLoader? _pageLoader; // the loader the page's script was set up with
int _views = 0;

/// The loader with the bundle served from the app's own assets.
QuranLoader _resolve(QuranLoader loader) {
  if (!loader.bundled) return loader;
  final assets = ui_web.assetManager.getAssetUrl('$kBundleDir/');
  return loader.resolveBundle(Uri.parse(web.document.baseURI).resolve(assets).toString());
}

/// Adds the library script to the page, unless it is there already (added by an earlier widget
/// or by the app's own index.html). The library reads its options from that one script, so
/// every widget on the page shares the first one's [QuranLoader.layout], size and URLs.
void _ensureScript(QuranLoader loader) {
  final first = _pageLoader;
  if (first != null) {
    if (first.src != loader.src ||
        first.cdn != loader.cdn ||
        first.layout != loader.layout ||
        first.fontSize != loader.fontSize) {
      debugPrint('quran_madina_flutter: on the web, layout, fontSize, src, cdn and bundled are '
          'set once for the page; this widget uses the first widget\'s.');
    }
    return;
  }
  _pageLoader = loader;
  if (web.document.querySelector('script[src*="quran-madina-html"]') != null) return;
  final script = web.HTMLScriptElement()..src = loader.src;
  script.setAttribute('data-cdn', loader.cdn);
  if (loader.layout != null) script.setAttribute('data-layout', loader.layout!);
  if (loader.fontSize != null) script.setAttribute('data-font-size', '${loader.fontSize}');
  web.document.head!.append(script);
}

class _WebQuranState extends State<QuranMadinaFlutter> {
  final String _viewType = 'quran-madina-flutter-${_views++}';
  final web.HTMLDivElement _box = web.HTMLDivElement();
  final web.Element _tag = web.document.createElement('quran-madina-html');
  web.ResizeObserver? _observer;
  late Map<String, String> _shown;
  double _height = 1;

  @override
  void initState() {
    super.initState();
    final loader = _resolve(loaderOf(widget));
    _ensureScript(loader);
    _shown = attributesOf(widget);
    _shown.forEach(_tag.setAttribute);
    _box
      ..setAttribute('dir', 'rtl')
      ..setAttribute('lang', 'ar')
      ..style.setProperty('display', 'flow-root')
      ..append(_tag);
    _paint(loader);
    // Flutter sizes the outer element; the box inside takes the text's own height, which the
    // widget then adopts.
    final outer = web.HTMLDivElement();
    outer.style
      ..setProperty('width', '100%')
      ..setProperty('height', '100%')
      ..setProperty('overflow', 'hidden');
    outer.append(_box);
    ui_web.platformViewRegistry.registerViewFactory(_viewType, (int id) => outer);
    _observer = web.ResizeObserver(
        ((JSArray<web.ResizeObserverEntry> entries, web.ResizeObserver observer) => _measure())
            .toJS);
    _observer!.observe(_box);
  }

  void _paint(QuranLoader loader) {
    _box.style
      ..setProperty('color', loader.textColor ?? '#20201d')
      ..setProperty('background', loader.backgroundColor ?? 'transparent');
  }

  void _measure() {
    final h = _box.getBoundingClientRect().height.ceilToDouble();
    if (mounted && h > 0 && (h - _height).abs() >= 1) setState(() => _height = h);
  }

  @override
  void didUpdateWidget(QuranMadinaFlutter old) {
    super.didUpdateWidget(old);
    if (loaderOf(widget) != loaderOf(old)) {
      final loader = _resolve(loaderOf(widget));
      _ensureScript(loader); // warns if it asks for another layout or size
      _paint(loader);
    }
    final next = attributesOf(widget);
    attributeUpdates(_shown, next).forEach((k, v) {
      if (v == null) {
        _tag.removeAttribute(k);
      } else {
        _tag.setAttribute(k, v);
      }
    });
    _shown = next;
  }

  @override
  void dispose() {
    _observer?.disconnect();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: widget.height ?? _height,
      child: HtmlElementView(viewType: _viewType),
    );
  }
}
