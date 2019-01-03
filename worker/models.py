from django.db import models

from common.models import *
from employer.models import *
from survey.models import Video, Survey

# Create your models here.


class Reviewer(models.Model):
    user = models.OneToOneField(PyanoUser, on_delete=models.CASCADE, primary_key=True)


class Annotator(models.Model):
    user = models.OneToOneField(PyanoUser, on_delete=models.CASCADE, primary_key=True)


class SurveyAssignment(models.Model):
    annotator = models.ForeignKey(Annotator, on_delete=models.CASCADE)
    job = models.ForeignKey(Survey, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    uuid = models.CharField(max_length=255, null=True, unique=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('annotator', 'job', 'video')


