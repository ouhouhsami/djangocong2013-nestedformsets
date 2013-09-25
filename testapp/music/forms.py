from django.forms import ModelForm
from .models import Band


class BandForm(ModelForm):
	class Meta:
		model = Band
		exclude = ('members', )