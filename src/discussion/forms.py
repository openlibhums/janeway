from django import forms

from discussion import models


class ThreadForm(forms.ModelForm):
    class Meta:
        model = models.Thread
        fields = (
            'subject',
        )

    def __init__(self, *args, **kwargs):
        self.object = kwargs.pop('object')
        self.object_type = kwargs.pop('object_type')
        self.owner = kwargs.pop('owner')
        super(ThreadForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        thread = super(ThreadForm, self).save(commit=False)

        if self.object_type == 'article':
            thread.article = self.object
        else:
            thread.preprint = self.object

        thread.owner = self.owner

        if commit:
            thread.save()

        return thread
