(function () {
  function closeOpenDropdowns(except) {
    document.querySelectorAll('details.a11y-toggle-dropdown[open]').forEach(function (el) {
      if (el !== except) {
        el.removeAttribute('open');
      }
    });
  }

  document.addEventListener('click', function (event) {
    var openDropdown = document.querySelector('details.a11y-toggle-dropdown[open]');
    if (!openDropdown) {
      return;
    }
    if (!openDropdown.contains(event.target)) {
      openDropdown.removeAttribute('open');
    }
  });

  document.addEventListener('keydown', function (event) {
    if (event.key !== 'Escape') {
      return;
    }
    var openDropdown = document.querySelector('details.a11y-toggle-dropdown[open]');
    if (!openDropdown) {
      return;
    }
    openDropdown.removeAttribute('open');
    var summary = openDropdown.querySelector('summary');
    if (summary) {
      summary.focus();
    }
  });

  document.addEventListener('toggle', function (event) {
    var target = event.target;
    if (!(target instanceof Element) || !target.classList.contains('a11y-toggle-dropdown')) {
      return;
    }
    if (target.open) {
      closeOpenDropdowns(target);
    }
  }, true);
})();
