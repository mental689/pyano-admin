from django.forms import ModelForm, Form
from django import forms
from employer.models import Topic, Job


class AddTopicForm(ModelForm):
    class Meta:
        model = Topic
        fields = ['name', 'description']


class AddJobForm(ModelForm):
    class Meta:
        model = Job
        fields = ['name', 'topic', 'has_keyword_search', 'has_qbe_search', 'has_survey', 'has_vatic', 'allow_invitation']