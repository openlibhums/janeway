// Rejects keywords longer than the submission.models.Keyword.word max_length
// before they become tags, mirroring the server-side validation in
// utils.forms.KeywordModelForm.
$(document).on("tagitbeforetagadded", "#id_keywords", function (event, ui) {
    var maxLength = 200;
    // Tags rebuilt from saved data must never be rejected, or they would be
    // silently dropped from the hidden field on the next save.
    if (ui.duringInitialization) {
        return;
    }
    var tagList = $(event.target).next("ul.tagit");
    var error = tagList.next(".tagit-max-length-error");
    if (ui.tagLabel.length > maxLength) {
        event.preventDefault();
        if (!error.length) {
            error = $('<div class="error tagit-max-length-error" role="alert">')
                .append($('<span class="fa fa-warning" aria-hidden="true">'))
                .append($('<span class="tagit-max-length-error-text">'))
                .insertAfter(tagList);
        }
        error.find(".tagit-max-length-error-text").text(
            " A keyword cannot exceed " + maxLength + " characters."
        );
    } else {
        error.remove();
    }
});
