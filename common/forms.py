from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.db import transaction

from common.models import *


class PyanoUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        model = PyanoUser
        fields = ('username', 'email')

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.is_employer = False
        user.is_reviewer = True
        user.is_annotator = True
        user.save()
        return user


class PyanoUserChangeForm(UserChangeForm):

    class Meta:
        model = PyanoUser
        fields = UserChangeForm.Meta.fields


class LoginForm(forms.ModelForm):
    def __init__(self, request, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
    email = forms.EmailField(widget=forms.EmailInput())
    password = forms.CharField(label='', widget=forms.PasswordInput())
    model = PyanoUser