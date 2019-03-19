from django.forms import ClearableFileInput


class JanewayFileInput(ClearableFileInput):
    template_name = 'admin/core/widgets/janeway_clearable_file.html'
