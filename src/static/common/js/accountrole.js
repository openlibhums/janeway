function add_role(user_id, role_id, journal_id){
    data = {
        'user': user_id,
        'role': role_id,
        'journal': journal_id
    }

    $.ajax({
        "type": "POST",
        "dataType": "json",
        "url": '/api/accountrole/',
        "data": data,
        "success": function(data) {
            console.log(data)
            $( "#" + user_id ).remove();
            toastr.success('User has been granted role.')
        },
        "error": function (xhr, status, error) {
            toastr.error(xhr.responseText)
        },
    })
}