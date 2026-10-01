$(function() {
  $('a[href*="#"]:not([href="#"])').click(function() {
    if (location.pathname.replace(/^\//,'') == this.pathname.replace(/^\//,'') && location.hostname == this.hostname) {
      var target = $(this.hash);
      target = target.length ? target : $('[name=' + this.hash.slice(1) +']');
      if (target.length) {
        $('html,body').animate({
          scrollTop: target.offset().top - $(".mini-bar").outerHeight()
        }, 1000);
      }
    }
  });

  if (location.pathname.split("/")[1]) {
    $('.main-header .menu li a[href^="/' + location.pathname.split("/")[1] + '"]').addClass('active');
  }
});

// Accessibility: Handle Nav aria-expanded on keyboard navigation
// (responsive toggle buttons are synced from menu visibility, see below)
$(document).on('click', '[aria-expanded]:not([data-toggle])', function() {
    var $button = $(this);
    var currentExpanded = $button.attr('aria-expanded') === 'true';
    $button.attr('aria-expanded', !currentExpanded);
});

function toggleAriaExpanded(submenu, expanded) {
  var $parent = submenu.parent('li.is-dropdown-submenu-parent');
  var $button = $parent.find('a[aria-expanded]');
  $button.attr('aria-expanded', expanded);
}

// Accessibility: Listen for Foundation menu events to update aria-expanded
$(document).ready(function() {
    // dropdown menu (wide screen)
    $(document).on('show.zf.dropdownmenu', function(event, $sub) {
        toggleAriaExpanded($sub, true);
    });
    
    $(document).on('hide.zf.dropdownmenu', function(event, $sub) {
        $('a[aria-expanded="true"]').attr('aria-expanded', 'false');
    });
    
    // drilldown menu (narrow screen)
    $(document).on('open.zf.drilldown', function(event, $elem) {
      toggleAriaExpanded($elem, true);
    });
    
    $(document).on('hide.zf.drilldown', function(event, $elem) {
        $('a[aria-expanded="true"]').attr('aria-expanded', 'false');
    });
});

// Accessibility: Sync aria-expanded on the mobile menu and search toggles
$(document).on('toggled.zf.responsiveToggle', '[data-responsive-toggle]', function() {
    var menuId = $(this).attr('data-responsive-toggle');
    var isOpen = $('#' + menuId).is(':visible');
    $('[aria-controls="' + menuId + '"]').attr('aria-expanded', isOpen ? 'true' : 'false');
    if (menuId === 'search-menu' && isOpen) {
        $(".global-search input").focus();
    }
});

// Foundation's drilldown moves keyboard focus between links only, so the
// accessibility mode switch (a button in a form) in the mobile menu could
// not be reached. Move focus through that submenu's items ourselves, in the
// capture phase so Foundation's handlers on the links don't run.
$(".a11y-mobile-form").closest("ul").each(function() {
    var submenu = this;
    var trigger = $(submenu).siblings("a").get(0);
    var openedByKeyboard = false;

    function items() {
        return $(submenu).children("li").find("> a, > form button").filter(":visible").get();
    }

    submenu.addEventListener("keydown", function(e) {
        var list = items();
        var index = list.indexOf(document.activeElement);
        var step = 0;
        if (e.key === "ArrowDown" || (e.key === "Tab" && !e.shiftKey)) {
            step = 1;
        } else if (e.key === "ArrowUp" || (e.key === "Tab" && e.shiftKey)) {
            step = -1;
        }
        var next = list[index + step];
        if (index === -1 || !step || !next) {
            return;
        }
        e.preventDefault();
        e.stopImmediatePropagation();
        next.focus();
    }, true);

    // Opening the submenu from the keyboard focuses its first link, which
    // skips the switch; focus the switch instead.
    if (trigger) {
        trigger.addEventListener("keydown", function(e) {
            openedByKeyboard = ["Enter", " ", "ArrowRight"].indexOf(e.key) !== -1;
        }, true);
    }
    submenu.addEventListener("focusin", function(e) {
        if (!openedByKeyboard) {
            return;
        }
        openedByKeyboard = false;
        var button = $(submenu).find(".a11y-mobile-form button").get(0);
        if (button && e.target !== button && $(button).is(":visible")) {
            button.focus();
        }
    });
});



function kanbanInit() {
  var $kanbanSelector = $(".kanban");
  var $boxSelector = $kanbanSelector.find(".box");
  var boxCount = $boxSelector.length;

  var boxWidth = $boxSelector.outerWidth(true);
  var innerWidth = boxWidth * boxCount;

  $kanbanSelector.find(".inner").width(innerWidth);

  $kanbanSelector.perfectScrollbar();
  $kanbanSelector.find(".box .content").perfectScrollbar();
}