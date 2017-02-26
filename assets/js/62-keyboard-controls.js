function handleKeyPress (e) {
  // Previous
  if (e.keyCode === 37 && document.querySelector('.photo-prevnext.prev')) {
    document.querySelector('.photo-prevnext.prev').click()
  } else if (e.keyCode === 39 && document.querySelector('.photo-prevnext.next')) {
    document.querySelector('.photo-prevnext.next').click()
  }
}

window.addEventListener('DOMContentLoaded', function () {
    if (document.querySelector('.photo-prevnext')) {
      document.addEventListener('keydown', handleKeyPress)
    }
});
