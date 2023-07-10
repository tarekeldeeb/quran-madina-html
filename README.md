# Quran Madina Html (no-images)
[![pylint](https://github.com/tarekeldeeb/quran-madina-html-no-images/actions/workflows/pylint.yml/badge.svg)](https://github.com/tarekeldeeb/quran-madina-html-no-images/actions/workflows/pylint.yml)
[![db_test](https://github.com/tarekeldeeb/quran-madina-html-no-images/actions/workflows/db_test.yml/badge.svg)](https://github.com/tarekeldeeb/quran-madina-html-no-images/actions/workflows/db_test.yml)
[![npm-grunt](https://github.com/tarekeldeeb/quran-madina-html-no-images/actions/workflows/npm-grunt.yml/badge.svg)](https://github.com/tarekeldeeb/quran-madina-html-no-images/actions/workflows/npm-grunt.yml)

A Madina Quran HTML Renderer without images

Theres a pre-processing python script to generate Json databases with quran text with special metadata. The preprocessing is based on text from [Tanzil](tanzil.net), and the OCR DB from [Murtaza Raja](https://github.com/murtraja/quran-android-images-helper) helper project.
Afterwards, the JS library uses those Json objects to render Madina-based Quran pages and lines.

The main purpose of this library is:
* Render Quran text that's visually similar to Madina Printed Pages
* Efficient Loading of Quran Visual Text (Not image-based, but pure Html)
* Easy to use: just a simple HTML tag! Example
```html
<quran-madina-html sura="2" aya="8-10"></quran-madina-html>
```

# Dev Setup

```
Fork this repo, rename it, then clone it.

$ npm install	// install bower tasks
$ bower install	// install components
$ grunt build   // build the dependencies

```

# Demo

Coming Soo ..

# Links

[X-Tags Docs](http://x-tags.org/docs)
