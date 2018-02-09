function popitup(url) {
	newwindow = window.open(url,'name','height=800,width=800');
	if (window.focus) {newwindow.focus()}
	return false;
}