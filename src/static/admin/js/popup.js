function popitup(url) {
	newwindow = window.open(url,'name','height=900,width=800');
	if (window.focus) {newwindow.focus()}
	return false;
}