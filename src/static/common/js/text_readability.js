function resizeText(multiplier) {
  if (document.body.style.fontSize == "") {
    document.body.style.fontSize = "1.0em";
  }
  document.body.style.fontSize = parseFloat(document.body.style.fontSize) + (multiplier * 0.2) + "em";
}

$("#dyslexia-mode").click(function(e) {
    e.preventDefault();
    return $('#article').toggleClass('dyslexia-friendly');
});