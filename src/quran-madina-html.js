(function(){
  var name = "quran-madina-html";
  var cdn = 'https://raw.githubusercontent.com/tarekeldeeb/quran-madina-html-no-images/main/DBs/';
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
  function parseRange(str){
    if (str.split('-').length == 2) return str.split('-').map(elem => elem -1);
    return Array(2).fill(str.split('-')[0]-1);
  }
  var madina_data = {"content":"Loading .."};
  var this_script = document.querySelector('script[data-name]');
  var doc_name    = this_script.getAttribute('data-name') || "Madina";
  var doc_font    = this_script.getAttribute('data-font') || "Amiri";
  var doc_font_sz = this_script.getAttribute('data-font-size') || 16;
  console.log("Quran> "+doc_name+" with font:"+doc_font+" size:"+doc_font_sz);
  const name_css = "../src/"+name+".css";
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
  loadJSON(cdn+doc_name+'-'+doc_font+'-'+doc_font_sz+'px.json',
        function(data) { 
          madina_data = data; 
          const myFont = new FontFace(madina_data.font_family, 'url('+encodeURI(madina_data.font_url)+')');
          myFont.load().then( () => {document.fonts.add(myFont);});
          xtag.register('quran-madina-html', {
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
                var sura = parseRange(this.sura)[0]; // Only a single Sura
                var multiline = false;
                [aya_from,aya_to] = parseRange(this.aya);
                var line_from = madina_data.suras[sura].ayas[aya_from].r[0].l;
                var line_to = madina_data.suras[sura].ayas[aya_to].r.slice(-1)[0].l;
                
                if(line_from!=line_to){
                  multiline = true;
                  tag.style = "display:block;";
                }
                if(multiline){
                  tag.style.setProperty('font-family', madina_data.font_family, '');
                  tag.style.setProperty('font-size', madina_data.font_size+"px", '');                  
                }
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
                      if(line.innerHTML.trim() == ""){ // First part in the line
                        var offset = line_match[0].o;
                        line.style.setProperty('padding-right', offset+"px", '');
                        if(offset > 0) line.style.setProperty('transform-origin', "left");
                      }
                      line.style.setProperty("transform","scaleX("+line_match[0].s+")","");
                      line.innerHTML += line_match[0].t;
                      aya_current = a;
                    }
                  }
                }
              }
            }
          });
        
        },
         function(xhr) { console.error(xhr); }
  );

})();
