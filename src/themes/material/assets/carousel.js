// Replaces Materialize's carousel, whose full-width mode crawls at the end of
// each move and leaves a hairline of background between slides.
(function () {
    "use strict";

    var SWIPE_THRESHOLD = 50;

    function setUp(root) {
        var track = root.querySelector("[data-carousel-track]");
        var slides = Array.prototype.slice.call(root.querySelectorAll(".carousel-item"));
        var toggle = root.querySelector("[data-carousel-toggle]");
        if (!track || slides.length < 2 || !toggle) {
            return;
        }
        var toggleIcon = toggle.querySelector(".fa");
        var current = root.querySelector("[data-carousel-current]");
        var delay = parseInt(root.getAttribute("data-carousel-delay"), 10) || 8000;
        var reduceMotion = window.matchMedia &&
            window.matchMedia("(prefers-reduced-motion: reduce)").matches;

        var index = 0;
        var playing = !reduceMotion;
        var hovered = false;
        var focused = false;
        var timer = null;
        var finishMove = null;

        function schedule() {
            window.clearTimeout(timer);
            timer = null;
            if (playing && !hovered && !focused) {
                timer = window.setTimeout(function () {
                    go(index + 1, 1);
                }, delay);
            }
        }

        function setActive(newIndex) {
            slides.forEach(function (slide, i) {
                var active = i === newIndex;
                slide.classList.toggle("is-active", active);
                if (active) {
                    slide.removeAttribute("inert");
                    slide.removeAttribute("aria-hidden");
                } else {
                    slide.setAttribute("inert", "");
                    slide.setAttribute("aria-hidden", "true");
                }
            });
            if (current) {
                current.textContent = newIndex + 1;
            }
        }

        // direction: 1 brings the new slide in from the right, -1 from the left.
        function go(target, direction) {
            if (finishMove) {
                finishMove();
            }
            var to = (target + slides.length) % slides.length;
            if (to === index) {
                return;
            }
            var outgoing = slides[index];
            var incoming = slides[to];
            index = to;
            setActive(to);

            if (reduceMotion) {
                schedule();
                return;
            }

            outgoing.classList.add("is-leaving");
            incoming.style.transform = "translateX(" + (direction * 100) + "%)";
            void track.offsetWidth;
            track.classList.add("is-moving");
            outgoing.style.transform = "translateX(" + (-direction * 100) + "%)";
            incoming.style.transform = "translateX(0)";

            var done = false;
            finishMove = function () {
                if (done) {
                    return;
                }
                done = true;
                finishMove = null;
                track.classList.remove("is-moving");
                outgoing.classList.remove("is-leaving");
                outgoing.style.transform = "";
                incoming.style.transform = "";
                incoming.removeEventListener("transitionend", onEnd);
            };
            function onEnd(event) {
                if (event.target === incoming && event.propertyName === "transform") {
                    finishMove();
                }
            }
            incoming.addEventListener("transitionend", onEnd);
            // transitionend can be skipped, e.g. in a hidden tab.
            window.setTimeout(function () {
                if (finishMove) {
                    finishMove();
                }
            }, 1000);
            schedule();
        }

        function render() {
            track.setAttribute("aria-live", playing ? "off" : "polite");
            toggle.setAttribute(
                "aria-label",
                toggle.getAttribute(playing ? "data-label-pause" : "data-label-play")
            );
            toggleIcon.classList.toggle("fa-pause", playing);
            toggleIcon.classList.toggle("fa-play", !playing);
        }

        toggle.addEventListener("click", function () {
            playing = !playing;
            render();
            schedule();
        });
        root.querySelector("[data-carousel-prev]").addEventListener("click", function () {
            go(index - 1, -1);
        });
        root.querySelector("[data-carousel-next]").addEventListener("click", function () {
            go(index + 1, 1);
        });

        var startX = null;
        var startY = null;
        track.addEventListener("touchstart", function (event) {
            startX = event.touches[0].clientX;
            startY = event.touches[0].clientY;
        }, {passive: true});
        track.addEventListener("touchend", function (event) {
            if (startX === null) {
                return;
            }
            var dx = event.changedTouches[0].clientX - startX;
            var dy = event.changedTouches[0].clientY - startY;
            startX = null;
            if (Math.abs(dx) > SWIPE_THRESHOLD && Math.abs(dx) > Math.abs(dy)) {
                if (dx < 0) {
                    go(index + 1, 1);
                } else {
                    go(index - 1, -1);
                }
            }
        });

        track.addEventListener("mouseenter", function () {
            hovered = true;
            schedule();
        });
        track.addEventListener("mouseleave", function () {
            hovered = false;
            schedule();
        });
        ["focusin", "focusout"].forEach(function (type) {
            root.addEventListener(type, function () {
                window.setTimeout(function () {
                    var active = document.activeElement;
                    focused = root.contains(active) && active !== toggle;
                    schedule();
                }, 0);
            });
        });

        setActive(0);
        render();
        schedule();
    }

    function init() {
        Array.prototype.forEach.call(document.querySelectorAll("[data-carousel]"), setUp);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
