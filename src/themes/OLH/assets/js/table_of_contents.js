$(document).ready(function () {

    if (!$("#toc")) {
        return;
    }

    var newLine, link, title, linkid, toc, iter, js;

    iter = 0;
    toc = '';

    $("#main_article h2, #main_article h3").each(function () {
        link = $(this);

        var clonedLink = link.clone();
        clonedLink.find('a').each(function () {
            if (!$(this).text().trim()) {
                $(this).remove();
            } else {
                $(this).contents().unwrap();
            }
        });

        title = clonedLink.html();

        if (!link.attr("id")) {
            link.attr('id', 'heading' + iter.toString());
        }

        linkid = "#" + link.attr("id");

        js = "$('html, body').animate({scrollTop: $( $.attr(this, 'href') ).offset().top - 35}, 500);return false;";

        newLine = "<li class=\"sidebar-item\"><a href='" + linkid + "' onclick=\"" + js + "\">" + title + "</a></li>";

        toc += newLine;
        iter++;
    });

    if (iter === 0) {
        $("#toc-section").remove();
    } else {
        $("#toc").append(toc);
    }
});
