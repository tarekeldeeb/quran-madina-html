(function(){
  var name = "quran-madina-html";
  //var cdn = "../";
  var cdn = `https://www.unpkg.com/${name}/`;
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
                var sura;
                var multiline;
                var aya_from;
                var aya_to;
                var line_from;
                var line_to;
                if(this.sura != null && this.aya != null ){
                  sura = parseSuraRange(this.sura)[0]; // Only a single Sura
                  multiline = false;
                  [aya_from,aya_to] = parseAyaRange(this.aya);
                  if(this.page != null) print("Ignoring page parameter!");
                } else if(this.page != null){
                  /* Search: only works within a single sura */
                  sura = 0; aya_from=1; aya_to=0;
                  while(madina_data.suras[sura].ayas[0].p < this.page) sura = sura + 1;
                  sura = sura -1;
                  while(madina_data.suras[sura].ayas[aya_from].p < this.page) aya_from = aya_from + 1;
                  aya_to = aya_from;
                  while(madina_data.suras[sura].ayas[aya_to].p == this.page) aya_to = aya_to + 1;
                  aya_to = aya_to -1;
                  multiline = true;
                } else{
                  console.error(`${name}> Bad arguments: Not rendering!`);
                  return 1;
                }
                line_from = madina_data.suras[sura].ayas[aya_from].r[0].l;
                line_to = madina_data.suras[sura].ayas[aya_to].r.slice(-1)[0].l;
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
                  tag_header.innerHTML = madina_data.suras[sura].name;
                  var copy = getCopyIcon();
                  copy.setAttribute("data-copy-sura", sura); //FIXME
                  copy.setAttribute("data-copy-aya-from", aya_from); //FIXME
                  copy.setAttribute("data-copy-aya-to", aya_to); //FIXME
                  copy.addEventListener("click", copyToClipboard);
                  tag_header.appendChild(copy);
                  tag.appendChild(tag_header);
                }
                /** Loop on Ayas, lines, parts */
                var aya_current = aya_from;
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
                    let isRightPage = madina_data.suras[sura].ayas[aya_from].p%2==1?"":"-";
                    tag.style.setProperty('box-shadow', 'inset '+isRightPage+'8px 0 7px -7px #333','');
                    line.style.setProperty('display','block','');
                  } 
                  for(let a = aya_current; a < aya_current+5 && a <=aya_to ; a++) { //Look ahead
                    line_match = madina_data.suras[sura].ayas[a].r.filter(rr => rr.l == ll);
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
                      let classes = getAyaClass(sura+1, a-1);
                      DOMTokenList.prototype.add.apply(aya_part.classList, classes);
                      aya_part.textContent = line_match[0].t;
                      aya_part.style.cssText = 'display:inline';
                      line.appendChild(aya_part);
                      hoverByType(classes.slice(-1)[0]);
                      aya_current = a;
                    }
                  }
                }
                if(!multiline){
                  tag_header = document.createElement("quran-madina-html-copy");
                  let copy = getCopyIcon();
                  copy.setAttribute("data-copy-sura", sura); //FIXME
                  copy.setAttribute("data-copy-aya-from", aya_from); //FIXME
                  copy.setAttribute("data-copy-aya-to", aya_to); //FIXME
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
