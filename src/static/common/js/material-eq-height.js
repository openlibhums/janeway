$(document).ready(function(){

    var tallest_div = 0;
        $('.eq-height-row .eq-height-col').each(function(){
                if($(this).height() > tallest_div){
                tallest_div = $(this).height();
        }
    });
    $('.eq-height-row .eq-height-col').height(tallest_div - 20);

});