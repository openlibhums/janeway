// Track if initialisation has been performed
var isInitialised = false;

// Track cumulative resize value
var cumulativeResize = 0;
var minResize = -3;
var maxResize = 6;

function initialise(){
  if (isInitialised) return; // Prevent double initialisation
  isInitialised = true;
  applyToArticle(function(element){
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
    console.log('Resize limit reached. Cumulative: ' + cumulativeResize + ', Attempted: ' + newCumulative);
    return;
  }
  
  // Update cumulative value and proceed with resize
  cumulativeResize = newCumulative;
  
  function resize(element){
    var computedStyle = window.getComputedStyle(element);
    var currentFontSize = parseFloat(computedStyle.fontSize);
    var newFontSize = Math.ceil(currentFontSize + (multiplier * 0.2 * currentFontSize));
    element.style.fontSize = newFontSize + "px";
    element.style.setProperty('font-size', newFontSize + "px", 'important');
  }
  
  applyToArticle(resize);
}

function toggleDyslexia(){
  function toggleDyslexiaClass(element){
    element.classList.toggle('dyslexia-friendly');
  }
  applyToArticle(toggleDyslexiaClass);
}

function applyToArticle(textFunction){
  if (!isInitialised) {
    initialise();
  }
  var articleElement = document.getElementById('article');
  if (!articleElement) return;
  var allElements = articleElement.querySelectorAll(
    'h1, h2, h3, h4, h5, h6, ' +
    'blockquote, div, p, pre, ' +
    'li, caption, table, tbody, td, tfoot, th, thead, tr, ' +
    'a, b, em, i, label, small, span, strong, code'
  );
  allElements.forEach(textFunction);
}