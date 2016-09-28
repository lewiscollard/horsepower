(function () {
  "use strict";

  // Prehistory. Someone might need to support these guys, and there's no
  // need to cause an exception.
  if (!window.addEventListener) {
    return;
  }

  var parallaxElementsA = [];
  var parallaxElements = [];

  /*
  Check for unprefixed 'transform', then check for 'webkitTransform'
  (-webkit-transform). This is to add support for older Webkits (Safari and
  Android browser) that are still widely used.
  Note to developer reading this in 2017): kill this.
  */
  var nullElement = document.createElement('div')
  var transformProperty;

  if ('transform' in nullElement.style) {
    transformProperty = 'transform'
  } else if ('webkitTransform' in nullElement.style) {
    transformProperty = 'webkitTransform'
  } else {
    // Don't bother with -moz-transform (old versions that do not support
    // the unprefixed transform are basically non-existent), -ms-transform
    // (for IE9), etc.
    return
  }

  // Store these, as they don't change with every scroll.
  var windowHeight;
  var windowMiddle;
  var windowWidth;

  function recalculateElementOffsets () {
    /*
    Calculate properties of all of our elements and store them.
    This is to prevent doing it on every scroll; we only need to do it
    on load and on resize. In particular, getBoundingClientRect is
    surprisingly expensive.
    */

    windowWidth = window.innerWidth
    windowHeight = window.innerHeight
    windowMiddle = windowHeight / 2

    parallaxElements = []

    var currentPos = window.scrollY || window.pageYOffset || document.documentElement.scrollTop;

    var element;
    var elemobj;
    var i;
    var responsiveBreak;
    for (i = 0; i < parallaxElementsA.length; i++) {
      element = parallaxElementsA[i];

      // This will be stored in our list of elements over which we will loop
      // in the scroll hook.
      elemobj = {
        element: element,
        top: currentPos + element.getBoundingClientRect().top,
        // Bottom of the element, measured from the top of the document.
        bottom: currentPos + element.getBoundingClientRect().top + element.offsetHeight,
        // Middle of the element, measured from the top of the document.
        middle: currentPos + element.getBoundingClientRect().top + (element.offsetHeight / 2),
        // Completely arbitrary 'parallax by' factor.
        moveXBy: 0,
        moveYBy: 0,
        // These will be set if present.
        maxWidth: null,
        minWidth: null,
        // Restrict to positive or negative. Set to 0 for none, 1 for negative
        // and 2 for positive.
        restrict: 0,
        unit: element.dataset.parallaxUnit || 'vh',
      };

      // Up/down parallaxing.
      if (element.dataset.parallaxYBy) {
        elemobj.moveYBy = parseFloat(element.dataset.parallaxYBy, 10);
      }

      // Left/right parallaxing.
      if (element.dataset.parallaxXBy) {
        elemobj.moveXBy = parseFloat(element.dataset.parallaxXBy, 10);
      }

      // Is it restricted to positive or negative values?
      if (element.dataset.parallaxRestrictTo) {
        if (element.dataset.parallaxRestrictTo === "negative") {
          elemobj.restrict = 1;
        } else if (element.dataset.parallaxRestrictTo === "positive") {
          elemobj.restrict = 2;
        }
      }

      responsiveBreak = false

      if (element.dataset.parallaxMaxWidth) {
        var maxWidth = parseFloat(element.dataset.parallaxMaxWidth, 10)
        if (windowWidth > maxWidth) {
          responsiveBreak = true
        }
      }

      if (element.dataset.parallaxMinWidth) {
        var minWidth = parseInt(element.dataset.parallaxMinWidth, 10)
        if (windowWidth < minWidth) {
          responsiveBreak = true
        }
      }

      if (responsiveBreak) {
        element.style.transform = 'translate3d(0, 0, 0)'
        continue
      }
      parallaxElements.push(elemobj)
    }
  }

  // Compute immediately
  recalculateElementOffsets()
  window.addEventListener('resize', recalculateElementOffsets)
  window.addEventListener("DOMContentLoaded", recalculateElementOffsets)

  function scrollHook () {
    var currentPos = window.scrollY || window.pageYOffset || document.documentElement.scrollTop

    var scrollBottom = windowHeight + currentPos

    var item;
    var middleOffset
    var xOffset;
    var yOffset;
    var i;

    for (i = 0; i < parallaxElements.length; i++) {
      item = parallaxElements[i];

      // Do nothing if it is not on screen.
      if (scrollBottom < item.top || currentPos > item.bottom) {
        continue;
      }

      // How far is the middle of the element from the middle of the
      // screen?
      middleOffset = item.middle - currentPos - windowMiddle;

      yOffset = 0;
      if (item.moveYBy) {
        yOffset = (middleOffset / 100.0) * item.moveYBy
      }

      xOffset = 0
      if (item.moveXBy) {
        xOffset = (middleOffset / 100.0) * item.moveXBy
      }

      // Does the element's 'restrict-to' parameter preclude this move?
      if (item.restrict > 0) {
        if (item.restrict === 1 && (xOffset > 0 || yOffset > 0)) {
          continue;
        } else if (item.restrict === 2 && (xOffset < 0 || yOffset < 0)) {
          continue;
        }
      }

      if (item.unit === 'px') {
        xOffset = parseInt(xOffset, 10)
        yOffset = parseInt(yOffset, 10)
      }
      item.element.style[transformProperty] = "translate3d(" + xOffset.toString() + item.unit + ", " + yOffset.toString() + item.unit + ", 0)";
    }
  }

  function initialise() {
    parallaxElementsA = [].slice.call(document.getElementsByClassName('fast-parallax'));
    recalculateElementOffsets();
    scrollHook();
    window.addEventListener('scroll', scrollHook);
  }

  window.addEventListener('DOMContentLoaded', initialise);
})();
