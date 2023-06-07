(function(){
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
  loadJSON('https://raw.githubusercontent.com/tarekeldeeb/quran-madina-html-no-images/main/Madina-Amiri.json',
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
            accessors: {}, 
            methods: {
               render: function(tag){
                var sura = tag.getAttribute("sura");
                sura = parseRange(sura)[0]; // Only a single Sura
                var aya  = tag.getAttribute("aya");
                var multiline = false;
                [aya_from,aya_to] = parseRange(aya);
                var line_from = madina_data.suras[sura].ayas[aya_from].r[0].l;
                var line_to = madina_data.suras[sura].ayas[aya_to].r.slice(-1)[0].l;
                
                if(line_from!=line_to){
                  multiline = true;
                  tag.style = "display:block;"
                }
                var aya_current = aya_from;
                for(let l = line_from; l <= line_to; l++) {
                  line = document.createElement("quran-madina-html-line");
                  tag.appendChild(line);
                  line.style.setProperty('font-family', madina_data.font_family, '');
                  if(multiline) line.style.setProperty('display','block','');
                  for(let a = aya_current; a < aya_current+5 && a <=aya_to ; a++) { //Look ahead
                    line_match = madina_data.suras[sura].ayas[a].r.filter(r => r.l == l)
                    if (line_match.length){
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
