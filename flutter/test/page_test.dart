import 'package:flutter_test/flutter_test.dart';
import 'package:quran_madina_flutter/quran_madina_flutter.dart';
import 'package:quran_madina_flutter/src/page.dart' show actionsScript, isLibraryScript, updateScript;

void main() {
  group('tagAttributes', () {
    test('page wins over sura/aya', () {
      expect(tagAttributes(page: 106, sura: 2, aya: '255'), {'page': '106'});
    });

    test('sura/aya with marks and letters', () {
      expect(
        tagAttributes(
            sura: 1, aya: '2-4', highlight: '1', error: '4', letters: '1:3, 4:3-5 emerald blink'),
        {
          'sura': '1',
          'aya': '2-4',
          'highlight': '1',
          'error': '4',
          'letters': '1:3, 4:3-5 emerald blink',
        },
      );
    });

    test('booleans become empty attributes; false, null and empty are left out', () {
      expect(tagAttributes(page: 3, headless: true, notitle: false, words: '', quotes: null),
          {'page': '3', 'headless': ''});
    });
  });

  group('attributeUpdates', () {
    test('changed, added and removed attributes', () {
      final from = {'sura': '1', 'aya': '1', 'highlight': '2'};
      final to = {'sura': '1', 'aya': '2', 'letters': '1:3'};
      expect(attributeUpdates(from, to), {'aya': '2', 'letters': '1:3', 'highlight': null});
    });

    test('nothing to do when equal', () {
      expect(attributeUpdates({'page': '1'}, {'page': '1'}), isEmpty);
    });

    test('update script passes nulls through for removal', () {
      expect(updateScript({'aya': '2', 'highlight': null}),
          'qmhSet({"aya":"2","highlight":null});');
    });
  });

  group('buildPage', () {
    test('loader settings go on the script tag', () {
      final html = buildPage(
          const QuranLoader(layout: 'IndoPak', fontSize: 22), tagAttributes(page: 50));
      expect(html, contains('<script src="$kDefaultSrc" data-cdn="$kDefaultCdn"'
          ' data-layout="IndoPak" data-font-size="22"></script>'));
      expect(html, contains('<quran-madina-html id="qmh" page="50"></quran-madina-html>'));
    });

    test('defaults: no layout or size attributes, transparent background', () {
      final html = buildPage(const QuranLoader(), tagAttributes(page: 1));
      expect(html, isNot(contains('data-layout')));
      expect(html, isNot(contains('data-font-size')));
      expect(html, contains('background: transparent'));
    });

    test('attribute values are escaped', () {
      final html = buildPage(const QuranLoader(), {'letters': '1:3 "x"<y>'});
      expect(html, contains('letters="1:3 &quot;x&quot;&lt;y&gt;"'));
    });

    test('boolean attributes have no value', () {
      final html = buildPage(const QuranLoader(), tagAttributes(page: 2, headless: true));
      expect(html, contains('<quran-madina-html id="qmh" page="2" headless></quran-madina-html>'));
    });

    test('text colour reaches the page (dark mode)', () {
      final html = buildPage(const QuranLoader(textColor: '#ece6d6'), tagAttributes(page: 1));
      expect(html, contains('color: #ece6d6'));
    });
  });

  group('verse actions', () {
    test('actions attribute: joined, an empty list means none', () {
      expect(tagAttributes(sura: 2, aya: '255', actions: ['copy', 'bookmark'])['actions'],
          'copy bookmark');
      expect(tagAttributes(sura: 2, aya: '255', actions: [])['actions'], 'none');
      expect(tagAttributes(sura: 2, aya: '255').containsKey('actions'), isFalse);
    });

    test('the page registers the actions and posts a choice back', () {
      final html = buildPage(const QuranLoader(), tagAttributes(sura: 2, aya: '255'),
          actions: const [QuranAyaAction(id: 'bookmark', icon: '<svg></svg>')]);
      expect(html, contains('function qmhActions(list)'));
      expect(html, contains('qmhPost("action"'));
      expect(html, contains('qmhActions([{"id":"bookmark","title":"bookmark","icon":"<svg><\\/svg>","order":100}]);'));
      expect(buildPage(const QuranLoader(), tagAttributes(page: 1)), isNot(contains('qmhActions([')));
    });

    test('a choice from the page becomes a QuranAyaSelection', () {
      final s = QuranAyaSelection.fromJson({
        'id': 'bookmark', 'sura': 2, 'aya': 255, 'page': 42, 'text': 'x', 'suraName': 'n',
        'layout': '1441H',
      })!;
      expect([s.id, s.sura, s.aya, s.page, s.text, s.layout], ['bookmark', 2, 255, 42, 'x', '1441H']);
      expect(QuranAyaSelection.fromJson({'id': 'x'}), isNull);
      expect(QuranAyaSelection.fromJson('nope'), isNull);
    });

    test('actions compare by value, so an unchanged list is not sent again', () {
      expect(const QuranAyaAction(id: 'a', title: 'A'), const QuranAyaAction(id: 'a', title: 'A'));
      expect(actionsScript(const [QuranAyaAction(id: 'a')]),
          'qmhActions([{"id":"a","title":"a","icon":null,"order":100}]);');
    });
  });

  group('bundled loader', () {
    test('resolves the placeholder to where the platform serves the bundle', () {
      const loader = QuranLoader(src: kBundledSrc, cdn: kBundledCdn, layout: 'IndoPak');
      expect(loader.bundled, isTrue);
      final served = loader.resolveBundle('http://127.0.0.1:4321/');
      expect(served.src, 'http://127.0.0.1:4321/dist/quran-madina-html.js');
      expect(served.cdn, 'http://127.0.0.1:4321/');
      expect(served.layout, 'IndoPak');
      expect(served.bundled, isFalse);
    });

    test('leaves other loaders alone', () {
      const loader = QuranLoader();
      expect(loader.bundled, isFalse);
      expect(loader.resolveBundle('http://127.0.0.1:1/'), loader);
    });
  });

  test('isLibraryScript knows the library from other scripts', () {
    expect(isLibraryScript(kDefaultSrc), isTrue);
    expect(isLibraryScript('https://unpkg.com/quran-madina-html@2.1.0/'), isTrue);
    expect(isLibraryScript('https://cdn.example/dist/quran-madina-html.js?v=2'), isTrue);
    expect(isLibraryScript('http://127.0.0.1:9/dist/quran-madina-html.js'), isTrue);
    expect(isLibraryScript('https://unpkg.com/quran-madina-html@2.1.1/dist/quran-madina-html.min.js'), isTrue);
    expect(isLibraryScript('/quran-madina-html/flutter/main.dart.js'), isFalse);
    expect(isLibraryScript('https://x.github.io/quran-madina-html/flutter/flutter.js'), isFalse);
  });
}
