
def get_display_modal(request):
    """
    Determins which file modal should be displayed when there is a form error.
    :param request: HttpRequest
    :return: string
    """
    if 'manuscript' in request.POST:
        return 'manuscript'
    elif 'data' in request.POST:
        return 'data'
