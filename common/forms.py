import logging

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

from common.models import *


class AddUserForm(UserCreationForm):

    class Meta:
        model = PyanoUser
        fields = ['username', 'first_name', 'last_name', 'email', 'sex', 'affiliation',
                  'phone', 'location', 'country', 'job_name', 'birthday']
        widgets = {
            'birthday': forms.DateInput(attrs={'class': 'datepicker'}),
        }

    @transaction.atomic
    def save(self):
        user = super().save(commit=True)
        user.is_employer = True
        user.is_reviewer = False
        user.is_annotator = False
        user.affiliation = self.cleaned_data.get('affiliation')
        user.phone = self.cleaned_data.get('phone')
        user.location = self.cleaned_data.get('location')
        user.country = self.cleaned_data.get('country')
        user.job_name = int(self.cleaned_data.get('job_name'))
        user.birthday = self.cleaned_data.get('birthday')
        user.save()
        return user


class AddWorkerForm(UserCreationForm):

    class Meta:
        model = PyanoUser
        fields = ['username', 'email', 'first_name', 'last_name', 'sex',
                  'birthday','is_reviewer', 'is_annotator', 'job_name',
                  'affiliation', 'phone', 'country', 'location']
        widgets = {
            'birthday': forms.DateInput(attrs={'class': 'datepicker'}),
        }

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=commit)
        user.is_employer = False
        user.is_reviewer = bool(self.cleaned_data.get('is_reviewer'))
        user.is_annotator = bool(self.cleaned_data.get('is_annotator'))
        if not (user.is_annotator or user.is_reviewer):
            raise ValidationError('Users must choose one of two jobs: reviewer or annotator.')
        user.affiliation = self.cleaned_data.get('affiliation')
        user.phone = self.cleaned_data.get('phone')
        user.location = self.cleaned_data.get('location')
        user.country = self.cleaned_data.get('country')
        user.job_name = int(self.cleaned_data.get('job_name'))
        user.birthday = self.cleaned_data.get('birthday')
        try:
            user.save()
        except Exception as e:
            raise Exception(e)
        return user


class LoginForm(forms.ModelForm):
    def __init__(self, request, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)

    email = forms.EmailField(widget=forms.EmailInput(), validators=[EmailValidator])
    password = forms.CharField(label='', widget=forms.PasswordInput())
    model = PyanoUser
