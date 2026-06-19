// Reader-configurable text formatting for the .text-format-region target.

// Track if initialisation has been performed
var isInitialised = false;

// Initialize on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initialise);
} else {
  initialise();
}

// Variables
// initial apply does not POST the just-loaded value straight back to the server.
var isLoading = false;

var options = JSON.parse(document.getElementById('tf-options').textContent);
var FONTS = options.fonts;
var COLOURS = options.schemes;
var sizeBounds = options.sizeBounds;


// In-memory reader preferences.
var state = {
  font: 'default',
  scheme: 'default',
  darkmode: false,
  noItalics: false,
  hideReadingBar: false,
  textSize: 0,
  custom: { light: '#ffffff', dark: '#1a1a1a' },

  _assign: function (changes) {
    var previous = {};
    for (var key in changes) {
      if (key === 'custom') {
        previous.custom = {};
        for (var colour in changes.custom) {
          previous.custom[colour] = this.custom[colour];
          this.custom[colour] = changes.custom[colour];
        }
      } else {
        previous[key] = this[key];
        this[key] = changes[key];
      }
    }
    return previous;
  },

  _set: function (changes) {
    var previous = this._assign(changes);
    if (!applyPreferences()) {
      this._assign(previous);
    } else if (!isLoading) {
      savePreferences();
    }
  },

  _toggle: function (key) {
    var changes = {};
    changes[key] = !this[key];
    this._set(changes);
  },

  setFont: function (fontKey) {
    this._set({ font: fontKey });
  },

  setScheme: function (schemeKey) {
    this._set({ scheme: schemeKey });
  },

  toggleDarkMode: function () {
    this._toggle('darkmode');
  },

  toggleNoItalics: function () {
    this._toggle('noItalics');
  },

  setReadingBarHidden: function (hidden) {
    this._set({ hideReadingBar: hidden });
  },

  setCustomColours: function (lightColour, darkColour) {
    this._set({ custom: { light: lightColour, dark: darkColour } });
  },

  // The granular custom-colour setters only report their own value (no
  // cross-element id lookups, which would break under the material theme's
  // duplicated control block).
  setCustomLight: function (value) {
    this._set({ custom: { light: value } });
  },

  setCustomDark: function (value) {
    this._set({ custom: { dark: value } });
  }
};


// Action Functions

function getRegions() {
  return document.querySelectorAll('.text-format-region');
}

function getBar() {
  return document.getElementById('tf-bar');
}

// Show or hide the whole reading options bar. 
function applyBarVisibility() {
  var bar = getBar();
  if (!bar) {
    return;
  }
  var wasHidden = bar.classList.contains('tf-bar-hidden');
  bar.classList.toggle('tf-bar-hidden', state.hideReadingBar);
  // Foundation's sticky plugin measured the bar while it was hidden (zero
  // width), so it ends up mis-sized and shoved left when first revealed. A
  // resize makes Foundation recalculate its dimensions.
  if (wasHidden && !state.hideReadingBar) {
    window.dispatchEvent(new Event('resize'));
  }
}


// After closing the bar, move focus to the accessibility menu
// ensures keyboard/sr aren't focused on nothing.
function hideReadingBar() {
  state.setReadingBarHidden(true);
  focusAccessibilityMenu();
}

function focusAccessibilityMenu() {
  var button = document.querySelector('.a11y-toggle-summary');
  if (button) {
    button.focus();
  }
}

// On show, move focus to the first visible control in the bar 
function focusBar() {
  var bar = getBar();
  if (!bar) return;
  var candidates = bar.querySelectorAll('button, a[href], input');
  for (var i = 0; i < candidates.length; i++) {
    if (candidates[i].offsetParent !== null) {
      candidates[i].focus();
      return;
    }
  }
}

function initialise() {
  if (isInitialised) return; // Prevent double initialisation
  isInitialised = true;
  applyToRegion(function (element) {
    var computedStyle = window.getComputedStyle(element);
    element.dataset.tfBaseSize = parseFloat(computedStyle.fontSize);
  });
}

function resizeText(multiplier) {
  var next = state.textSize + multiplier;
  // Ignore steps that would take us out of bounds.
  if (next < sizeBounds.min || next > sizeBounds.max) {
    return;
  }

  state._set({ textSize: next });
}

