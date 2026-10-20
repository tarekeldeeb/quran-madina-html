# Setup and tests

## Install

```bash
git clone https://github.com/tarekeldeeb/quran-madina-html
cd quran-madina-html
npm install

# Python, for the tests and the database builder (a venv keeps its pinned versions apart)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Build and run

```bash
npm run build     # scripts/build.mjs: jshint, then dist/ (readable script and CSS with the license banner)
npm run start     # serve the repository on http://localhost:8000
```

Then open <http://localhost:8000/demo/index.html>. On `localhost` the script loads its files
from `../`, so the demo uses the repository's own `dist/` and `assets/`.

## Tests

```bash
npm test                                   # all Python tests
python -m pytest test/db_test.py           # database checks (no browser)
python -m pytest test/render_test.py       # rendering, in Chrome via Selenium; needs `npm run start`
python -m pytest test/v2_layout_test.py    # line breaks and gaps against the print
```

React wrapper:

```bash
cd react && npm install && npm test
```

The Flutter wrapper is checked on GitHub (the `Flutter` workflow: analysis, tests, a pub.dev
dry run, and web and Android builds of the example). Locally, with Flutter installed:

```bash
cd flutter && flutter pub get && flutter analyze && flutter test
```

## Docs

```bash
pip install mkdocs-material
mkdocs serve      # http://127.0.0.1:8000/quran-madina-html/docs/
```

Pages are Markdown in `docs/`, the menu is in `mkdocs.yml`. A raw `<quran-madina-html>` tag in a
page renders live: the site loads the latest 2.x from unpkg.

## README images

```bash
npm run start
python scripts/readme_gif.py           # docs/assets/img/showcase.gif, the README animation
python scripts/readme_screenshots.py   # the still screenshots in demo/img
```
