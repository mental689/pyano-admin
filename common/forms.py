from django import forms
from django.forms import ModelForm
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.core.validators import EmailValidator
from django.contrib.auth.password_validation import *
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from common.models import *

import logging


class AddUserForm(ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, validators=[MinimumLengthValidator(8).validate,
                                                                       UserAttributeSimilarityValidator(
                                                                           user_attributes=(
                                                                           'username', 'first_name', 'last_name',
                                                                           'email', 'affiliation',
                                                                           'location')).validate,
                                                                       CommonPasswordValidator,
                                                                       NumericPasswordValidator],
                               help_text=_('Required. Minimum length is 8. '
                                           'A common password or a password which is too similar to username, fullname or email will be rejected.'
                                           'A password must have non-numeric characters.')
                               )

    class Meta:
        model = PyanoUser
        fields = ['username', 'first_name', 'last_name', 'email', 'affiliation', 'phone', 'location', 'country_code']

    @transaction.atomic
    def save(self):
        user = super().save(commit=True)
        user.is_employer = True
        user.is_reviewer = False
        user.is_annotator = False
        user.affiliation = self.cleaned_data.get('affiliation')
        user.phone = self.cleaned_data.get('phone')
        user.location = self.cleaned_data.get('location')
        user.country_code = int(self.cleaned_data.get('country_code'))
        user.set_password(self.cleaned_data.get('password'))
        user.save()
        return user


class AddWorkerForm(UserCreationForm):

    class Meta:
        model = PyanoUser
        fields = ['username', 'first_name', 'is_reviewer', 'is_annotator',
                  'last_name', 'email', 'affiliation', 'phone', 'location', 'country_code']

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=commit)
        user.is_employer = False
        user.is_reviewer = bool(self.cleaned_data.get('is_reviewer'))
        user.is_annotator = bool(self.cleaned_data.get('is_annotator'))
        user.affiliation = self.cleaned_data.get('affiliation')
        user.phone = self.cleaned_data.get('phone')
        user.location = self.cleaned_data.get('location')
        user.country_code = int(self.cleaned_data.get('country_code'))
        try:
            user.save()
        except Exception as e:
            logging.error(e)
        return user


class LoginForm(forms.ModelForm):
    def __init__(self, request, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)

    email = forms.EmailField(widget=forms.EmailInput(), validators=[EmailValidator])
    password = forms.CharField(label='', widget=forms.PasswordInput())
    model = PyanoUser
