$(document).ready(function () {
    $(".tagit-field").each(function () {
        $(this).tagit(
	    {allowSpaces: $(this).data("allowSpaces") === true});
    });
});
