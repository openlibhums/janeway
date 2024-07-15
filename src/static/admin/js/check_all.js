// Deprecated. Use select_all.html instead.

 $("#checkall").click(function () {
     $('input:checkbox').not(this).prop('checked', this.checked);
 });
