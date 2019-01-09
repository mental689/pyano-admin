from django import forms
from vatic.models import JobGroup


class AddJobGroupForm(forms.ModelForm):
    class Meta:
        model = JobGroup
        fields = ('title', 'description', 'cost', 'duration', 'height', 'keywords', 'parent')