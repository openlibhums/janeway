function setTimezone() {
    browserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone
    data = {
        "chosen_timezone": browserTimezone
    }
    $.ajax({
        "type": "POST",
        "dataType": "json",
        "url": '/set-timezone/',
        "data": data,
        "success": function(data){
            console.log("timezone set")
        },
        "error": function (xhr, status, error) {
            console.log(status, error);
        }
    })
    console.log(data)
}
