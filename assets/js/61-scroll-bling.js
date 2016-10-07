window.addEventListener('DOMContentLoaded', function () {
    inView('.gallery-section-item').on('enter', function (element) {
        element.classList.add('in-view');
    });
});
