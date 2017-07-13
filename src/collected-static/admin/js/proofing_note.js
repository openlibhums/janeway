function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
            // Only send the token to relative URLs i.e. locally.
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    }
});


function submit_note(proofing_task_id, galley_id){
    var text = $('#' + galley_id + '_new_note').val();
    data = {'note': text}
    $.ajax({
            "type": "POST",
            "dataType": "json",
            "url": "/proofing/requests/" + proofing_task_id + "/galley/" + galley_id + "/new_note/",
            "data": data,
            "success": function(data) {
                console.log(data);
                $('#' + galley_id + '_new_note').val("")
                $('#' + galley_id + '-note-holder').prepend(data.html);
            },
        });
}


function delete_note(proofing_task_id, galley_id, note_id) {
    data = {'note_id': note_id};
    $.ajax({
            "type": "POST",
            "dataType": "json",
            "url": "/proofing/requests/" + proofing_task_id + "/galley/" + galley_id + "/delete/",
            "data": data,
            "success": function(data) {
                console.log(data);
                $('#note-' + note_id).remove()
            },
        });
}