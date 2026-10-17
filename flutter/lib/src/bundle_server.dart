import 'dart:async';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

import 'page.dart';

/// Serves the bundled library files ([kBundleDir] in the app's assets) to the WebViews over
/// http on the loopback interface. A WebView can't fetch the databases and fonts from Flutter
/// assets directly; a page served from 127.0.0.1 can. One server for the whole app, started on
/// first use, on a free port.
class BundleServer {
  BundleServer._();

  /// The app's server.
  static final BundleServer instance = BundleServer._();

  Future<String>? _base;

  /// The URL [kBundleDir] is served at, ending in '/'. Starts the server the first time.
  Future<String> baseUrl() => _base ??= _start();

  Future<String> _start() async {
    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    server.listen(_serve);
    return 'http://${server.address.address}:${server.port}/';
  }

  Future<void> _serve(HttpRequest request) async {
    final response = request.response;
    response.headers.set('Access-Control-Allow-Origin', '*');
    final path = bundlePath(request.uri.path);
    if (path == null || (request.method != 'GET' && request.method != 'HEAD')) {
      response.statusCode = HttpStatus.notFound;
      await response.close();
      return;
    }
    try {
      final data = await rootBundle.load('$kBundleDir/$path');
      response.headers.contentType = contentTypeFor(path);
      response.headers.set('Cache-Control', 'max-age=86400');
      if (request.method == 'GET') {
        response.add(data.buffer.asUint8List(data.offsetInBytes, data.lengthInBytes));
      }
    } catch (_) {
      debugPrint('quran_madina_flutter: $kBundleDir/$path is not in the app\'s assets. Run '
          '`dart run quran_madina_flutter:bundle` and declare its folders in pubspec.yaml.');
      response.statusCode = HttpStatus.notFound;
    }
    await response.close();
  }
}

/// The bundle-relative path of a request path, or null if it tries to leave the bundle.
@visibleForTesting
String? bundlePath(String requestPath) {
  final parts = Uri.decodeComponent(requestPath).split('/').where((p) => p.isNotEmpty).toList();
  if (parts.isEmpty || parts.any((p) => p == '..' || p == '.')) return null;
  return parts.join('/');
}

/// The content type the library expects for a bundled file.
@visibleForTesting
ContentType contentTypeFor(String path) {
  final ext = path.contains('.') ? path.substring(path.lastIndexOf('.') + 1).toLowerCase() : '';
  switch (ext) {
    case 'js':
      return ContentType('text', 'javascript', charset: 'utf-8');
    case 'css':
      return ContentType('text', 'css', charset: 'utf-8');
    case 'json':
      return ContentType('application', 'json', charset: 'utf-8');
    case 'woff2':
      return ContentType('font', 'woff2');
    case 'svg':
      return ContentType('image', 'svg+xml');
    case 'png':
      return ContentType('image', 'png');
    default:
      return ContentType.binary;
  }
}
