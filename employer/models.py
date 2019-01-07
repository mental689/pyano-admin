from django.db import models
from django.utils.translation import ugettext_lazy as _
from tinymce.models import HTMLField

from common.models import *
import survey.models as survey_models


class Employer(models.Model):
    user = models.OneToOneField(PyanoUser, on_delete=models.CASCADE, primary_key=True)

    def __str__(self):
        return self.user.get_full_name()


class Topic(models.Model):
    """
    Teacher may have to prepare the topics.
    """
    name = models.CharField(max_length=255, blank=False, null=False)
    description = models.TextField(default='', help_text='Teachers will provide a description of the topics in their labs.')
    owner = models.ForeignKey(Employer, help_text='Owner of the topic', on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Job(models.Model):
    """
    Teacher may have to prepare jobs for workers (reviewers + annotators)
    Each job will contain thre
    e sub-tasks: search (keyword- or qbe-based), survey by users and VATIC.
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
    guideline = HTMLField(blank=True, null=False, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name


class Survey(models.Model):
    survey = models.OneToOneField(survey_models.Survey, on_delete=models.CASCADE, unique=True)
    parent = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='surveys')
    guideline = HTMLField(default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta(object):
        verbose_name = _('survey')
        verbose_name_plural = _('surveys')
        unique_together = ('survey', 'parent')

    def __str__(self):
        return self.survey.name

    def latest_answer_date(self):
        """ Return the latest answer date.

        Return None is there is no response. """
        return self.survey.latest_answer_date()

    def get_absolute_url(self):
        return self.survey.get_absolute_url()


class Credit(models.Model):
    amount = models.FloatField(default=3.0) # the number of points each worker will receive for job completion.
    job = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='credits')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Video(models.Model):
    video = models.OneToOneField(survey_models.Video, on_delete=models.CASCADE)
    parent = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='videos')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('video', 'parent')

    def __str__(self):
        return self.video.vid



