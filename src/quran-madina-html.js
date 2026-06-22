(
  function(){
  var name = "quran-madina-html";
  var cdn = (/localhost/.test(document.location.hostname))? "../":`https://www.unpkg.com/${name}/`;
  function loadJSON(path, success, error){
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function()
    {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
                if (success)
                    success(JSON.parse(xhr.responseText));
            } else {
                if (error)
                    error(xhr);
            }
        }
    };
    xhr.open("GET", path, true);
    xhr.send();
  }
  function hoverByType(class_name, type="class", color_bg="lightgrey", color_out="transparent"){
    var elms = (type.toLowerCase() === "tag") ? document.getElementsByTagName(class_name)  
                                              : document.getElementsByClassName(class_name);
    Array.from(elms).forEach(function(elm) {
      elm.onmouseover = function() {
        Array.from(elms).forEach(function(element) {
          element.style.backgroundColor = color_bg;
        });
      };
      elm.onmouseout = function() {
        Array.from(elms).forEach(function(element) {
          element.style.backgroundColor = color_out;
        });
      };
    });
  }
  function parseSuraRange(str){
    // Sura count is 0-based, we need to subtract 1
    return Array(2).fill(str.split('-')[0]-1);
  }
  function parseAyaRange(str){
    // Aya count is 0-based, there are 2 extra ayas (Title + Basmala)
    if (str.split('-').length == 2) return str.split('-').map(elem => parseInt(elem) +1);
    return Array(2).fill(parseInt(str.split('-')[0])+1);
  }
  // Aya-number ornaments (ornate parens for Hafs/Uthman/me_quran, end-of-aya for Amiri).
  // These are markers, not words, so they never count towards the words= index.
  var AYA_MARKER = /[﴿﴾۝]/;
  function isTrue(val){
    // Boolean HTML attribute: true when present as `headless`, `headless=""`, "true", "1" or "yes".
    if(val == null) return false;
    var v = String(val).trim().toLowerCase();
    return v === "" || v === "true" || v === "1" || v === "yes";
  }
  function parseWordsRange(str){
    // 1-based, inclusive. "n" => [n,n]; "n:m" or "n-m" => [n,m]. Returns null if malformed.
    if(str == null) return null;
    var parts = str.split(/[-:]/).map(elem => parseInt(elem, 10));
    if(parts.length == 1) parts = [parts[0], parts[0]];
    if(parts.length != 2 || isNaN(parts[0]) || isNaN(parts[1])) return null;
    return parts;
  }
  function countAyaWords(aya){
    // Number of selectable words in an aya (whitespace-separated, excluding aya-number markers).
    var n = 0;
    aya.r.forEach(function(part){
      part.t.split(/\s+/).forEach(function(token){
        if(token !== "" && !AYA_MARKER.test(token)) n = n + 1;
      });
    });
    return n;
  }
  function appendWords(parent, text, range, counter){
    // Render each whitespace-separated word as its own span so non-selected words can be
    // hidden in place (visibility:hidden) while keeping the original Madina line geometry.
    // `counter` is the running 1-based word index across the whole selection (spans ayas).
    text.split(/(\s+)/).forEach(function(token){
      if(token === "") return;
      if(/^\s+$/.test(token)){ parent.appendChild(document.createTextNode(token)); return; }
      var span = document.createElement("span");
      span.textContent = token;
      span.classList.add(`${name}-word`);
      if(AYA_MARKER.test(token)){
        span.classList.add(`${name}-word-hidden`); // ornament: never a selectable word
      } else {
        counter = counter + 1;
        if(counter < range[0] || counter > range[1]) span.classList.add(`${name}-word-hidden`);
      }
      parent.appendChild(span);
    });
    return counter;
  }
  function partOnLine(aya, line_no){
    // The aya's render part that falls on the given page-line, or null.
    for(var k = 0; k < aya.r.length; k++){ if(aya.r[k].l === line_no) return aya.r[k]; }
    return null;
  }
  function lineContext(sura_idx, page, line_no, aya_idx, dir){
    // Parts on (page, line_no) that lie outside the selection on one side, in reading order. dir<0
    // walks back from the first selected aya (text preceding it); dir>0 walks forward from the last
    // selected aya (text following it). Rendering these invisibly lets the line's own centering or
    // stretch place the visible text exactly where it sits on the full page.
    var ayas = madina_data.suras[sura_idx].ayas, parts = [];
    for(var a = aya_idx + dir; a >= 0 && a < ayas.length; a += dir){
      if(ayas[a].p != page) break;
      var match = partOnLine(ayas[a], line_no);
      if(match === null) break;
      if(dir < 0){ parts.unshift(match); if(match.o === 0) break; } // reached the line's right start
      else { parts.push(match); }
    }
    return parts;
  }
  function appendSpacers(line_el, parts){
    // Render parts as invisible spacers: they hold the line's layout but show nothing and are
    // excluded from copy-to-clipboard. Shared by the verse and words= render paths.
    for(var i = 0; i < parts.length; i++){
      var spacer = document.createElement("div");
      spacer.textContent = parts[i].t;
      spacer.style.cssText = 'display:inline;visibility:hidden';
      line_el.appendChild(spacer);
    }
  }
  function collectWordParts(sura_start, aya_start, range){
    // Walk ayas in reading order from (sura_start, aya_start), crossing page AND sura
    // boundaries, grouping parts into visual lines keyed by (page, line), until the end word
    // index is covered. Aya indices 0/1 of each sura are the name/basmala decoration: rendered
    // for context but not counted as words (countable=false).
    var groups = [];
    var current = null;
    var counted = 0;
    for(var s = sura_start; s < madina_data.suras.length; s++){
      var ayas = madina_data.suras[s].ayas;
      var aya_begin = (s === sura_start) ? aya_start : 0;
      var reached = false;
      for(var a = aya_begin; a < ayas.length; a++){
        var countable = (a >= 2);
        var aya = ayas[a];
        for(var pi = 0; pi < aya.r.length; pi++){
          var part = aya.r[pi];
          var key = `${aya.p}:${part.l}`;
          if(!current || current.key !== key){
            current = {key: key, offset: part.o, stretch: part.s, parts: []};
            groups.push(current);
          }
          current.parts.push({sura: s, ayaIdx: a, part: part, countable: countable});
        }
        if(countable){
          counted = counted + countAyaWords(aya);
          if(counted >= range[1]){ reached = true; break; }
        }
      }
      if(reached) break;
    }
    return groups;
  }
  function renderWordsSpan(tag, sura_start, aya_start, range, headless){
    // Dedicated render path for the words= selection. Unlike the page/aya loop it is not bound
    // to a single page or sura, so a word range can span both.
    var groups = collectWordParts(sura_start, aya_start, range);
    var multiline = groups.length > 1;
    var counter = 0; // running 1-based word index from the start aya, drives word visibility
    tag.innerHTML = "";
    tag.removeAttribute('style');
    if(multiline){
      tag.style = "display:block;";
      tag.style.setProperty('font-family', madina_data.font_family, '');
      tag.style.setProperty('font-size', madina_data.font_size+"px", '');
      if(madina_data.font_family === "me_quran"){
        tag.style.setProperty('line-height', madina_data.font_size*2+"px", '');
      }
      tag.style.width = (madina_data.line_width+10)+"px";
      let start_page = madina_data.suras[sura_start].ayas[aya_start].p;
      tag.style.setProperty('box-shadow', 'inset '+(start_page%2==1?"":"-")+'8px 0 7px -7px #333', '');
      if(!headless){
        let header = document.createElement("quran-madina-html-header");
        header.innerHTML = madina_data.suras[sura_start].name;
        let copy = getCopyIcon(); copy.addEventListener("click", copyToClipboard);
        let translation = getTranslateIcon(); translation.addEventListener("click", openTranslate);
        header.appendChild(copy); header.appendChild(translation);
        tag.appendChild(header);
      }
    }
    groups.forEach(function(group, gi){
      var line = document.createElement("quran-madina-html-line");
      if(multiline){
        line.style.setProperty('display', 'block', '');
        if(group.stretch >= 0){
          line.style.setProperty("transform", `scaleX(${group.stretch})`, "");
        } else {
          line.style.setProperty("text-align", "center", "");
        }
        if(group.offset > 0 && gi === 0){
          // The selection begins mid-line: rebuild the preceding text invisibly so the line's own
          // centering/stretch positions the first word exactly as it sits on the page.
          var first = group.parts[0];
          appendSpacers(line, lineContext(first.sura,
            madina_data.suras[first.sura].ayas[first.ayaIdx].p, first.part.l, first.ayaIdx, -1));
        } else if(group.offset > 0){
          line.style.setProperty('padding-right', group.offset+"px", '');
          line.style.setProperty('transform-origin', "left");
        }
      } else {
        line.style.setProperty('font-family', madina_data.font_family, '');
        line.style.setProperty('font-size', madina_data.font_size+"px", '');
      }
      tag.appendChild(line);
      group.parts.forEach(function(item){
        var aya_part = document.createElement("div");
        var classes = getAyaClass(item.sura+1, item.ayaIdx-1);
        DOMTokenList.prototype.add.apply(aya_part.classList, classes);
        if(item.countable){
          counter = appendWords(aya_part, item.part.t, range, counter);
        } else {
          aya_part.textContent = item.part.t; // sura name / basmala: always visible
        }
        aya_part.style.cssText = 'display:inline';
        line.appendChild(aya_part);
        hoverByType(classes.slice(-1)[0]);
      });
      if(multiline && gi === groups.length - 1){
        // The selection ends mid-line: rebuild the following text invisibly to keep the last line
        // laid out (and centered) exactly as on the page.
        var last = group.parts[group.parts.length - 1];
        appendSpacers(line, lineContext(last.sura,
          madina_data.suras[last.sura].ayas[last.ayaIdx].p, last.part.l, last.ayaIdx, 1));
      }
    });
    if(!multiline && !headless){
      let tag_copy = document.createElement("quran-madina-html-copy");
      let copy = getCopyIcon(); copy.addEventListener("click", copyToClipboard);
      tag_copy.appendChild(copy);
      tag.appendChild(tag_copy);
    }
  }
  function getAyaClass(sura, aya){
    const zeroPad = (num, places) => String(num).padStart(places, '0');
    const classes = [`${name}-part`, `${name}-${zeroPad(sura,3)}-${zeroPad(aya,3)}`];
    if(aya == -1) classes.push("quran-madina-html-sura-start"); // Decorate Sura Name
    return classes;
  }
  function getCopyIcon(){
    let htmlString = '<svg viewBox="0 0 24 24" class="quran-madina-html-icon" width="20px">'+
      '<path d="M16.02 20.96H3.78c-.41 0-.75-.34-.75-.75V7.74c0-.41.34-.75.75-.75h7.87c.21 0 '+
      '.39.08.53.22l4.37 4.37c.14.14.22.32.22.53v8.11c0 .4-.34.74-.75.74ZM4.53 19.47h10.75v-6'+
      '.61h-3.62c-.41 0-.75-.34-.75-.75V8.48H4.53v10.99Z"></path><path d="m20.74 7.63-4.37-4.'+
      '37c-.14-.14-.36-.2-.53-.22H8.01c-.41 0-.75.34-.75.75V5.5h1.49v-.97h6.34v3.62c0 .41.34.'+
      '75.75.75h3.62v8.19h-1.2v1.49h1.95c.41 0 .75-.34.75-.75V8.16c0-.21-.08-.4-.22-.53Z">'+
      '</path></svg>';
      var div = document.createElement('div');
      div.innerHTML = htmlString.trim();
      return div.firstChild;
  }
  function getTranslateIcon(){
    let htmlString = '<svg class="quran-madina-html-icon" viewBox="0 0 820 615" style="height:20px"><path d="M70 '+
    '1.9C37.6 8.8 12.6 33.4 3.4 67.5c-1.8 6.6-1.9 11.9-1.9 98v91l2.3 8c5.1 17.8 17 36.4 29.9 46.7 '+
    '10.8 8.6 25.4 15.4 38.1 17.8 3.1.6 15.2 1 26.8 1 17.7 0 21.3.2 21.7 1.4.4.9.6 17.1.7 36.1 0 '+
    '32.4.2 34.9 2 38.5 6.4 12.5 21.4 17.4 33.3 10.8 2.3-1.3 7.5-6.4 12.1-11.9l63-74.1c.6-.4 16.3-.8 '+
    '34.9-.8H300l-.2-18.3-.3-18.2-42.8.1-43.1.5c-.2.2-12.7 15.1-27.9 33.1-15.1 18-27.8 32.4-28.1 '+
    '32.1-.3-.4-.6-15.3-.6-33.2v-32.6l-38.8-.1c-42.1-.2-43.9-.4-54.3-6-6.5-3.6-16.9-14.6-20.2-21.5-5.8'+
    '-11.9-5.7-10-5.7-100.7 0-92-.2-89.4 6.3-101.7 3.9-7.3 13.5-17.1 20.3-20.7C76 36.7 66.1 37 244.5 '+
    '37L412 38.1c18 4.1 33.5 20.5 37.5 39.6 2.2 10.2 2.1 164.6 0 174.8-3.9 18.3-16.4 32.7-33.5 '+
    '38.5-3.2 1.1-7.8 2-10 2-3.1 0-4 .4-4 1.7 0 1-.2 8.8-.3 17.3-.2 8.5-.2 16.2 0 17 .9 3.3 21.7-.5 '+
    '34.1-6 13.7-6.3 27.5-17.9 36.2-30.5 5-7.2 10.8-20.4 13.2-30.1l2.3-8.9V165 '+
    '76.5l-2.3-9c-8.1-31.4-30.5-54.9-61.7-64.8l-7-2.2-169-.2C87.7.1 78 .2 70 1.9zm277.294 '+
    '102.559q19.5-.5 28.25 24.5 2.5 7.25-3.75 19.75-5.75 11.75-9.75 16-19.5 21.5-67 25.25-27.75 '+
    '2.25-50.25-2.25-5.25 38.25-16.5 50-26 26.75-66 29.5-27.75 2-42.5-11-20.25-17.75-16.5-48.5 '+
    '3-23.75 14.25-42.5 2.75-4.5 4.75-7.5 2-3 3-4.25 2.25-2.75 4.75-1.25 2.75 1.5 0 6.25-12.75 '+
    '24.5-10 45 4 30.5 44.5 30.5 30.25 0 53.25-15.5 12.5-8.25 '+
    '14.75-14.25-2.25-20.75-13.75-35.75-3.5-4.25-1.75-8l9.5-23.5q3-7.5 8.25 1.25l8.75 14.75q7.75 4.25 '+
    '28.25 5 16.75-19.25 39.25-36.25 22.5-16.75 36.25-17.25zm11.5 40.5q-12.5-9.5-31.75-5.75-19 '+
    '3.75-41.25 19.5 50.75.5 73-13.75zm-71.5-89.75q1.5-2 4.25-1.25 5 1.75 9.5 4.5 4.75 2.75 8.75 6.25 '+
    '2 2 .75 4.5l-12 19q-1.75 2.5-4.5.5-2.5-2-18-11.25-2.75-1.75-1-4.25zm278.784 '+
    '232.623c-4.7.4-4.7.4-6.7 6.1-1.2 3.1-9.3 25.9-18 50.7l-36.6 102.7-3.5 9.8h17.9 17.8l5.7-17 '+
    '5.7-17h31.7 31.8l5.6 17.2 5.6 17.3 17.9-.3 '+
    '18-.3-6-17.2-15-43.2-13.3-38.5-14.1-41-9.9-28.7c-.3-.6-30.2-1.1-34.6-.6zm35.7 106c-.2.2-10 '+
    '.2-21.9.1l-21.5-.3 9.8-29.5 11-32.5c1.2-2.9 1.8-1.4 12.1 29.4l10.5 32.8zm148.8 139.609c32.4-6.9 '+
    '57.4-31.5 66.6-65.6 1.8-6.6 1.9-11.9 '+
    '1.9-98v-91l-2.3-8c-5.1-17.8-17-36.4-29.9-46.7-10.8-8.6-25.4-15.4-38.1-17.8-3.1-.6-15.2-1-26.8-1-1'+
    '7.7 0-21.3-.2-21.7-1.4-.4-.9-.6-17.1-.7-36.1 '+
    '0-32.4-.2-34.9-2-38.5-6.4-12.5-21.4-17.4-33.3-10.8-2.3 1.3-7.5 6.4-12.1 11.9l-63 '+
    '74.1c-.6.4-16.3.8-34.9.8h-33.7l.2 18.3.3 18.2 42.8-.1 43.1-.5c.2-.2 12.7-15.1 27.9-33.1 15.1-18 '+
    '27.8-32.4 28.1-32.1.3.4.6 15.3.6 33.2v32.6l38.8.1c42.1.2 43.9.4 54.3 6 6.5 3.6 16.9 14.6 20.2 '+
    '21.5 5.8 11.9 5.7 10 5.7 100.7 0 92 .2 89.4-6.3 101.7-3.9 7.3-13.5 17.1-20.3 20.7-11.4 6.1-1.5 '+
    '5.8-179.9 5.8-108.2 0-164.5-.4-167.5-1.1-18-4.1-33.5-20.5-37.5-39.6-2.2-10.2-2.1-164.6 0-174.8 '+
    '3.9-18.3 16.4-32.7 33.5-38.5 3.2-1.1 7.8-2 10-2 3.1 0 4-.4 4-1.7 0-1 .2-8.8.3-17.3.2-8.5.2-16.2 '+
    '0-17-.9-3.3-21.7.5-34.1 6-13.7 6.3-27.5 17.9-36.2 30.5-5 7.2-10.8 20.4-13.2 30.1l-2.3 8.9v88.5 '+
    '88.5l2.3 9c8.1 31.4 30.5 54.9 61.7 64.8l7 2.2 169 .2 177.5-1.6z"/></svg>';
    var div = document.createElement('div');
    div.innerHTML = htmlString.trim();
    return div.firstChild;
  }
  function getLoadingIcon(){
    return '<img src="data:image/png;base64,R0lGODlhIAAKAPQVALSytMzOzLy6vPz6/NTW1LS2tNTS1Ly+vPz+'+
    '/AQCBFxaXOzu7BwaHCQmJGxubCwuLBQWFGRmZPT29CwqLHx6fAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'+
    'CH/C05FVFNDQVBFMi4wAwEAAAAh+QQFEAAVACwAAAAAIAAKAAAFYyBCHEJZGkMlkuaBqtTTzLMjjUCuA0GF77keJUEsEi'+
    'MsYK6SVFYeRiOjCWQqdc9oEWK6Wq+FrDbBBYcLZrG2DP56G2Myded2QscQA7gX2FcccQoDfWg7CCqEQIcSEQwQj4+CIQA'+
    'h+QQFEAAVACwLAAAAFQAKAAAFSOBAPU1ZOlKFEIfguoaYzPQcVSyg70Dw1DVGpcXjNYA0yLBoRM6UL2bh6IRKdVSk9fqr'+
    'Lq8OZ0LxlUoiDIharVioAoX4LiAJAQAh+QQFEAAVACwAAAAAHgAKAAAFXeBAPU1ZOlKFEIfgusagsq9LJXiORxUN/MBA'+
    'D0h86HSMSotIVDJ/jWMO4nz+qsyJFEetPbHFbaJrvRas2i25DAYa1e3mkukQK+I/YcAqiTAggIAKCzNnhj8IhYcFIQAh'+
    '+QQFEAAJACwAAAAAIAAKAAAEOhCRI2o1I+nNu08TII5A8J0fRZJou6mrmBwuasVF3cLxrKc4Ge3X4a2IH0PQhOwMAoUo'+
    'CZHIaFiuQQQAOw==" alt="Loading .." />';
  }
  function print(str){
    console.log(`${name}> ${str}`);
  }
  function copyToClipboard(){
    textWithHeader = this.parentElement.parentElement.innerText.split("\n");
    if(textWithHeader.length > 1){
      text = textWithHeader.slice(1).join(" ") + "\n\n" + textWithHeader[0];
    } else {
      let sura_index = this.parentElement.parentElement.getAttribute("sura");
      text = textWithHeader[0]+ "\n\n" + madina_data.suras[sura_index-1].name;
    }
    navigator.clipboard.writeText(text);
    alert("\u2398 تم نسخ:\n\n" + text);
  }
  function openTranslate(){
    let host = this.parentElement.parentElement;
    if(host.getAttribute("sura") != null && host.getAttribute("aya") != null){
      let sura_index = host.getAttribute("sura");
      let aya_index = host.getAttribute("aya");
      URL = `https://quran.com/${sura_index}/${aya_index}`;
    } else {
      let page_index = host.getAttribute("page");
      URL = `https://quran.com/page/${page_index}`;
    }
    window.open(URL, '_blank');
  }
  var madina_data = {"content":"Loading .."};
  var this_script = document.currentScript || document.querySelector(`script[src*="${name}"]`);
  var doc_name    = this_script.getAttribute('data-name') || "Madina05";
  var doc_font    = (this_script.getAttribute('data-font') || "me_quran").replaceAll(" ","_");
  var doc_font_sz = this_script.getAttribute('data-font-size') || 16;
  print(`${doc_name} with font: ${doc_font} size: ${doc_font_sz}`);
  const name_css = cdn+"dist/"+name+".min.css?v=1.1";
  if (!document.getElementById(name))
  {
      var head  = document.getElementsByTagName('head')[0];
      var link  = document.createElement('link');
      link.id   = name;
      link.rel  = 'stylesheet';
      link.type = 'text/css';
      link.href = name_css;
      link.media = 'all';
      head.appendChild(link);
  }
  loadJSON(`${cdn}assets/db/${doc_name}-${doc_font}-${doc_font_sz}px.json`,
        function(data) { 
          madina_data = data; 
          const myFont = new FontFace(madina_data.font_family, 'url('+encodeURI(madina_data.font_url)+')');
          myFont.load().then( () => {document.fonts.add(myFont);});
          xtag.register(name, {
            lifecycle: {
              created: function() {
                this.render(this);
              },
              inserted: function() {},
              removed: function() {},
              attributeChanged: function() {
                this.render(this);
              }
            }, 
            events: {},
            accessors: {
              page:{
                attribute: {},
                set: function(value) {
                  this.xtag.data.page = value;
                },
                get: function(){
                  return this.getAttribute("page");
                }
              },
              page_param:{
                attribute: {},
                set: function(value) {
                  this.xtag.data.page_param = value;
                },
                get: function(){
                  return this.getAttribute("page_param");
                }
              },
              aya:{
                attribute: {},
                set: function(value) {
                  this.xtag.data.aya = value;
                },
                get: function(){
                  return this.getAttribute("aya");
                }
              },
              sura:{
                attribute: {},
                set: function(value) {
                  this.xtag.data.sura = value;
                },
                get: function(){
                  return this.getAttribute("sura");
                }
              },
              words:{
                attribute: {},
                set: function(value) {
                  this.xtag.data.words = value;
                },
                get: function(){
                  return this.getAttribute("words");
                }
              },
              headless:{
                attribute: {},
                set: function(value) {
                  this.xtag.data.headless = value;
                },
                get: function(){
                  return this.getAttribute("headless");
                }
              }
            },
            methods: {
               render: function(tag){
                // Re-entrancy guard. While building we mutate the element's style attribute, and
                // x-tag re-invokes render() on any attribute change — that nested render would clear
                // and rebuild mid-build, duplicating the output. The guard drops such re-entrant
                // calls; genuine user-driven renders run when no render is in progress.
                if(this.xtag.data.rendering){ return; }
                this.xtag.data.rendering = true;
                try {
                  this.doRender(tag);
                } finally {
                  this.xtag.data.rendering = false;
                }
               },
               doRender: function(tag){
                var sura_from;
                var sura_to;
                var multiline;
                var aya_from;
                var aya_to;
                var line_from;
                var line_to;
                var words_range = null;
                // `page` is the page to render, derived locally. We deliberately never write derived
                // state (sura/aya/page) back onto the element: those are x-tag accessor attributes,
                // and writing them re-triggers render(), which used to cascade and duplicate output.
                var page = this.page;
                var headless = isTrue(this.headless); // hide header (multiline) / copy button (inline)
                var verse_mode = (this.sura != null && this.aya != null);
                if(verse_mode){
                  sura_from = parseSuraRange(this.sura)[0];
                  sura_to = sura_from;
                  multiline = false;
                  [aya_from,aya_to] = parseAyaRange(this.aya);
                  if(this.page != null) print("Ignoring page parameter!");
                  page = madina_data.suras[sura_from].ayas[aya_from].p;
                } else if(this.page != null){
                  sura_from = 0; sura_to = 0; aya_from=0; aya_to=0;
                  while(madina_data.suras[sura_from].ayas.slice(-1)[0].p < page) sura_from = sura_from + 1;
                  sura_to = sura_from;
                  while(sura_to < 114 && madina_data.suras[sura_to].ayas[0].p <= page) sura_to = sura_to + 1;
                  sura_to = sura_to -1;
                  while(madina_data.suras[sura_from].ayas[aya_from].p < page) aya_from = aya_from + 1;
                  aya_to = madina_data.suras[sura_to].ayas.length-1;
                  while (madina_data.suras[sura_to].ayas[aya_to].p > page) aya_to = aya_to - 1;
                  multiline = true;
                } else{
                  console.error(`${name}> Bad arguments: Not rendering!`);
                  return 1;
                }
                if(this.words != null){
                  if(!verse_mode){
                    print("Ignoring words parameter with page!");
                  } else {
                    words_range = parseWordsRange(this.words);
                    if(words_range == null){
                      print(`Bad words parameter: ${this.words}`);
                    } else {
                      // words= has its own renderer that spans pages and suras from the start aya.
                      renderWordsSpan(tag, sura_from, aya_from, words_range, headless);
                      return;
                    }
                  }
                }
                tag.innerHTML = ""; //Remove all pre-existing elements
                tag.removeAttribute('style'); // and styles.
                line_from = madina_data.suras[sura_from].ayas[aya_from].r[0].l;
                line_to = madina_data.suras[sura_to].ayas[aya_to].r.slice(-1)[0].l;
                if(line_from!=line_to){
                  multiline = true;
                  tag.style = "display:block;";
                }
                if(multiline){
                  tag.style.setProperty('font-family', madina_data.font_family, '');
                  tag.style.setProperty('font-size', madina_data.font_size+"px", '');
                  if(madina_data.font_family === "me_quran"){
                    tag.style.setProperty('line-height', madina_data.font_size*2+"px", '');
                  }
                }
                /**Add Header with Copy button */
                var tag_header = "";
                if(multiline && !headless){
                  tag_header = document.createElement("quran-madina-html-header");
                  tag_header.innerHTML = madina_data.suras[sura_from].name;
                  var copy = getCopyIcon();
                  copy.addEventListener("click", copyToClipboard);
                  var translation = getTranslateIcon();
                  translation.addEventListener("click", openTranslate);
                  tag_header.appendChild(copy);
                  tag_header.appendChild(translation);
                  tag.appendChild(tag_header);
                }
                /** Loop on Ayas, lines, parts */
                var aya_current = aya_from;
                var sura_current = sura_from;
                for(let l = line_from; l <= line_to; l++) {
                  const ll = l; //Const for inner loops to refer
                  line = document.createElement("quran-madina-html-line");
                  tag.appendChild(line);
                  if(!multiline){
                    line.style.setProperty('font-family', madina_data.font_family, '');
                    line.style.setProperty('font-size', madina_data.font_size+"px", '');
                  }
                  if(multiline){
                    tag.style.width = (madina_data.line_width+10)+"px";
                    let isRightPage = madina_data.suras[sura_current].ayas[aya_current].p%2==1?"":"-";
                    tag.style.setProperty('box-shadow', 'inset '+isRightPage+'8px 0 7px -7px #333','');
                    line.style.setProperty('display','block','');
                  }
                  if(multiline && verse_mode && l === line_from){
                    appendSpacers(line, lineContext(sura_from, page, line_from, aya_from, -1));
                  }
                  let look_ahead = (sura_from == sura_to)? aya_to: madina_data.suras[sura_current].ayas.length-1;
                  for(let a = aya_current; a <= Math.min(aya_current+5, look_ahead) ; a++) {
                    if(madina_data.suras[sura_current].ayas[a].p == page){
                      line_match = madina_data.suras[sura_current].ayas[a].r.filter(rr => rr.l == ll);
                      if (line_match.length){
                        if(multiline){
                          if(line.innerHTML.trim() == ""){ // First part in the line
                            var offset = line_match[0].o;
                            line.style.setProperty('padding-right', offset+"px", '');
                            if(offset > 0) line.style.setProperty('transform-origin', "left");
                          }
                          if(line_match[0].s>=0){
                            line.style.setProperty("transform",`scaleX(${line_match[0].s})`,"");                        
                          } else {
                            line.style.setProperty("text-align","center","");  
                          }
                        }
                        let aya_part = document.createElement("div");
                        let classes = getAyaClass(sura_current+1, a-1);
                        DOMTokenList.prototype.add.apply(aya_part.classList, classes);
                        aya_part.textContent = line_match[0].t;
                        aya_part.style.cssText = 'display:inline';
                        line.appendChild(aya_part);
                        hoverByType(classes.slice(-1)[0]);
                        aya_current = a;
                        if(aya_current >= look_ahead &&
                          sura_current < 113 &&
                          madina_data.suras[sura_current+1].ayas[0].p == page &&
                          madina_data.suras[sura_current+1].ayas[0].r[0].l == ll+1) {
                          //Jump to next Sura
                          sura_current = sura_current + 1;
                          aya_current = 0;
                        }
                      }
                    }
                  }
                  if(multiline && verse_mode && l === line_to){
                    appendSpacers(line, lineContext(sura_to, page, line_to, aya_to, 1));
                  }
                }
                if(!multiline && !headless){
                  tag_header = document.createElement("quran-madina-html-copy");
                  let copy = getCopyIcon();
                  copy.addEventListener("click", copyToClipboard);
                  tag_header.appendChild(copy);
                  tag.appendChild(tag_header);
                }
              }
            }
          });
        
        },
         function(xhr) { console.error(xhr); }
  );

})();
