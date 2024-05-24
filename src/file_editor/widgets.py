from django import forms


class CodeEditor(forms.Textarea):
    def __init__(self, *args, **kwargs):
        super(CodeEditor, self).__init__(*args, **kwargs)
        self.attrs['class'] = 'code-editor'

    class Media:
        css = {
            'all': (
                'https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.62.3/codemirror.min.css',
                'https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.62.3/theme/nord.min.css',
                'https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.62.3/theme/solarized.min.css',
            )
        }
        js = (
            'https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.62.3/codemirror.min.js',
            'https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.62.3/mode/css/css.min.js',
        )