function applyFontSize() {
  var step = state.textSize || 0;
  applyToRegion(function (element) {
    var base = parseFloat(element.dataset.tfBaseSize);
    if (!base) return;
    if (step === 0) {
      element.style.removeProperty('font-size');
    } else {
      var size = Math.ceil(base * (1 + 0.2 * step));
      element.style.setProperty('font-size', size + 'px', 'important');
    }
  });
}

function applyToRegion(textFunction) {
  if (!isInitialised) {
    initialise();
  }
  getRegions().forEach(function (region) {
    textFunction(region);
    var allElements = region.querySelectorAll(
      'h1, h2, h3, h4, h5, h6, ' +
      'blockquote, div, p, pre, ' +
      'li, caption, table, tbody, td, tfoot, th, thead, tr, ' +
      'a, b, em, i, label, small, span, strong, code'
    );
    allElements.forEach(textFunction);
  });
}


function applyPreferences() {
  // Reject font or colour preferences we can't resolve *before* touching the DOM, so the caller
  // can roll state back to its last good value. Returns true on a clean apply.
  if (!FONTS[state.font] || !COLOURS[state.scheme]) {
    return false;
  }

  getRegions().forEach(paintRegion);
  applyFontSize();
  applyBarVisibility();
  // Reflect the applied state onto every control copy and report success.
  return syncControls();
}

// Write the current preferences onto a single region as CSS custom properties
// and presence classes; its descendants inherit them via the stylesheet rules.
function paintRegion(region) {
  // Font
  var font = FONTS[state.font];
  var fontStack = font ? font.value : null;
  if (fontStack) {
    region.style.setProperty('--tf-font', fontStack);
    region.classList.add('tf-has-font');

    // FontAwesome keeps its glyphs via its own !important.
    region.style.setProperty('font-family', fontStack, 'important');
  } else {
    region.style.removeProperty('--tf-font');
    region.classList.remove('tf-has-font');
    region.style.removeProperty('font-family');
  }

  // dark/light is swapping bg/fg.
  var pair = state.scheme === 'customise' ? state.custom : COLOURS[state.scheme];
  var wantColour = !((state.scheme === 'default' && !state.darkmode) || !pair);

  // Animate the colour change only for a live toggle, not the initial apply of
  // a restored preference — a new page should load already in its colour, not
  // fade into it.
  region.classList.toggle(
    'tf-default-transition',
    !isLoading && wantColour !== region.classList.contains('tf-has-colour')
  );

  if (wantColour) {
    var background = state.darkmode ? pair.dark : pair.light;
    var foreground = state.darkmode ? pair.light : pair.dark;
    region.style.setProperty('--tf-bg', background);
    region.style.setProperty('--tf-fg', foreground);
    region.classList.add('tf-has-colour');
  } else {
    region.style.removeProperty('--tf-bg');
    region.style.removeProperty('--tf-fg');
    region.classList.remove('tf-has-colour');
  }

  // Italics
  if (state.noItalics) {
    region.classList.add('tf-no-italics');
  } else {
    region.classList.remove('tf-no-italics');
  }
}

// The toggle buttons swap their label between two strings of different length.
// Lock each one to the width of its widest label so the button does not resize
// as the label changes. Measured (rather than a guessed CSS width) so it stays
// correct across themes, fonts and translations.
function lockToggleButtonWidths() {
  document.querySelectorAll('[data-tf-toggle]').forEach(function (button) {
    var data = button.dataset;
    var labels = [
      data.labelToDark, data.labelToLight, data.labelRemove, data.labelShow
    ].filter(Boolean);
    if (labels.length < 2) return;
    button.style.minWidth = '';
    var current = button.textContent;
    var widest = 0;
    labels.forEach(function (text) {
      button.textContent = text;
      if (button.offsetWidth > widest) {
        widest = button.offsetWidth;
      }
    });
    button.textContent = current;
    if (widest) {
      button.style.minWidth = widest + 'px';
    }
  });
}

function lockSelectLabelWidths() {
  var groups = [
    { selector: '.tf-font-select', options: FONTS },
    { selector: '.tf-scheme-select', options: COLOURS }
  ];
  groups.forEach(function (group) {
    var labels = Object.keys(group.options).map(function (key) {
      return group.options[key].label;
    });
    if (labels.length < 2) return;
    document.querySelectorAll(group.selector).forEach(function (button) {
      var label = button.querySelector('.tf-label');
      if (!label) return;
      // inline-block so min-width reserves space even in themes (OLH) where the
      // label would otherwise be an inline span.
      label.style.display = 'inline-block';
      // Clear any previous lock so a re-measure (e.g. after webfonts load)
      // starts from the natural width, not a stale, possibly-too-small minimum.
      label.style.minWidth = '';
      var current = label.textContent;
      var widest = 0;
      labels.forEach(function (text) {
        label.textContent = text;
        if (label.offsetWidth > widest) {
          widest = label.offsetWidth;
        }
      });
      label.textContent = current;
      if (widest) {
        label.style.minWidth = widest + 'px';
      }
    });
  });
}

  // Reflect state back onto controls.
