function figure_downloads() {
	var figs = $("div[id^=F]");
	$( figs ).each( function( index, element ){
	    $(this).find('.fig-caption').prepend('<p class="fig-download"><i class="fa fa-download">&nbsp;</i><a target="_blank" href="' + $( this ).find('img').attr('src') +'">Download</a></p>' );
	});
}

function table_downloads() {
	var tables = $("div[id^=T]");
	$( tables ).each( function( index, element ){
	    $(this).find('.table-caption').prepend('<p class="fig-download"><i class="fa fa-download">&nbsp;</i><a target="_blank" href="table/' + $( this ).attr('id') +'">Download</a></p>' );
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
