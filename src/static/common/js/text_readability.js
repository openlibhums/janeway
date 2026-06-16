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

  toggleReadingBar: function () {
    this._toggle('hideReadingBar');
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

// Show or hide the whole reading options bar. The server renders it already
// hidden (inline style) when the saved preference says so, so this only has to
// keep it in step with live toggles.
function applyBarVisibility() {
  var bar = getBar();
  if (!bar) {
    return;
  }
  var wasHidden = bar.style.display === 'none';
  bar.style.display = state.hideReadingBar ? 'none' : '';
  // Foundation's sticky plugin measured the bar while it was hidden (zero
  // width), so it ends up mis-sized and shoved left when first revealed. A
  // resize makes Foundation recalculate its dimensions.
  if (wasHidden && !state.hideReadingBar) {
    window.dispatchEvent(new Event('resize'));
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
  document.querySelectorAll('.tf-font-select').forEach(function (button) {
    var label = button.querySelector('.tf-label');
    if (label) {
      label.textContent = (FONTS[state.font] || FONTS['default']).label;
    }
  });
  document.querySelectorAll('.tf-scheme-select').forEach(function (button) {
    var label = button.querySelector('.tf-label');
    if (label) {
      label.textContent = (COLOURS[state.scheme] || COLOURS['default']).label;
    }
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
    var newLabel = dark ? 'Dark mode on' : 'Dark mode off';
    var oldLabel = button.getAttribute('aria-label');
    if (button.dataset.labelToDark || button.dataset.labelToLight) {
      // Text themes (clean/material): swap the label to the next action.
      button.textContent = dark ? button.dataset.labelToLight : button.dataset.labelToDark;
    } else {
      // Icon themes (OLH): aria-pressed carries state and drives the tick.
      button.setAttribute('aria-pressed', dark);
      button.setAttribute('aria-label', newLabel);
    }
  });
  document.querySelectorAll('[data-tf-toggle="italics"]').forEach(function (button) {
    var italicsPresent = !state.noItalics;
    var newLabel = italicsPresent ? 'Italics on' : 'Italics off';
    var oldLabel = button.getAttribute('aria-label');
    if (button.dataset.labelRemove || button.dataset.labelShow) {
      button.textContent = state.noItalics ? button.dataset.labelShow : button.dataset.labelRemove;
    } else {
      // Tick shows when italics are present (the default state).
      button.setAttribute('aria-pressed', italicsPresent);
      button.setAttribute('aria-label', newLabel);
    }
  });
  // The reading-bar switch lives in the nav accessibility menu; "on" means the
  // bar is shown. Translated On/Off labels come from data attributes.
  document.querySelectorAll('[data-tf-bar-toggle]').forEach(function (button) {
    var shown = !state.hideReadingBar;
    button.setAttribute('aria-checked', shown);
    button.classList.toggle('a11y-switch--on', shown);
    var stateLabel = button.querySelector('.a11y-switch-state');
    if (stateLabel) {
      stateLabel.textContent = shown
        ? (button.dataset.labelOn || 'On')
        : (button.dataset.labelOff || 'Off');
    }
  });
  return true;
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

// The reading-bar switch is rendered (disabled) in the global nav on every
// page; only enable and wire it where this script — and so the bar — is loaded.
function enableBarToggle() {
  document.querySelectorAll('[data-tf-bar-toggle]').forEach(function (button) {
    button.disabled = false;
    button.addEventListener('click', function () {
      state.toggleReadingBar();
    });
  });
}

document.addEventListener('DOMContentLoaded', function () {
  loadPreferences();
  applyPreferences();
  var preload = document.getElementById('tf-preload');
  if (preload) {
    preload.remove();
  }
  enableBarToggle();
  lockToggleButtonWidths();
  lockSelectLabelWidths();
});