function syncControls() {
  // Keep the menu-button labels in step with the selection. 
  setLabelText('.tf-font-select', (FONTS[state.font] || FONTS['default']).label);
  setLabelText('.tf-scheme-select', (COLOURS[state.scheme] || COLOURS['default']).label);
  document.querySelectorAll('.tf-custom-colours').forEach(function (block) {
    block.hidden = state.scheme !== 'customise';
  });
  document.querySelectorAll('.tf-custom-light').forEach(function (input) {
    input.value = state.custom.light;
  });
  document.querySelectorAll('.tf-custom-dark').forEach(function (input) {
    input.value = state.custom.dark;
  });
  document.querySelectorAll('.tf-custom-colours').forEach(function (block) {
    block.hidden = state.scheme !== 'customise';
  });
  document.querySelectorAll('.tf-custom-light').forEach(function (input) {
    input.value = state.custom.light;
  });
  document.querySelectorAll('.tf-custom-dark').forEach(function (input) {
    input.value = state.custom.dark;
  });
  document.querySelectorAll('[data-tf-toggle="mode"]').forEach(function (button) {
    var dark = state.darkmode;
    if (button.dataset.labelToDark || button.dataset.labelToLight) {
      // Text themes (clean/material): swap the label to the next action.
      button.textContent = dark ? button.dataset.labelToLight : button.dataset.labelToDark;
    } else {
      setToggleState(button, dark);
    }
  });
  document.querySelectorAll('[data-tf-toggle="italics"]').forEach(function (button) {
    // aria-pressed (and the tick) mean italics are present, the default state.
    var italicsPresent = !state.noItalics;
    if (button.dataset.labelRemove || button.dataset.labelShow) {
      button.textContent = state.noItalics ? button.dataset.labelShow : button.dataset.labelRemove;
    } else {
      setToggleState(button, italicsPresent);
    }
  });

  // Mark the active font/colour as "current" for aria.
  syncCurrentOption('[data-tf-font-option]', 'tfFontOption', state.font);
  syncCurrentOption('[data-tf-scheme-option]', 'tfSchemeOption', state.scheme);

  document.querySelectorAll('[data-tf-bar-show]').forEach(function (button) {
    button.disabled = !state.hideReadingBar;
  });
  // The mobile toggle's expanded state mirrors the shared hideReadingBar state.
  document.querySelectorAll('.title-bar-title').forEach(function (button) {
    button.setAttribute('aria-expanded', state.hideReadingBar ? 'false' : 'true');
  });
  return true;
 }

// Set the visible (and accessible) label of a select-style menu button
function setLabelText(selector, text) {
  document.querySelectorAll(selector).forEach(function (button) {
    var label = button.querySelector('.tf-label');
    if (label && label.textContent !== text) {
      label.textContent = text;
    }
  });
}

// Reflect a toggle button's state through aria-pressed
function setToggleState(button, isOn) {
  var pressed = isOn ? 'true' : 'false';
  if (button.getAttribute('aria-pressed') !== pressed) {
    button.setAttribute('aria-pressed', pressed);
  }
}

function syncCurrentOption(selector, datasetKey, activeValue) {
  document.querySelectorAll(selector).forEach(function (button) {
    var shouldBeCurrent = button.dataset[datasetKey] === activeValue;
    if (shouldBeCurrent === (button.getAttribute('aria-current') === 'true')) {
      return;
    }
    if (shouldBeCurrent) {
      button.setAttribute('aria-current', 'true');
    } else {
      button.removeAttribute('aria-current');
    }
  });
}

// Persistence. Preferences are stored server-side (Account field for logged-in
// readers, session for anonymous ones), resolved in core/logic.py and seeded
// into the page as JSON by the reading options bar template.

function getConfig() {
  return document.getElementById('tf-config');
}

// The serialisable preference data: every non-function property of `state`. 
// New settings added to `state` are persisted automatically
function serialiseState() {
  var data = {};
  Object.keys(state).forEach(function (key) {
    if (typeof state[key] !== 'function') {
      data[key] = state[key];
    }
  });
  return data;
}

