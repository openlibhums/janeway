function figure_downloads() {
	var figs = $("div.fig-inline-img-set");
	$( figs ).each( function( index, element ){
        var divId = $(this).attr('id');
	    $(this).find('.fig-caption').prepend('<p class="fig-download"><i class="fa fa-download">&nbsp;</i><a target="_blank" aria-describedby="' + divId + '" href="' + $( this ).find('img').attr('src') +'">Download</a></p>' );	});
}

function table_downloads() {
	var tables = $("div.table-expansion");
	$( tables ).each( function( index, element ){
        var divId = $(this).attr('id');
	    $(this).find('.table-caption').prepend('<p class="fig-download"><i class="fa fa-download">&nbsp;</i><a target="_blank" aria-describedby="' + divId + '" href="table/' + $( this ).attr('id') +'">Download</a></p>' );	});
}


$( document ).ready(function(){
    figure_downloads();
    table_downloads();
    initSidenavAccessibility();
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

/**
 * Handles closing sidenav when keyboard focus leaves it and escape key functionality
 */
function initSidenavAccessibility() {
    // Wait for Materialize to initialize
    setTimeout(function() {
        var sidenavInstance = M.Sidenav.getInstance(document.getElementById('nav-mobile'));
        var sidenavTrigger = document.querySelector('.sidenav-trigger');
        var sidenavElement = document.getElementById('nav-mobile');
        
        if (!sidenavInstance || !sidenavElement) {
            return;
        }
        
        var originalTrigger = null;
        
        // Handle escape key to close sidenav
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && sidenavInstance.isOpen) {
                sidenavInstance.close();
                // Return focus to the trigger button
                if (sidenavTrigger) {
                    sidenavTrigger.focus();
                }
            }
        });
        
        // Handle focus management when sidenav opens
        sidenavElement.addEventListener('focusin', function(e) {
            // Store the trigger when sidenav opens
            if (!originalTrigger && sidenavTrigger) {
                originalTrigger = sidenavTrigger;
            }
        });
        
        // Handle focus leaving the sidenav
        sidenavElement.addEventListener('focusout', function(e) {
            setTimeout(function() {
                var activeElement = document.activeElement;
                var isFocusInSidenav = sidenavElement.contains(activeElement) || 
                                     sidenavElement === activeElement;
                
                // If focus is not in sidenav and sidenav is open, close it
                if (!isFocusInSidenav && sidenavInstance.isOpen) {
                    sidenavInstance.close();
                    if (originalTrigger && originalTrigger.offsetParent !== null) {
                        originalTrigger.focus();
                    }
                }
            }, 10);
        });
        
        // Handle clicking outside sidenav to close it (additional accessibility)
        document.addEventListener('click', function(e) {
            if (sidenavInstance.isOpen) {
                var isClickInSidenav = sidenavElement.contains(e.target);
                var isClickOnTrigger = sidenavTrigger && sidenavTrigger.contains(e.target);
                
                if (!isClickInSidenav && !isClickOnTrigger) {
                    sidenavInstance.close();
                }
            }
        });
        
    }, 100); // Small delay to ensure Materialize has initialized
}
