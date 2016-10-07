function makeCarousel(selector) {
    var carousel = document.querySelector(selector);
    if (!carousel) {
        return;
    }
    carousel.classList.add('carousel-loading');
    var loryCarousel = lory(carousel, {
        'infinite': 1,
        'classNameFrame': 'carousel-frame',
        'classNamePrevCtrl': 'carousel-button-previous',
        'classNameNextCtrl': 'carousel-button-next',
        'classNameSlideContainer': 'carousel-slides',
        'enableMouseEvents': 'true'
    });

    carousel.classList.remove('carousel-loading');

    // Autoplay
    var timer = window.setInterval(function () {
        loryCarousel.next();
    }, 5000);

    function cancelTimer() {
        window.clearInterval(timer)
    }

    carousel.querySelector('.carousel-button-next').addEventListener('click', cancelTimer);
    carousel.querySelector('.carousel-button-previous').addEventListener('click', cancelTimer);
    carousel.addEventListener('on.lory.touchstart', cancelTimer);
}

window.addEventListener('load', function() {
    makeCarousel('.carousel-outer')
});

