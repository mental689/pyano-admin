from django.forms import ModelForm, Form, inlineformset_factory
from django import forms
from django.db import transaction
from employer.models import Topic, Job, PyanoUser
from survey.models import Survey, Question


class AddTopicForm(ModelForm):
    class Meta:
        model = Topic
        fields = ['name', 'description']


class AddJobForm(ModelForm):
    class Meta:
        model = Job
        fields = ['name', 'topic', 'has_keyword_search', 'has_qbe_search', 'has_survey', 'has_vatic', 'allow_invitation', 'guideline']


class AddSurveyForm(ModelForm):
    class Meta:
        model = Survey
        fields = ['name', 'need_logged_user', 'display_by_question', 'randomize_questions']

    @transaction.atomic
    def save(self):
        self.instance.is_published = True
        self.instance.description = ''
        survey = super().save(commit=True)
        return survey