// Seed `state` from the server-rendered JSON before the first apply.
function loadPreferences() {
  var seed = document.getElementById('tf-preferences');
  if (!seed) return;
  var saved;
  try {
    saved = JSON.parse(seed.textContent);
  } catch (e) {
    return;
  }
  if (!saved || typeof saved !== 'object' || !Object.keys(saved).length) {
    return;
  }
  isLoading = true;
  state._set(saved);
  isLoading = false;
}

// Persist the current state. Debounced so rapid changes.
var saveTimer = null;
function savePreferences() {
  var config = getConfig();
  if (!config || !config.dataset.saveUrl) return;
  if (saveTimer) {
    clearTimeout(saveTimer);
  }
  saveTimer = setTimeout(function () {
    fetch(config.dataset.saveUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': config.dataset.csrf || ''
      },
      credentials: 'same-origin',
      body: JSON.stringify(serialiseState())
    }).catch(function () { /* persistence is best-effort */ });
  }, 400);
}

// The "Show reading options" item is rendered (hidden) in the global nav on
// every page; reveal and wire it only where this script — and so the bar — is
// loaded. It then stays in the menu; syncControls enables it only while the bar
// is hidden, so it doesn't vanish under the cursor when clicked.
function enableBarShow() {
  document.querySelectorAll('.a11y-bar-show-item').forEach(function (item) {
    item.hidden = false;
  });
  document.querySelectorAll('[data-tf-bar-show]').forEach(function (button) {
    button.addEventListener('click', function () {
      state.setReadingBarHidden(false);
      // Close the accessibility menu we opened to reach this button, then move
      // focus into the now-visible bar.
      var details = button.closest('details');
      if (details) {
        details.open = false;
      }
      focusBar();
    });
  });
}


// layouts stay in sync (rotate a device: shown<->expanded, hidden<->collapsed).
function wireReadingOptionsToggle() {
  var bar = getBar();
  if (!bar) return;
  var button = bar.querySelector('.title-bar-title');
  if (!button) return;
  button.addEventListener('click', function (e) {
    e.preventDefault();
    state.setReadingBarHidden(!state.hideReadingBar);
  });
}

// In-bar dropdowns (Font, Colour, Cite) for themes without Foundation.
// CSS reveals the menu on the button's aria-expanded="true".
function wireBarDropdowns() {
  if (window.Foundation) return;
  var bar = getBar();
  if (!bar) return;
  var toggles = bar.querySelectorAll('[aria-haspopup="true"][aria-controls]');

  function closeAll(except) {
    toggles.forEach(function (toggle) {
      if (toggle !== except) {
        toggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  toggles.forEach(function (toggle) {
    var item = toggle.parentNode; // the <li> wrapping button + menu
    var menu = document.getElementById(toggle.getAttribute('aria-controls'));
    if (!menu) return;

    toggle.addEventListener('click', function (e) {
      e.preventDefault();
      var open = toggle.getAttribute('aria-expanded') === 'true';
      closeAll(toggle); // only one open at a time
      toggle.setAttribute('aria-expanded', open ? 'false' : 'true');
    });

    menu.querySelectorAll('button, a').forEach(function (entry) {
      entry.addEventListener('click', function () {
        toggle.setAttribute('aria-expanded', 'false');
        if (entry.tagName === 'BUTTON') {
          toggle.focus();
        }
      });
    });

    // Tabbing or clicking out of the whole control closes it.
    item.addEventListener('focusout', function (e) {
      if (!item.contains(e.relatedTarget)) {
        toggle.setAttribute('aria-expanded', 'false');
      }
    });

    // Escape closes and returns focus to the button.
    item.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
        toggle.setAttribute('aria-expanded', 'false');
        toggle.focus();
      }
    });
  });

  // A click anywhere outside the bar closes any open dropdown.
  document.addEventListener('click', function (e) {
    if (!bar.contains(e.target)) {
      closeAll(null);
    }
  });
}

// Lock the variable-width controls so they don't resize as their label changes.
function lockControlWidths() {
  lockToggleButtonWidths();
  lockSelectLabelWidths();
}

document.addEventListener('DOMContentLoaded', function () {
  loadPreferences();
  applyPreferences();
  var preload = document.getElementById('tf-preload');
  if (preload) {
    preload.remove();
  }
  enableBarShow();
  lockControlWidths();
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(lockControlWidths);
  }
  wireReadingOptionsToggle();
  wireBarDropdowns();
});
