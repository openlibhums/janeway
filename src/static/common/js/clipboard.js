function copyToClipboard(elementId, event, activatedText) {
    const element = document.getElementById(elementId);
    if (!element) {
        console.error("No element found with ID: " + elementId);
        return;
    }

    // the copied text needs to exclude screenreader-only content and icons.
    const ignoreClasses = ['.sr-only', '.fa'];
    
    function removeElementsByClass(element, classesToRemove){
        const tempElement = element.cloneNode(true);
        classesToRemove.forEach(function(item){
            tempElement.querySelectorAll(item).forEach(el => el.remove());
        });
        return tempElement;
    }

    const button = event.currentTarget;
    const originalContent = button.innerHTML;
    let content, plainText;

    // nb. share links are from inputs which are value, but how-to-cite is html that needs to be rich text
    if (element.tagName === 'INPUT') {
        content = element.value;
        plainText = element.value;
    }
    else {
        content = removeElementsByClass(element, ignoreClasses).innerHTML;
        plainText = removeElementsByClass(element, ignoreClasses).textContent;
    }

    plainText = plainText
        .replace(/\s+/g, ' ')  // Replace multiple spaces with single space
        .replace(/\n\s*\n/g, '\n')  // Replace multiple newlines with single newline
        .trim();  // Remove leading/trailing whitespace

    // Create a single ClipboardItem with both formats
    const clipboardItem = new ClipboardItem({
        'text/plain': new Blob([plainText], { type: 'text/plain' }),
        'text/html': new Blob([content], { type: 'text/html' })
    });

    // Write to clipboard
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
