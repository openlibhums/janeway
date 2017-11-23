 $("#checkall").click(function () {
     $('input:checkbox').not(this).prop('checked', this.checked);
 });