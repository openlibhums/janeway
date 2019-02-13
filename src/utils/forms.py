from django.forms import ModelForm

class FakeModelForm(ModelForm):
	""" A form that can't be saved
	
	Usefull for rendering a sample form
	"""

	def __init__(self, *args, disable_fields=False, **kwargs):
		super().__init__(*args, **kwargs)
		self.disable_fields = disable_fields
		if disable_fields is True:
			for field in self.fields:
				self.fields[field].widget.attrs["readonly"] = True

	def save(self, *args, **kwargs):
		raise NotImplementedError("FakeModelForm can't be saved")

	def clean(self, *args, **kwargs):
		if self.disable_fields is True:
			raise NotImplementedError(
				"FakeModelForm can't be cleaned: disable_fields is True",
			)
		return super().clean(*args, **kwargs)

