document.addEventListener('click', function (event) {
    const button = event.target.closest('[data-dismiss-message]');
    if (button) {
        button.closest('.static-alert').remove();
    }
});
