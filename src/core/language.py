from parler.forms import TranslatableModelForm


class JanewayTranslatableModelForm(TranslatableModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self._translated_fields:
            self.fields[field].widget.attrs = {
                'class': 'translatable',
            }

    def translated_fields(self):
        return self._translated_fields
