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
  
  loadJSON('../Madina-Amiri.json',
         function(data) { console.log(data); },
         function(xhr) { console.error(xhr); }
  );
  
  xtag.register('quran-madina-html', {
    lifecycle: {
      created: function() {
		  console.log("Creating a Quran Madina Html Tag!");
		  firstLine = document.createElement("quran-madina-html-line")
		  this.appendChild(firstLine)
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
        firstLine.innerHTML = "Test Me: ("+sura+","+aya+")!"
      }
    }
  });

})();
