function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    if (!element) {
        console.error("No element found with ID: " + elementId);
        return;
    }

    // nb. share links are from inputs which are value, but how-to-cite is html that needs to be rich text
    const content = element.tagName === 'INPUT' ? element.value : element.innerHTML;

    const blob = new Blob([content], { type: 'text/html' });
    const clipboardItem = new ClipboardItem({
        'text/html': blob
    });

    navigator.clipboard.write([clipboardItem]).catch(function(err) {
        console.error("Failed to copy: ", err);
    });
}
