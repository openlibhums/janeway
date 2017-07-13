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

function getUrlVars()
{
    var vars = [], hash;
    var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
    for(var i = 0; i < hashes.length; i++)
    {
        hash = hashes[i].split('=');
        vars.push(hash[0]);
        vars[hash[0]] = hash[1];
    }
    return vars;
}

function submit_note(article_id){
    var text = $('#' + article_id + '_new_note').val();
    data = {'note': text}
    $.ajax({
            "type": "POST",
            "dataType": "json",
            "url": "/kanban/article/" + article_id + "/note/new/",
            "data": data,
            "success": function(data) { 
                $('#' + article_id + '_new_note').val("")
                $('.note-holder').prepend(data.html);
            },
        });
}

try {
    var target_modal = getUrlVars()["article_id"];
    //var popup = new Foundation.Reveal($('#modal-' + target_modal));
    //popup.open();
} catch(err) {
    console.log('Target modal not found or not supplied')
}