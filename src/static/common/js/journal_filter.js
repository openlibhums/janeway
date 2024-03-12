jQuery.expr[":"].Contains = jQuery.expr.createPseudo(function (arg) {
    return function (elem) {
        return jQuery(elem).text().toUpperCase().indexOf(arg.toUpperCase()) >= 0;
    };
});
var journals = $('.journal-div');
$('#filter').keyup(function () {
    var filter = $("#filter").val();
    console.log(filter);
    if (filter) {
        var $found = journals.find('.journal-description-box span:contains("' + filter.toLowerCase() + '")').closest('.journal-div').show();
        journals.not($found).hide()
    } else {
        journals.show();
    }
});