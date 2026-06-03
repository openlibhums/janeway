(function () {
    var root = document.getElementById('recommendation-form-wrap');
    if (!root) return;
    var sel = root.querySelector('select[name="recommendation"]');
    var input = root.querySelector('[name="suggested_reviewers"]');
    if (!sel || !input) return;
    var wrap = input.closest('label') || input.closest('.row') || input.parentElement;
    function toggle() {
        wrap.style.display = (sel.value === 'accept_for_peer_review') ? '' : 'none';
    }
    sel.addEventListener('change', toggle);
    toggle();
})();
