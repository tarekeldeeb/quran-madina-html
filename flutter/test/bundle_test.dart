import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:quran_madina_flutter/src/bundle.dart';
import 'package:quran_madina_flutter/src/bundle_server.dart';

/// A ustar archive of [files], like npm pack writes.
List<int> tarOf(Map<String, String> files) {
  final out = <int>[];
  files.forEach((path, text) {
    final data = utf8.encode(text);
    final header = List<int>.filled(512, 0);
    void put(int at, String s) => header.setRange(at, at + s.length, ascii.encode(s));
    String prefix = '', name = path;
    if (path.length > 100) {
      prefix = path.substring(0, path.lastIndexOf('/'));
      name = path.substring(path.lastIndexOf('/') + 1);
    }
    put(0, name);
    put(100, '0000644');
    put(124, data.length.toRadixString(8).padLeft(11, '0'));
    put(156, '0');
    put(257, 'ustar');
    put(345, prefix);
    out
      ..addAll(header)
      ..addAll(data)
      ..addAll(List<int>.filled((512 - data.length % 512) % 512, 0));
  });
  return out..addAll(List<int>.filled(1024, 0));
}

String manifest(String font) => jsonEncode({'version': 2, 'font_url': font});

final package = {
  'package/package.json': '{}',
  'package/dist/quran-madina-html.min.js': 'js',
  'package/dist/quran-madina-html.min.css': 'css',
  'package/assets/img/sura_border_sym4.svg': '<svg/>',
  'package/assets/db/v2/Madina-1441H.json': 'monolith',
  'package/assets/db/v2/Madina-1441H/manifest.json': manifest('assets/db/v2/madina-qmh.woff2'),
  'package/assets/db/v2/Madina-1441H/juz-01.json': 'j1',
  'package/assets/db/v2/IndoPak-15/manifest.json': manifest('assets/db/v2/indopak-qmh.woff2'),
  'package/assets/db/v2/IndoPak-15/juz-01.json': 'i1',
  'package/assets/db/v2/madina-qmh.woff2': 'f1',
  'package/assets/db/v2/indopak-qmh.woff2': 'f2',
  'package/assets/db/v2/oldmadina-qmh.woff2': 'f3',
};

void main() {
  group('readTar', () {
    test('reads plain files, sizes and long (prefixed) names', () {
      final long = 'package/${'a' * 60}/${'b' * 60}/c.json';
      final files = readTar(tarOf({'package/x.txt': 'hello', long: '{"k": 1}', 'e': ''}));
      expect(files.keys, ['package/x.txt', long, 'e']);
      expect(utf8.decode(files['package/x.txt']!), 'hello');
      expect(utf8.decode(files[long]!), '{"k": 1}');
      expect(files['e'], isEmpty);
    });

    test('reads a gzipped archive', () {
      final files = readTarGz(gzip.encode(tarOf({'a/b': 'xyz'})));
      expect(utf8.decode(files['a/b']!), 'xyz');
    });
  });

  test('readFolder reads a checkout like a package, only the bundle folders', () {
    final dir = Directory.systemTemp.createTempSync('qmh');
    addTearDown(() => dir.deleteSync(recursive: true));
    for (final path in ['dist/a.js', 'assets/db/v2/X/manifest.json', 'src/big.py', 'README.md']) {
      File('${dir.path}/$path')
        ..createSync(recursive: true)
        ..writeAsStringSync(path);
    }
    final files = readFolder(dir);
    expect(files.keys.toSet(), {'package/dist/a.js', 'package/assets/db/v2/X/manifest.json'});
    expect(utf8.decode(files['package/dist/a.js']!), 'dist/a.js');
  });

  group('selectBundle', () {
    final files = readTar(tarOf(package));

    test('takes the script, CSS, images, and each layout\'s shards and font', () {
      final out = selectBundle(files, ['1441H', 'indopak']);
      expect(out.keys.toSet(), {
        'dist/quran-madina-html.min.js',
        'dist/quran-madina-html.min.css',
        'assets/img/sura_border_sym4.svg',
        'assets/db/v2/Madina-1441H/manifest.json',
        'assets/db/v2/Madina-1441H/juz-01.json',
        'assets/db/v2/madina-qmh.woff2',
        'assets/db/v2/IndoPak-15/manifest.json',
        'assets/db/v2/IndoPak-15/juz-01.json',
        'assets/db/v2/indopak-qmh.woff2',
      });
    });

    test('rejects an unknown layout and a layout missing from the package', () {
      expect(() => selectBundle(files, ['Warsh']), throwsArgumentError);
      expect(() => selectBundle(files, ['1405H']), throwsStateError);
    });

    test('lists the asset folders to declare', () {
      final out = selectBundle(files, ['1441H']);
      expect(assetFolders('assets/quran_madina', out.keys), [
        'assets/quran_madina/assets/db/v2/',
        'assets/quran_madina/assets/db/v2/Madina-1441H/',
        'assets/quran_madina/assets/img/',
        'assets/quran_madina/dist/',
      ]);
    });
  });

  group('bundle server', () {
    test('maps request paths into the bundle, refusing to leave it', () {
      expect(bundlePath('/dist/quran-madina-html.min.js'), 'dist/quran-madina-html.min.js');
      expect(bundlePath('/assets//db/v2/x.json'), 'assets/db/v2/x.json');
      expect(bundlePath('/assets/../../secret'), isNull);
      expect(bundlePath('/'), isNull);
    });

    test('serves the types the library expects', () {
      expect(contentTypeFor('a/b.json').mimeType, 'application/json');
      expect(contentTypeFor('x.min.js').mimeType, 'text/javascript');
      expect(contentTypeFor('x.min.css').mimeType, 'text/css');
      expect(contentTypeFor('f.woff2').mimeType, 'font/woff2');
      expect(contentTypeFor('i.svg').mimeType, 'image/svg+xml');
    });
  });
}
