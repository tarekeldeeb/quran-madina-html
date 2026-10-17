import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:quran_madina_flutter/quran_madina_flutter.dart';

void main() => runApp(const ExampleApp());

class ExampleApp extends StatefulWidget {
  const ExampleApp({super.key});

  @override
  State<ExampleApp> createState() => _ExampleAppState();
}

class _ExampleAppState extends State<ExampleApp> {
  // Offline needs the bundled files: `dart run quran_madina_flutter:bundle` (see README.md).
  // On the web the library is set up once per page, so the web build always uses the bundle.
  bool _offline = kIsWeb;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'quran_madina_flutter',
      home: Scaffold(
        appBar: AppBar(
          title: const Text('quran_madina_flutter'),
          actions: [
            if (!kIsWeb) ...[
              const Center(child: Text('offline')),
              Switch(value: _offline, onChanged: (v) => setState(() => _offline = v)),
            ],
          ],
        ),
        body: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // A verse range with marked words and emphasised letters
            QuranMadinaFlutter(
              sura: 1,
              aya: '2-4',
              headless: true,
              highlight: '1',
              error: '4',
              letters: '1:3, 4:3+5 lapis blink, 6:4 emerald',
              fontSize: 20,
              bundled: _offline,
            ),
            const SizedBox(height: 24),
            // A full page
            QuranMadinaFlutter(page: 50, headless: true, fontSize: 20, bundled: _offline),
          ],
        ),
      ),
    );
  }
}
