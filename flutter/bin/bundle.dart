// Copies quran-madina-html (script, CSS, databases, fonts) into the app's assets, so
// QuranMadinaFlutter(bundled: true) renders offline. Run from the app's folder:
//
//   dart run quran_madina_flutter:bundle                    # the 1441H layout
//   dart run quran_madina_flutter:bundle --layouts 1441H,IndoPak
//   dart run quran_madina_flutter:bundle --version 2.1.0    # another library version
//   dart run quran_madina_flutter:bundle --from ../quran-madina-html   # a local checkout (built)
import 'dart:io';

import 'package:quran_madina_flutter/src/bundle.dart';
import 'package:quran_madina_flutter/src/page.dart' show kBundleDir;
import 'package:quran_madina_flutter/src/version.dart';

Future<void> main(List<String> args) async {
  var layouts = ['1441H'];
  var version = kLibraryVersion;
  String? from;
  for (var i = 0; i < args.length; i++) {
    final arg = args[i];
    String value() {
      if (arg.contains('=')) return arg.substring(arg.indexOf('=') + 1);
      if (i + 1 >= args.length) _fail('$arg needs a value');
      return args[++i];
    }

    if (arg.startsWith('--layouts')) {
      layouts = value().split(',').map((s) => s.trim()).where((s) => s.isNotEmpty).toList();
    } else if (arg.startsWith('--version')) {
      version = value();
    } else if (arg.startsWith('--from')) {
      from = value();
    } else if (arg == '-h' || arg == '--help') {
      stdout.writeln('usage: dart run quran_madina_flutter:bundle '
          '[--layouts 1441H,1405H,IndoPak] [--version $kLibraryVersion | --from <folder>]');
      return;
    } else {
      _fail('unknown option $arg');
    }
  }
  if (!File('pubspec.yaml').existsSync()) _fail('run this from your app\'s folder');

  final Map<String, List<int>> package;
  if (from != null) {
    final dir = Directory(from);
    if (!dir.existsSync()) _fail('no folder $from');
    stdout.writeln('Reading ${dir.path}');
    package = readFolder(dir);
  } else {
    package = readTarGz(await _download(version));
  }

  final Map<String, List<int>> files;
  try {
    files = selectBundle(package, layouts);
  } on Object catch (e) {
    _fail('$e');
  }
  final root = Directory(kBundleDir);
  if (root.existsSync()) root.deleteSync(recursive: true);
  var bytes = 0;
  files.forEach((path, data) {
    File('$kBundleDir/$path')
      ..createSync(recursive: true)
      ..writeAsBytesSync(data);
    bytes += data.length;
  });
  stdout
    ..writeln('Wrote ${files.length} files (${(bytes / 1048576).toStringAsFixed(1)} MB) '
        'to $kBundleDir/ for ${layouts.join(', ')}.')
    ..writeln()
    ..writeln('Make sure your pubspec.yaml lists these folders:')
    ..writeln()
    ..writeln('flutter:')
    ..writeln('  assets:');
  for (final folder in assetFolders(kBundleDir, files.keys)) {
    stdout.writeln('    - $folder');
  }
}

Future<List<int>> _download(String version) async {
  final url = 'https://registry.npmjs.org/quran-madina-html/-/quran-madina-html-$version.tgz';
  stdout.writeln('Downloading $url');
  final client = HttpClient();
  try {
    final response = await (await client.getUrl(Uri.parse(url))).close();
    if (response.statusCode != 200) _fail('download failed: HTTP ${response.statusCode}');
    return [for (final chunk in await response.toList()) ...chunk];
  } finally {
    client.close();
  }
}

Never _fail(String message) {
  stderr.writeln('quran_madina_flutter:bundle: $message');
  exit(1);
}
