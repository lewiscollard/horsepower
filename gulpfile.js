var gulp = require('gulp'),
  plumber = require('gulp-plumber'),
  rename = require('gulp-rename');
var autoprefixer = require('gulp-autoprefixer');
var concat = require('gulp-concat');
var uglify = require('gulp-uglify');
var cleancss = require('gulp-clean-css');
var sass = require('gulp-sass');

gulp.task('bs-reload', function () {
  browserSync.reload();
});

gulp.task('images', function() {
  gulp.src('assets/images/**/*')
    .pipe(gulp.dest('html/resource/images/'));
});

gulp.task('styles', function(){
  gulp.src(['assets/scss/**/*.scss'])
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
    .pipe(gulp.dest('html/resource/css/'))
});

gulp.task('scripts', function () {
  return gulp.src('assets/js/**/*.js')
    .pipe(plumber({
      errorHandler: function (error) {
        console.log(error.message);
        this.emit('end');
    }}))
    .pipe(concat('main.js'))
    .pipe(uglify())
    .pipe(gulp.dest('html/resource/js'))
});

gulp.task('default', ['styles', 'scripts', 'images'], function(){
  gulp.watch("assets/scss/**/*.scss", ['styles']);
  gulp.watch("assets/images/**/*", ['images']);
  gulp.watch("assets/js/**/*.js", ['scripts']);
});
