function copyToClipboard(elementId, event, activatedText) {
    const element = document.getElementById(elementId);
    if (!element) {
        console.error("No element found with ID: " + elementId);
        return;
    }

    const button = event.currentTarget;
    const originalContent = button.innerHTML;

    // nb. share links are from inputs which are value, but how-to-cite is html that needs to be rich text
    const content = element.tagName === 'INPUT' ? element.value : element.innerHTML;

    const blob = new Blob([content], { type: 'text/html' });
    const clipboardItem = new ClipboardItem({
        'text/html': blob
    });

    navigator.clipboard.write([clipboardItem])
        .then(() => {
            // Change button text to "Copied" for 5 seconds
            button.innerHTML = '<i aria-hidden="true" class="fa fa-copy"></i>&nbsp;' + activatedText;
            setTimeout(() => {
                button.innerHTML = originalContent;
            }, 5000);
        })
        .catch(function(err) {
            console.error("Failed to copy: ", err);
        });
}
