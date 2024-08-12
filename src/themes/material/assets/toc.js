$( document ).ready(function() {

    if (!$("#toc")) {
        return;
    }

    var newLine, link, title, linkid, toc, iter, js;

    iter = 0;
    toc = '';

    $("#main_article h2").each(function () {

        link = $(this);
        link.find('a').contents().unwrap();
        title = link.html();

        if (!link.attr("id")) {
            link.attr('id', 'heading' + iter.toString());
            link.addClass("section scrollspy")
        }

        linkid = "#" + link.attr("id");

        js = "$('html, body').animate({scrollTop: $( $.attr(this, 'href') ).offset().top - 35}, 500);return false;";

        newLine = "<li><a href='" + linkid + "' onclick=\"" + js + "\">" + title + "</a></li>";

        toc += newLine;
        iter++;

    });

    if(iter==0){
        $("#toc-section").remove();
    }
    else{
        $("#toc").append(toc);
    }
});
