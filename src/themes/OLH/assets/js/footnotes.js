$( document ).ready(function() {

    "use strict";

    var element = $(".scroll-link");

    element
        .each(function(i,item) {
            var html = $("a[data-scroll='#" + $(this).attr("id") + "']").parent().clone();
            html.children('a:first').remove();

            $(item).attr('data-tip-text', html.text());
            $(item).attr('data-tooltip', '');
            $(item).attr('aria-haspopup', 'true');
            $(item).attr('class', 'has-tip scroll-link');
            $(item).attr('data-fade-out-duration', 1000);
            // TODO: we need to make sure tooltips stay open while user's mouse is inside

        });

    $(document).foundation()

});
