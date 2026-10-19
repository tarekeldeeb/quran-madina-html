module.exports = function(grunt) {

  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    // The npm package ships readable (unminified) code. The output keeps the historical
    // `.min.js` / `.min.css` names because they are a published URL contract (unpkg links,
    // the React / React Native / Flutter / WordPress wrappers, self-hosting docs).
    // Each file opens with the license header (version/author from package.json).
    concat: {
      options: {
        stripBanners: false,
        banner: '/*!\n' +
                ' * <%= pkg.name %> v<%= pkg.version %>\n' +
                ' * <%= pkg.description %>\n' +
                ' * <%= pkg.homepage %>\n' +
                ' *\n' +
                ' * Copyright (c) <%= pkg.author %>\n' +
                ' * Licensed under the "Waqf" General Public License 2.0, 3 Muharram 1435\n' +
                ' * https://github.com/ojuba-org/waqf/tree/master/2.0\n' +
                ' * See LICENSE.md in the package for details.\n' +
                ' */\n'
      },
      js: {
        src: ['src/<%= pkg.name %>.js'],
        dest: 'dist/<%= pkg.name %>.min.js'
      },
      css: {
        src: ['src/<%= pkg.name %>.css'],
        dest: 'dist/<%= pkg.name %>.min.css'
      }
    },
    jshint: {
      files: ['Gruntfile.js', 'src/**/*.js', 'test/**/*.js'],
      options: {
        // options here to override JSHint defaults
        globals: {
          jQuery: true,
          console: true,
          module: true,
          document: true
        },
        esnext: true
      }
    },
    'json-minify': {
      build: {
        files: 'assets/db/*.json'
      }
    },
    clean : {
      yourTarget : {
          src : [ "dist"
          ]
      }
    },
    watch: {
      files: ['<%= jshint.files %>'],
      tasks: ['jshint']
    }
  });

  grunt.loadNpmTasks('grunt-contrib-jshint');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-clean');
  grunt.loadNpmTasks('grunt-json-minify');

  grunt.registerTask('test', ['jshint']);
  grunt.registerTask('default', ['jshint', 'clean', 'concat', 'json-minify']);

};