from django.db import models

from common.models import *


class Employer(models.Model):
    user = models.OneToOneField(PyanoUser, on_delete=models.CASCADE, primary_key=True)


class Topic(models.Model):
    """
    Teacher may have to prepare the topics.
    """
    name = models.CharField(max_length=255, blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Job(models.Model):
    """
    Teacher may have to prepare jobs for workers (reviewers + annotators)
    Each job will contain three sub-tasks: search (keyword- or qbe-based), survey by users and VATIC.
    Teacher may be allowed to invite outsiders to review workers' jobs.
    """
    name = models.CharField(max_length=255, blank=False, null=False)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='jobs')
    has_keyword_search = models.BooleanField(default=True)
    has_qbe_search = models.BooleanField(default=False)
    has_survey = models.BooleanField(default=True)
    allow_invitation = models.BooleanField(default=False, help_text='Allow teacher to invite outsiders to review the jobs')
    has_vatic = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Credit(models.Model):
    amount = models.FloatField(default=3.0) # the number of points each worker will receive for job completion.
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='credits')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
