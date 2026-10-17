import 'dart:convert';
import 'dart:io';

/// The layouts the library ships, by the name `layout` takes, and their database folders.
const Map<String, String> kLayoutStems = {
  '1441H': 'Madina-1441H',
  '1405H': 'Madina-1405H',
  'IndoPak': 'IndoPak-15',
};

/// The files of a `.tgz` (an npm package), by path. Plain files only.
Map<String, List<int>> readTarGz(List<int> bytes) => readTar(gzip.decode(bytes));

/// The files of a tar archive, by path. Plain files only (ustar names with prefixes).
Map<String, List<int>> readTar(List<int> tar) {
  final out = <String, List<int>>{};
  String field(int start, int length) {
    final raw = tar.sublist(start, start + length);
    final end = raw.indexOf(0);
    return utf8.decode(end < 0 ? raw : raw.sublist(0, end), allowMalformed: true);
  }

  var pos = 0;
  while (pos + 512 <= tar.length) {
    if (tar.sublist(pos, pos + 512).every((b) => b == 0)) break; // end of archive
    final name = field(pos, 100);
    final sizeText = field(pos + 124, 12).trim();
    final size = sizeText.isEmpty ? 0 : int.parse(sizeText, radix: 8);
    final type = tar[pos + 156];
    final prefix = field(pos + 257, 6).startsWith('ustar') ? field(pos + 345, 155) : '';
    final path = prefix.isEmpty ? name : '$prefix/$name';
    final start = pos + 512;
    if (type == 0 || type == 0x30) out[path] = tar.sublist(start, start + size); // '0' or NUL
    pos = start + ((size + 511) ~/ 512) * 512;
  }
  return out;
}

/// The stem for a layout name, any case; null if the library has no such layout.
String? layoutStem(String layout) {
  for (final e in kLayoutStems.entries) {
    if (e.key.toLowerCase() == layout.toLowerCase()) return e.value;
  }
  return null;
}

/// The files of the npm package (paths under `package/`) an app needs for [layouts]: the
/// script, the CSS, the images, and each layout's sharded database and font. Paths in the
/// result are relative to the bundle folder.
Map<String, List<int>> selectBundle(Map<String, List<int>> package, Iterable<String> layouts) {
  final files = <String, List<int>>{};
  package.forEach((path, data) {
    if (path.startsWith('package/')) files[path.substring('package/'.length)] = data;
  });
  final out = <String, List<int>>{};
  void take(String path) {
    final data = files[path];
    if (data == null) throw StateError('$path is missing from the package');
    out[path] = data;
  }

  take('dist/quran-madina-html.min.js');
  take('dist/quran-madina-html.min.css');
  files.keys.where((p) => p.startsWith('assets/img/')).forEach(take);
  for (final layout in layouts) {
    final stem = layoutStem(layout);
    if (stem == null) {
      throw ArgumentError('unknown layout "$layout" (use ${kLayoutStems.keys.join(', ')})');
    }
    final dir = 'assets/db/v2/$stem/';
    files.keys.where((p) => p.startsWith(dir)).forEach(take);
    final manifest = jsonDecode(utf8.decode(files['${dir}manifest.json'] ??
        (throw StateError('${dir}manifest.json is missing from the package'))));
    take(manifest['font_url'] as String);
  }
  return out;
}

/// The folders an app lists under `flutter: assets:` for [paths] (Flutter doesn't include
/// subfolders on its own), each under [root] and ending in '/'.
List<String> assetFolders(String root, Iterable<String> paths) {
  final dirs = paths.map((p) => p.contains('/') ? p.substring(0, p.lastIndexOf('/')) : '');
  return ({for (final d in dirs) d.isEmpty ? '$root/' : '$root/$d/'}).toList()..sort();
}
