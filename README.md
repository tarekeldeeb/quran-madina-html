# Quran Madina Html (no-images)
[![pylint](https://github.com/tarekeldeeb/quran-madina-html/actions/workflows/pylint.yml/badge.svg)](https://github.com/tarekeldeeb/quran-madina-html/actions/workflows/pylint.yml)
[![db_test](https://github.com/tarekeldeeb/quran-madina-html/actions/workflows/db_test.yml/badge.svg)](https://github.com/tarekeldeeb/quran-madina-html/actions/workflows/db_test.yml)
[![npm-grunt](https://github.com/tarekeldeeb/quran-madina-html/actions/workflows/npm-grunt.yml/badge.svg)](https://github.com/tarekeldeeb/quran-madina-html/actions/workflows/npm-grunt.yml)

A Madina Quran HTML Renderer without images

Theres a pre-processing python script to generate Json databases with quran text with special metadata. The preprocessing is based on text from [Tanzil](tanzil.net), and the OCR DB from [Murtaza Raja](https://github.com/murtraja/quran-android-images-helper) helper project.
Afterwards, the JS library uses those Json objects to render Madina-based Quran pages and lines.

The main purpose of this library is:
* Render Quran text that's visually similar to Madina Printed Pages
* Efficient Loading of Quran Visual Text (Not image-based, but pure Html)
* Easy to use: just a simple HTML tag! 

# Getting Started
In your Html header, add this script:
```html
  <script type="text/javascript" src="https://unpkg.com/quran-madina-html" data-name="Madina" data-font="Uthman"></script>
```
* Supported ``data-font`` parameters are: Amiri (default), Uthman, Hafs
* Other options include: ``data-font-size`` which defaults to 16 (px)

Then in your body, just add the tag.
```html
<quran-madina-html sura="2" aya="8-10"></quran-madina-html>
```
 If the selected aya(s) fit on a single line, the default is to generate an inline ``<span>`` element, otherwise a ``<div>`` is generated.
  
# Dev Setup

The project is published on npm ``npm install quran-madina-html``, with sources, assets and distributables.
Alternatively, you can fork this repo, then clone it.

```
$ npm install	// install bower tasks
$ bower install	// install components
$ grunt // build the dist with dependencies

```

# Demo

https://tarekeldeeb.github.io/quran-madina-html/demo/index.html

Don't forget to see the page source!

# Links

[X-Tags Docs](http://x-tags.org/docs)
