import 'package:flutter/material.dart';
import 'package:quran_madina_flutter/quran_madina_flutter.dart';

void main() => runApp(const ExampleApp());

class ExampleApp extends StatelessWidget {
  const ExampleApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'quran_madina_flutter',
      home: Scaffold(
        appBar: AppBar(title: const Text('quran_madina_flutter')),
        body: ListView(
          padding: const EdgeInsets.all(16),
          children: const [
            // A verse range with marked words and emphasised letters
            QuranMadinaHtml(
              sura: 1,
              aya: '2-4',
              headless: true,
              highlight: '1',
              error: '4',
              letters: '1:3, 4:3+5 lapis blink, 6:4 emerald',
              fontSize: 22,
            ),
            SizedBox(height: 24),
            // A full page
            QuranMadinaHtml(page: 50, headless: true, fontSize: 20),
          ],
        ),
      ),
    );
  }
}
