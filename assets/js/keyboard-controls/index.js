export default function () {
  function handleKeyPress (e) {
    // Previous
    if (e.keyCode === 37 && document.querySelector('.photo-prevnext.prev')) {
      document.querySelector('.photo-prevnext.prev').click()
    } else if (e.keyCode === 39 && document.querySelector('.photo-prevnext.next')) {
      document.querySelector('.photo-prevnext.next').click()
    }
  }

  if (document.querySelector('.photo-prevnext')) {
    window.addEventListener('keydown', handleKeyPress)
  }
}
