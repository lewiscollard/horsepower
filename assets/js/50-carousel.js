function makeCarousel(selector) {
    var carousel = document.querySelector(selector);
    if (!carousel) {
        return;
    }
    carousel.classList.add('carousel-loading');
    lory(carousel, {
        'infinite': 1,
        'classNameFrame': 'carousel-frame',
        'classNamePrevCtrl': 'carousel-button-previous',
        'classNameNextCtrl': 'carousel-button-next',
        'classNameSlideContainer': 'carousel-slides',
        'enableMouseEvents': 'true'
    });
    carousel.addEventListener('after.lory.init', function () {
        console.log('lory is loaded');
    });
    window.addEventListener("load", function () {
        carousel.classList.remove('carousel-loading');
    })
}
