from django.forms import ClearableFileInput, CheckboxSelectMultiple


class JanewayFileInput(ClearableFileInput):
    template_name = 'admin/core/widgets/janeway_clearable_file.html'

class TableMultiSelectUser(CheckboxSelectMultiple):
    template_name = 'admin/core/widgets/multi_checkbox_user_table.html'
