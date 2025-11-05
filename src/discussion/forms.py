from django import forms

from discussion import models


class ThreadForm(forms.ModelForm):
    class Meta:
        model = models.Thread
        fields = (
            "subject",
        )

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        self.object = kwargs.pop("object")
        self.object_type = kwargs.pop("object_type")
        self.owner = kwargs.pop("owner")
        super(ThreadForm, self).__init__(*args, **kwargs)

        # Attach FK + owner BEFORE validation so model.clean() passes
        if self.object_type == "article":
            self.instance.article = self.object
            self.instance.preprint = None
        else:
            self.instance.preprint = self.object
            self.instance.article = None

        self.instance.owner = self.owner

    def save(
        self,
        commit=True,
    ):
        thread = super(ThreadForm, self).save(
            commit=False,
        )
        # Instance already has article/preprint/owner set in __init__
        if commit:
            thread.save()
        return thread