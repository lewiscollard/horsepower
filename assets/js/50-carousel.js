function makeCarousel(selector) {
    var carousel = document.querySelector(selector);
    if (!carousel) {
        return;
    }
    carousel.classList.add('carousel-loading');
    lory(carousel, {
        'infinite': 1,
        'classNameFrame': 'carousel-frame',
        'classNamePrevCtrl': 'carousel-button-next',
        'classNameNextCtrl': 'carousel-button-previous',
        'classNameSlideContainer': 'carousel-slides'
    });

    window.addEventListener("load", function () {
        carousel.classList.remove('carousel-loading');
    })
}
