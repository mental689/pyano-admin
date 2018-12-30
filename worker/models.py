from django.db import models

from common.models import *
from employer.models import *
from survey.models import Video

# Create your models here.


class Reviewer(models.Model):
    user = models.OneToOneField(PyanoUser, on_delete=models.CASCADE, primary_key=True)


class Annotator(models.Model):
    user = models.OneToOneField(PyanoUser, on_delete=models.CASCADE, primary_key=True)


class AnnotatorAssignment(models.Model):
    annotator = models.ForeignKey(Annotator, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


