function copyToClipboard() {
    var linkField = document.getElementById("share-link");

    if (!linkField) {
        console.error("No input field found with ID 'share-link'");
        return;
    }

    navigator.clipboard.writeText(linkField.value).catch(function(err) {
        console.error("Failed to copy: ", err);
    });
}
