function figure_downloads() {
	var figs = $("div[id^=F]");
	$( figs ).each( function( index, element ){
        var label = $(this).find('.fig-label');
        label.append('<span class="fig-download"><a target="_blank" href="' + $( this ).find('img').attr('src') +'"><i aria-hidden="true" class="fa fa-download">&nbsp;</i><span class="sr-only"> Download '+ label.text() +'</span></a></span>' );
	});
}

function table_downloads() {
	var tables = $("div[id^=T]");
	$( tables ).each( function( index, element ){
        var label = $(this).find('.table-label');
	    label.append('<span class="fig-download"><a target="_blank" href="table/' + $( this ).attr('id') +'"><i aria-hidden="true" class="fa fa-download">&nbsp;</i><span class="sr-only"> Download '+ label.text() +'</span></a></span>' );
	});
}


$( document ).ready(function(){
    figure_downloads();
    table_downloads();
})

var $root = $('html, body');

$('a[href^="#"]:not(a[href$="!"])').click(function() {
  // The jquery selector needs to exclude href="#!"
  // or the event listener will interfere with the sidenav trigger
    var href = $.attr(this, 'href');
    if (href) {

        $root.animate({
            scrollTop: $(href).offset().top
        }, 500, function () {
            window.location.hash = href;
        });
    }

    return false;
});
