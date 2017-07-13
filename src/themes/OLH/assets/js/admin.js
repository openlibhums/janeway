(function() {
  $(function() {
    var collapseMyMenu, expandMyMenu, hideMenuTexts, showMenuTexts;
    expandMyMenu = function() {
      return $("nav.sidebar").removeClass("sidebar-menu-collapsed").addClass("sidebar-menu-expanded");
    };
    collapseMyMenu = function() {
      return $("nav.sidebar").removeClass("sidebar-menu-expanded").addClass("sidebar-menu-collapsed");
    };
    showMenuTexts = function() {
      return $("nav.sidebar ul a span.expanded-element").show();
    };
    hideMenuTexts = function() {
      return $("nav.sidebar ul a span.expanded-element").hide();
    };
    return $("#justify-icon").click(function(e) {
      if ($(this).parent("nav.sidebar").hasClass("sidebar-menu-collapsed")) {
        expandMyMenu();
        showMenuTexts();
        $(this).css({
          color: "#2A3036"
        });
      } else if ($(this).parent("nav.sidebar").hasClass("sidebar-menu-expanded")) {
        collapseMyMenu();
        hideMenuTexts();
        $(this).css({
          color: "#FFF"
        });
      }
      return false;
    });
  });

}).call(this);
