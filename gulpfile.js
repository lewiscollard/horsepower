var gulp = require('gulp'),
  plumber = require('gulp-plumber'),
  rename = require('gulp-rename');
var concat = require('gulp-concat');
var uglify = require('gulp-uglify');
var cleancss = require('gulp-clean-css');
var sass = require('gulp-sass');
var browserSync = require('browser-sync');

var config = {
  sass: {
    src: 'assets/scss/**/*.scss'
  },
  js: {
    src: 'assets/js/**/*.js'
  },
  html: {
    src: 'templates/**/*.html'
  },
  images: {
    src: 'assets/images/**/*'
  }
};

gulp.task('serve', function () {
  browserSync.init({
    injectChanges: true,
    logFileChanges: true,
    logPrefix: 'text',
    notify: false,
    open: false,
    proxy: 'hp.local'
  });

  process.on('exit', function () {
    browserSync.exit();
  });

  /***********/
  /* Watches */
  /***********/
  // - Pass SASS to the Styles task
  gulp.watch(config.sass.src, ['styles']);

  // - HTML and Images don't need to be processed
  gulp.watch(config.html.src, browserSync.reload);
  gulp.watch(config.images.src, browserSync.reload);
  gulp.watch(config.js.src, ['scripts']);
});

gulp.task('images', function() {
  gulp.src(config.images.src)
    .pipe(gulp.dest('html/resource/images/'));
});

gulp.task('styles', function(){
  gulp.src([config.sass.src])
    .pipe(plumber({
      errorHandler: function (error) {
        console.log(error.message);
        this.emit('end');
      }
    }))
    .pipe(sass())
    .pipe(gulp.dest('html/resource/css/'))
    .pipe(rename({suffix: '.min'}))
    .pipe(cleancss())
    .pipe(browserSync.stream({match: '**/*.css'}))
    .pipe(gulp.dest('html/resource/css/'))
});

gulp.task('scripts', function () {
  return gulp.src(config.js.src)
    .pipe(plumber({
      errorHandler: function (error) {
        console.log(error.message);
        this.emit('end');
    }}))
    .pipe(concat('main.js'))
    .pipe(uglify())
    .pipe(gulp.dest('html/resource/js'))
});

gulp.task('default', ['styles', 'scripts', 'images', 'serve']);
