/**
 * Lets keyboard users scroll article tables that are wider than their box.
 * A table whose scroll box overflows is given a tab stop, so it can be
 * focused and scrolled with the arrow keys; the stop is removed again when
 * the table fits.
 */
(function () {
    var MARK = 'data-scroll-region';

    function scroller(table) {
        for (var element = table; element && element !== document.body; element = element.parentElement) {
            var overflow = getComputedStyle(element).overflowX;
            if (overflow === 'auto' || overflow === 'scroll') {
                return element;
            }
        }
        return null;
    }

    function update() {
        var tables = document.querySelectorAll('table');
        for (var i = 0; i < tables.length; i++) {
            var table = tables[i];
            var box = scroller(table);
            var overflows = box && box.scrollWidth > box.clientWidth + 1;
            if (overflows && !table.hasAttribute('tabindex')) {
                table.setAttribute('tabindex', '0');
                table.setAttribute(MARK, '');
            } else if (!overflows && table.hasAttribute(MARK)) {
                table.removeAttribute('tabindex');
                table.removeAttribute(MARK);
            }
        }
    }

    var timer = null;
    function scheduleUpdate() {
        clearTimeout(timer);
        timer = setTimeout(update, 150);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', update);
    } else {
        update();
    }
    window.addEventListener('load', update);
    window.addEventListener('resize', scheduleUpdate);
})();
