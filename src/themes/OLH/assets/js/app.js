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

// Accessibility: Toggle aria-expanded for any button with data-toggle
$(document).on('click', '[data-toggle]', function() {
    var $button = $(this);
    var currentExpanded = $button.attr('aria-expanded') === 'true';
    $button.attr('aria-expanded', !currentExpanded);
});

// Accessibility: Handle Nav aria-expanded on keyboard navigation
$(document).on('click', '[aria-expanded]', function() {
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

$(".search-toggle").click(function() {
    var $searchMenu = $("#search-menu");
    if ($searchMenu.is(':visible')) {
        $(".global-search input").focus();
    }
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