from django import forms


class EditorSectionChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.editor_display_name()
