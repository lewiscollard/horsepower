document.createElement("article");
document.createElement("section");
document.createElement("nav");

jQuery.fn.slider = function() {
 var slider = $(this);
 var loadblock = $("<div class='slider-loading'></div>")
 loadblock.appendTo(slider);
 slider.changeSlide = function(id) {
  // Current slide.
  var current = slider.children(".slide:visible").first();
  var target = $("#" + id);
  var current_id = current.attr("id");
  var current_nav = slider.children(".nav").children("li[data-for='" + current_id + "']");
  current_nav.removeClass("active");
  current.css("z-index", "2");
  target.css("z-index", "1");
  target.fadeTo(0, 1);
  current.fadeOut(800, function() {
   current.css("z-index", "1");
   target.css("z-index", "2");
   var target_nav = slider.children(".nav").children("li[data-for='" + id + "']");
   target_nav.addClass("active");
  });
  target.fadeIn();
 }
 
 slider.nextSlide = function() {
  var current = slider.children(".slide:visible").first();
  var next = current.next(".slide");
  if (!next.attr("id")) {
   next = slider.children(".slide").first();
  }
  slider.changeSlide(next.attr("id"));
 }

 slider.prevSlide = function() {
  var current = slider.children(".slide:visible").first();
  var next = current.prev(".slide");
  if (!next.attr("id")) {
   next = slider.children(".slide").last();
  }
  slider.changeSlide(next.attr("id"));
 }
 
 $(window).load(function() {
  // Remove "loading" 
  loadblock.fadeOut(400, function() {
   loadblock.remove();
  });
  /* Create nav */
  var nav = $("<ul class='nav'></ul>");
  var timer = window.setInterval(function() {
   slider.nextSlide();
  }, 8000);
  slider.children(".slide").each(function() {
   var id = $(this).attr("id");
   var li = $("<li data-for='" + id + "'></li>");
   li.appendTo(nav);
   li.click(function() {
    window.clearInterval(timer);
    slider.changeSlide(id);
   });
  });
  nav.appendTo(slider);
  // Add previous/next
  var next = $("<span class='prevnext next'>&gt;</span>");
  next.css("display: none");
  next.click(function() {
   window.clearInterval(timer);
   slider.nextSlide();
  });
  next.appendTo(slider);
  next.fadeIn(200);

  var prev = $("<span class='prevnext prev'>&lt;</span>");
  prev.css("display: none");
  prev.click(function() {
   window.clearInterval(timer);
   slider.prevSlide();
  });
  prev.appendTo(slider);
  prev.fadeIn(200);
  
  nav.children("li").first().addClass("active");
  
  
 });
 
}