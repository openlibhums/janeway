/**
 * Lets keyboard users scroll article tables that are wider than their box.
 * A table whose scroll box overflows is given a tab stop, so it can be
 * focused and scrolled with the arrow keys; the stop is removed again when
 * the table fits. Tables are checked whenever they or their box change size,
 * so tables in a modal opened later, or that grow when fonts load, are
 * included.
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

    function label(table) {
        var wrapper = table.closest('.table-expansion');
        var heading = wrapper && wrapper.querySelector('.table-label[id]');
        return heading ? heading.id : null;
    }

    function update(table) {
        var box = scroller(table);
        var overflows = box && box.scrollWidth > box.clientWidth + 1;
        if (overflows && !table.hasAttribute('tabindex')) {
            table.setAttribute('tabindex', '0');
            table.setAttribute(MARK, '');
            var labelId = label(table);
            if (labelId && !table.hasAttribute('aria-label') && !table.hasAttribute('aria-labelledby')) {
                table.setAttribute('aria-labelledby', labelId);
                table.setAttribute(MARK, 'labelled');
            }
        } else if (!overflows && table.hasAttribute(MARK) && document.activeElement !== table) {
            if (table.getAttribute(MARK) === 'labelled') {
                table.removeAttribute('aria-labelledby');
            }
            table.removeAttribute('tabindex');
            table.removeAttribute(MARK);
        }
    }

    function updateAll() {
        var tables = document.querySelectorAll('table');
        for (var i = 0; i < tables.length; i++) {
            update(tables[i]);
        }
    }

    var pending = false;
    function scheduleUpdate() {
        if (pending) {
            return;
        }
        pending = true;
        requestAnimationFrame(function () {
            pending = false;
            updateAll();
        });
    }

    function start() {
        updateAll();
        if (!('ResizeObserver' in window)) {
            return;
        }
        var observer = new ResizeObserver(scheduleUpdate);
        var tables = document.querySelectorAll('table');
        for (var i = 0; i < tables.length; i++) {
            observer.observe(tables[i]);
            if (tables[i].firstElementChild) {
                observer.observe(tables[i].firstElementChild);
            }
            var box = scroller(tables[i]);
            if (box && box !== tables[i]) {
                observer.observe(box);
            }
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', start);
    } else {
        start();
    }
    window.addEventListener('load', scheduleUpdate);
    window.addEventListener('resize', scheduleUpdate);
})();
