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

$(".search-toggle").click(function() {
  $(".global-search input").focus();
});

$("#dyslexia-mode").click(function(e) {
    e.preventDefault();
    return $('#article').toggleClass('dyslexia-friendly');
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