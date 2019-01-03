from django.db import models
from common.models import PyanoUser
from employer.models import Job
from survey.models import Video
# Create your models here.


class KeywordSearch(models.Model):
    parent = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='searchTasks')
    keyword = models.CharField(max_length=255, blank=False, null=False)
    outcome = models.TextField(blank=True, null=True)
    worker = models.ForeignKey(PyanoUser, on_delete=models.CASCADE, related_name='searches')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class QBESearch(models.Model):
    parent = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='qbesearchTasks')
    query = models.ForeignKey(Video, blank=False, null=False, on_delete=models.CASCADE)
    outcome = models.TextField(blank=True, null=True)
    worker = models.ForeignKey(PyanoUser, on_delete=models.CASCADE, related_name='qbesearches')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)