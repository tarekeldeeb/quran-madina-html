module.exports = function(grunt) {

  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    concat: {
      options: {
        separator: ';'
      },
      dist: {
        src: ['src/<%= pkg.name %>.js',
         'bower_components/x-tag-core/dist/x-tag-core.min.js'],
        dest: 'dist/<%= pkg.name %>.js'
      }
    },
    uglify: {
      options: {
        banner: '/*! <%= pkg.name %> <%= grunt.template.today("dd-mm-yyyy") %> */\n'
      },
      dist: {
        files: {
          'dist/<%= pkg.name %>.min.js': ['<%= concat.dist.dest %>']
        }
      }
    },
    cssmin: {
      target: {
        files: [{
          expand: true,
          cwd: 'src',
          src: ['*.css', '!*.min.css'],
          dest: 'dist',
          ext: '.min.css'
        }]
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

  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-jshint');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-clean');
  grunt.loadNpmTasks('grunt-contrib-cssmin');
  grunt.loadNpmTasks('grunt-json-minify');

  grunt.registerTask('test', ['jshint']);
  grunt.registerTask('default', ['jshint', 'clean', 'concat', 'uglify', 'cssmin', 'json-minify']);

};