from django import forms
from tinymce.widgets import TinyMCE

from core import files
from file_editor import widgets


class GalleyEditForm(forms.Form):
    galley_content = forms.CharField()

    def __init__(self, *args, **kwargs):
        self.galley = kwargs.pop('galley')
        super(GalleyEditForm, self).__init__(*args, **kwargs)
        if self.galley.file.mime_type in files.HTML_MIMETYPES:
            self.fields['galley_content'].widget = TinyMCE(
                mce_attrs={"height": "700"},
            )
        else:
            self.fields['galley_content'].widget = widgets.CodeEditor()

        self.fields['galley_content'].initial = self.galley.file.get_file(
            self.galley.article,
        )

    def save(self):
        galley_content = self.cleaned_data['galley_content']
        with open(
                self.galley.file.get_file_path(self.galley.article),
                'w'
        ) as galley_file:
            galley_file.write(galley_content)
            galley_file.close()
