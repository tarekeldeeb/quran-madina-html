(function(){
  var name = "quran-madina-html";
  var cdn = "../";
  //var cdn = `https://www.unpkg.com/${name}/`;
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
  function getAyaClass(sura, aya){
    const zeroPad = (num, places) => String(num).padStart(places, '0');
    return [`${name}-part`, `${name}-${zeroPad(sura,3)}-${zeroPad(aya,3)}`];
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
    '1.9C37.6 8.8 12.6 33.4 3.4 67.5c-1.8 6.6-1.9 11.9-1.9 98v91l2.3 8c5.1 17.8 17 36.4 29.9 46.7 10.8 8.6 25.4 15.4 38.1 17.8 '+
    '3.1.6 15.2 1 26.8 1 17.7 0 21.3.2 21.7 1.4.4.9.6 17.1.7 36.1 0 32.4.2 34.9 2 38.5 6.4 12.5 21.4 17.4 33.3 10.8 2.3-1.3 7.5-6.4 '+
    '12.1-11.9l63-74.1c.6-.4 16.3-.8 34.9-.8H300l-.2-18.3-.3-18.2-42.8.1-43.1.5c-.2.2-12.7 15.1-27.9 33.1-15.1 18-27.8 32.4-28.1 '+
    '32.1-.3-.4-.6-15.3-.6-33.2v-32.6l-38.8-.1c-42.1-.2-43.9-.4-54.3-6-6.5-3.6-16.9-14.6-20.2-21.5-5.8-11.9-5.7-10-5.7-100.7 '+
    '0-92-.2-89.4 6.3-101.7 3.9-7.3 13.5-17.1 20.3-20.7C76 36.7 66.1 37 244.5 37L412 38.1c18 4.1 33.5 20.5 37.5 39.6 2.2 10.2 2.1 '+
    '164.6 0 174.8-3.9 18.3-16.4 32.7-33.5 38.5-3.2 1.1-7.8 2-10 2-3.1 0-4 .4-4 1.7 0 1-.2 8.8-.3 17.3-.2 8.5-.2 16.2 0 17 .9 3.3 '+
    '21.7-.5 34.1-6 13.7-6.3 27.5-17.9 36.2-30.5 5-7.2 10.8-20.4 13.2-30.1l2.3-8.9V165 '+
    '76.5l-2.3-9c-8.1-31.4-30.5-54.9-61.7-64.8l-7-2.2-169-.2C87.7.1 78 .2 70 1.9zm614.341 308.289q19.5-.5 28.25 24.5 2.5 7.25-3.75 '+
    '19.75-5.75 11.75-9.75 16-19.5 21.5-67 25.25-27.75 2.25-50.25-2.25-5.25 38.25-16.5 50-26 26.75-66 29.5-27.75 '+
    '2-42.5-11-20.25-17.75-16.5-48.5 3-23.75 14.25-42.5 2.75-4.5 4.75-7.5 2-3 3-4.25 2.25-2.75 4.75-1.25 2.75 1.5 0 6.25-12.75 '+
    '24.5-10 45 4 30.5 44.5 30.5 30.25 0 53.25-15.5 12.5-8.25 14.75-14.25-2.25-20.75-13.75-35.75-3.5-4.25-1.75-8l9.5-23.5q3-7.5 '+
    '8.25 1.25l8.75 14.75q7.75 4.25 28.25 5 16.75-19.25 39.25-36.25 22.5-16.75 36.25-17.25zm11.5 40.5q-12.5-9.5-31.75-5.75-19 '+
    '3.75-41.25 19.5 50.75.5 73-13.75zm-71.5-89.75q1.5-2 4.25-1.25 5 1.75 9.5 4.5 4.75 2.75 8.75 6.25 2 2 .75 4.5l-12 19q-1.75 '+
    '2.5-4.5.5-2.5-2-18-11.25-2.75-1.75-1-4.25zM215.9 69.7c-4.7.4-4.7.4-6.7 6.1-1.2 3.1-9.3 25.9-18 50.7l-36.6 102.7-3.5 '+
    '9.8H169h17.8l5.7-17 5.7-17h31.7 31.8l5.6 17.2 5.6 17.3 17.9-.3 '+
    '18-.3-6-17.2-15-43.2-13.3-38.5-14.1-41-9.9-28.7c-.3-.6-30.2-1.1-34.6-.6zm35.7 106c-.2.2-10 .2-21.9.1l-21.5-.3L218 '+
    '146l11-32.5c1.2-2.9 1.8-1.4 12.1 29.4l10.5 32.8zm498.978 357.741c32.4-6.9 57.4-31.5 66.6-65.6 1.8-6.6 1.9-11.9 '+
    '1.9-98v-91l-2.3-8c-5.1-17.8-17-36.4-29.9-46.7-10.8-8.6-25.4-15.4-38.1-17.8-3.1-.6-15.2-1-26.8-1-17.7 '+
    '0-21.3-.2-21.7-1.4-.4-.9-.6-17.1-.7-36.1 0-32.4-.2-34.9-2-38.5-6.4-12.5-21.4-17.4-33.3-10.8-2.3 1.3-7.5 6.4-12.1 11.9l-63 '+
    '74.1c-.6.4-16.3.8-34.9.8h-33.7l.2 18.3.3 18.2 42.8-.1 43.1-.5c.2-.2 12.7-15.1 27.9-33.1 15.1-18 27.8-32.4 28.1-32.1.3.4.6 '+
    '15.3.6 33.2v32.6l38.8.1c42.1.2 43.9.4 54.3 6 6.5 3.6 16.9 14.6 20.2 21.5 5.8 11.9 5.7 10 5.7 100.7 0 92 .2 89.4-6.3 101.7-3.9 '+
    '7.3-13.5 17.1-20.3 20.7-11.4 6.1-1.5 5.8-179.9 5.8-108.2 0-164.5-.4-167.5-1.1-18-4.1-33.5-20.5-37.5-39.6-2.2-10.2-2.1-164.6 '+
    '0-174.8 3.9-18.3 16.4-32.7 33.5-38.5 3.2-1.1 7.8-2 10-2 3.1 0 4-.4 4-1.7 0-1 .2-8.8.3-17.3.2-8.5.2-16.2 '+
    '0-17-.9-3.3-21.7.5-34.1 6-13.7 6.3-27.5 17.9-36.2 30.5-5 7.2-10.8 20.4-13.2 30.1l-2.3 8.9v88.5 88.5l2.3 9c8.1 31.4 30.5 54.9 '+
    '61.7 64.8l7 2.2 169 .2 177.5-1.6z"/></svg>';
    var div = document.createElement('div');
    div.innerHTML = htmlString.trim();
    return div.firstChild;
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
    if(this.parentElement.parentElement.getAttribute("page") != null){
      let page_index = this.parentElement.parentElement.getAttribute("page");
      URL = `https://quran.com/page/${page_index}`;
    } else {
      let sura_index = this.parentElement.parentElement.getAttribute("sura");
      let aya_index = this.parentElement.parentElement.getAttribute("aya");
      URL = `https://quran.com/${sura_index}/${aya_index}`;
    }
    window.open(URL, '_blank');
  }
  var madina_data = {"content":"Loading .."};
  var this_script = document.currentScript || document.querySelector(`script[src*="${name}"]`);
  var doc_name    = this_script.getAttribute('data-name') || "Madina05";
  var doc_font    = (this_script.getAttribute('data-font') || "Hafs").replaceAll(" ","%");
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
              attributeChanged: function() {}
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
              }              
            }, 
            methods: {
               render: function(tag){
                var sura_from;
                var sura_to;
                var multiline;
                var aya_from;
                var aya_to;
                var line_from;
                var line_to;
                if(this.sura != null && this.aya != null ){
                  sura_from = parseSuraRange(this.sura)[0]; 
                  this.sura = sura_from.toString(); // Only a single Sura
                  sura_to = sura_from;
                  multiline = false;
                  [aya_from,aya_to] = parseAyaRange(this.aya);
                  if(this.page != null) print("Ignoring page parameter!");
                } else if(this.page != null){
                  sura_from = 0; sura_to = 0; aya_from=1; aya_to=0;
                  while(madina_data.suras[sura_from].ayas.slice(-1)[0].p < this.page) sura_from = sura_from + 1;
                  sura_to = sura_from;
                  while(madina_data.suras[sura_to].ayas[0].p <= this.page) sura_to = sura_to + 1;
                  sura_to = sura_to -1;
                  this.sura =(sura_from == sura_to)? `${sura_from+1}`:`${sura_from+1}-${sura_to+1}`;
                  while(madina_data.suras[sura_from].ayas[aya_from].p < this.page) aya_from = aya_from + 1;
                  aya_to = madina_data.suras[sura_to].ayas.length-1;
                  while (madina_data.suras[sura_to].ayas[aya_to].p > this.page) aya_to = aya_to - 1;
                  this.aya = `${aya_from-1}-${aya_to-1}`;
                  multiline = true;
                } else{
                  console.error(`${name}> Bad arguments: Not rendering!`);
                  return 1;
                }
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
                if(multiline){
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
                    let isRightPage = madina_data.suras[sura_current].ayas[aya_from].p%2==1?"":"-";
                    tag.style.setProperty('box-shadow', 'inset '+isRightPage+'8px 0 7px -7px #333','');
                    line.style.setProperty('display','block','');
                  } 
                  let look_ahead = (sura_from == sura_to)? aya_to: madina_data.suras[sura_current].ayas.length-1;
                  for(let a = aya_current; a <= Math.min(aya_current+5, look_ahead) ; a++) {
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
                      if(aya_current >= look_ahead && madina_data.suras[sura_current+1].ayas[0].r[0].l == ll+1) { 
                        //Jump to next Sura
                        sura_current = sura_current + 1;
                        aya_current = 0;
                      }
                    }
                  }
                }
                if(!multiline){
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
