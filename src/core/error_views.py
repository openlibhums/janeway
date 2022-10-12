from django.shortcuts import render


def handler404(request, *args, **argv):
    template = '404.html'
    context = {}
    return render(
        request,
        template,
        context,
        status=404,
    )


def handler500(request, *args, **argv):
    response = render(
        None,
        '500.html',
    )
    response.status_code = 404
    return response
