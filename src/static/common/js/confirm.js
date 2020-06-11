$(document).ready(function(){
  $(".del").click(function(){
    if (!confirm("Are you sure you want to delete this? You will not be able to recover any deleted data or files.")){
      return false;
    }
  });
});