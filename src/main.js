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
    return str.split('-')[0]-1; //FIXME: BAD IMPLEMENTATION
    var _from = 0;
    if (str.split('-').length == 2) return str.split('-');
    _from = str.split('-')[0];
    return [_from, _from];
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
                firstLine = document.createElement("quran-madina-html-line");
                this.appendChild(firstLine);
                this.render(firstLine, this.getAttribute("sura"), this.getAttribute("aya"));
              },
              inserted: function() {},
              removed: function() {},
              attributeChanged: function() {}
            }, 
            events: {},
            accessors: {}, 
            methods: {
               render: function(firstLine, sura,aya){
                firstLine.innerHTML = madina_data.suras[parseRange(sura)].ayas[parseRange(aya)].r[0].t;
                firstLine.style = "font-family: "+madina_data.font_family;
              }
            }
          });
        
        },
         function(xhr) { console.error(xhr); }
  );

})();
