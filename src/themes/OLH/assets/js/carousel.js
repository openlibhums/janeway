// Orbit's own autoplay is off because it pauses or resumes on any click
// inside the carousel. Must run after footnotes.js initialises Foundation.
$(document).ready(function () {
    "use strict";

    $("[data-carousel]").each(function () {
        var $root = $(this);
        var $orbit = $root.find("[data-orbit]");
        var orbit = $orbit.data("zfPlugin");
        var $toggle = $root.find("[data-carousel-toggle]");
        if (!orbit || !$toggle.length) {
            return;
        }

        var $container = $orbit.find(".orbit-container");
        var $slides = $orbit.find(".orbit-slide");
        var $current = $root.find("[data-carousel-current]");
        var $toggleIcon = $toggle.find(".fa");
        var delay = parseInt($root.data("carousel-delay"), 10) || 7000;
        var reduceMotion = window.matchMedia &&
            window.matchMedia("(prefers-reduced-motion: reduce)").matches;

        var playing = !reduceMotion;
        if (reduceMotion) {
            orbit.options.useMUI = false;
        }
        var hovered = false;
        var focused = false;
        var timer = null;

        function schedule() {
            window.clearTimeout(timer);
            timer = null;
            if (playing && !hovered && !focused) {
                timer = window.setTimeout(function () {
                    orbit.changeSlide(true);
                }, delay);
            }
        }

        function render() {
            $toggle.attr("aria-label", $toggle.data(playing ? "label-pause" : "label-play"));
            $toggleIcon.toggleClass("fa-pause", playing).toggleClass("fa-play", !playing);
        }

        // Orbit re-adds aria-live="polite" to each new slide; drop it while
        // rotating so every slide isn't announced.
        function quietSlides() {
            if (playing) {
                $slides.filter("[aria-live]").removeAttr("aria-live");
            }
        }
        if (window.MutationObserver) {
            new MutationObserver(quietSlides).observe($orbit[0], {
                attributes: true,
                subtree: true,
                attributeFilter: ["aria-live"],
            });
        }

        $orbit.on("slidechange.zf.orbit", function (event, $newSlide) {
            $current.text($slides.index($newSlide) + 1);
            quietSlides();
            schedule();
        });

        $root.find("[data-carousel-prev]").on("click", function () {
            orbit.changeSlide(false);
        });
        $root.find("[data-carousel-next]").on("click", function () {
            orbit.changeSlide(true);
        });
        $toggle.on("click", function () {
            playing = !playing;
            render();
            quietSlides();
            schedule();
        });

        // Foundation 6.5's swipe detection never fires here, so Orbit's is off.
        var startX = null;
        var startY = null;
        $container[0].addEventListener("touchstart", function (event) {
            startX = event.touches[0].clientX;
            startY = event.touches[0].clientY;
        }, {passive: true});
        $container[0].addEventListener("touchend", function (event) {
            if (startX === null) {
                return;
            }
            var dx = event.changedTouches[0].clientX - startX;
            var dy = event.changedTouches[0].clientY - startY;
            startX = null;
            if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) {
                orbit.changeSlide(dx < 0);
            }
        });

        // Hover counts on the slides only, so resting on Play doesn't hold it.
        $container.on("mouseenter", function () {
            hovered = true;
            schedule();
        }).on("mouseleave", function () {
            hovered = false;
            schedule();
        });
        $root.on("focusin focusout", function () {
            window.setTimeout(function () {
                var active = document.activeElement;
                focused = $.contains($root[0], active) && active !== $toggle[0];
                schedule();
            }, 0);
        });

        render();
        quietSlides();
        schedule();
    });
});
