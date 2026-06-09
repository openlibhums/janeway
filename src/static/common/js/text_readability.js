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
var cumulativeResize = 0;
var minResize = -3;
var maxResize = 6;

var FONTS = {
  'default': { label: 'Default Font', value: null },
  'sans-serif': { label: 'Sans-serif', value: 'Arial, Verdana, sans-serif' },
  'serif': { label: 'Serif', value: 'Georgia, "Times New Roman", serif' },
  'monospace': { label: 'Monospace', value: '"Courier New", monospace' },
  'opendyslexic': { label: 'OpenDyslexic', value: '"OpenDyslexic", Verdana, sans-serif' }
};

var COLOURS = {
  'default': { label: 'Default Colour', light: '#ffffff', dark: '#1a1a1a' },
  'yellow': { label: 'Yellow', light: '#F5F5DC', dark: '#4c4c4c' },
  'blue': { label: 'Blue', light: '#45E9F2', dark: '#302F31' },
  'green': { label: 'Green', light: '#00EA9A', dark: '#003407' },
  'customise': { label: 'Customise', light: null, dark: null }
};


// In-memory reader preferences. 
var state = {
  font: 'default',
  scheme: 'default',
  darkmode: false,
  noItalics: false,
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

function getRegion() {
  return document.querySelector('.text-format-region');
}

function initialise() {
  if (isInitialised) return; // Prevent double initialisation
  isInitialised = true;
  applyToRegion(function (element) {
    var computedStyle = window.getComputedStyle(element);
    var currentFontSize = parseFloat(computedStyle.fontSize);
    element.style.fontSize = currentFontSize + "px";
  });
}

function resizeText(multiplier) {  
  // Calculate new cumulative value
  var newCumulative = cumulativeResize + multiplier;

  // Check if the new value would be within bounds
  if (newCumulative < minResize || newCumulative > maxResize) {
    return;
  }

  // Update cumulative value and proceed with resize
  cumulativeResize = newCumulative;

  function resize(element) {
    var computedStyle = window.getComputedStyle(element);
    var currentFontSize = parseFloat(computedStyle.fontSize);
    var newFontSize = Math.ceil(currentFontSize + (multiplier * 0.2 * currentFontSize));
    element.style.setProperty('font-size', newFontSize + "px", 'important');
  }

  applyToRegion(resize);

}

function applyToRegion(textFunction) {
  if (!isInitialised) {
    initialise();
  }
  var region = getRegion();
  if (!region) return;
  var allElements = region.querySelectorAll(
    'h1, h2, h3, h4, h5, h6, ' +
    'blockquote, div, p, pre, ' +
    'li, caption, table, tbody, td, tfoot, th, thead, tr, ' +
    'a, b, em, i, label, small, span, strong, code'
  );
  allElements.forEach(textFunction);
}


function applyPreferences() {
  // Reject font or colour preferences we can't resolve *before* touching the DOM, so the caller
  // can roll state back to its last good value. Returns true on a clean apply.
  if (!FONTS[state.font] || !COLOURS[state.scheme]) {
    return false;
  }

  var region = getRegion();
  if (!region) return true;  // state is valid; nothing on the page to paint yet

  // Font
  var font = FONTS[state.font];
  var fontStack = font ? font.value : null;
  if (fontStack) {
    region.style.setProperty('--tf-font', fontStack);
    region.classList.add('tf-has-font');
  } else {
    region.style.removeProperty('--tf-font');
    region.classList.remove('tf-has-font');
  }

  // dark/light is swapping bg/fg.
  var pair = state.scheme === 'customise' ? state.custom : COLOURS[state.scheme];
  if ((state.scheme === 'default' && !state.darkmode ) || !pair) {
    region.style.removeProperty('--tf-bg');
    region.style.removeProperty('--tf-fg');
    region.classList.remove('tf-has-colour');
  } else {
    var background = state.darkmode ? pair.dark : pair.light;
    var foreground = state.darkmode ? pair.light : pair.dark;
    region.style.setProperty('--tf-bg', background);
    region.style.setProperty('--tf-fg', foreground);
    region.classList.add('tf-has-colour');
  }

  // Italics
  if (state.noItalics) {
    region.classList.add('tf-no-italics');
  } else {
    region.classList.remove('tf-no-italics');
  }

  // Reflect the applied state onto every control copy and report success.
  return syncControls();
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
  return true;
 }

// Stub seam for the later persistence phase (account field + session flag
// resolved server-side) to seed `state` before the first apply. A server-rendered context
// (account field for logged-in readers, session flag for anonymous readers)
// will seed `state` here before the first apply.
// All preferences live in an in-memory `state` object. Every change funnels
// through `applyPreferences()`, the single apply point that writes CSS custom
// properties and presence classes onto the target region.
//
// Seed `state` via state._set({...}) rather than assigning fields directly: that
// routes a saved/server value through the same validate-and-rollback path as the
// live controls, so a stale or tampered font/scheme can't lodge an unresolvable
// value in `state`.
function loadPreferences() {
  return;
}

document.addEventListener('DOMContentLoaded', function () {
  loadPreferences();
  applyPreferences();
  lockToggleButtonWidths();
});
