export default function () {
  const items = document.querySelectorAll('.scroll-bling')

  const callback = (entries, observer) => {
    Array.from(entries).forEach((entry, index) => {
      if (entry.isIntersecting && !entry.target.dataset.activating) {
        entry.target.classList.add('scroll-bling--in-view')
        observer.unobserve(entry.target)
      }
    })
  }

  const observer = new IntersectionObserver(callback, {
    threshold: 0,
  })
  Array.from(items).forEach(item => observer.observe(item))
}
