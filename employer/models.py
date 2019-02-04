from django.db import models
from django.utils.translation import ugettext_lazy as _
from tinymce.models import HTMLField
from versions.models import Versionable
from versions.fields import VersionedForeignKey

from common.models import PyanoUser
import survey.models as survey_models
from worker.models import Annotator


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
    owner = models.ForeignKey(Employer, help_text='Owner of the topic', on_delete=models.CASCADE, null=True, related_name='topics')
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


class CollaborationProject(models.Model):
    project = models.OneToOneField(Job, related_name='collaboration_project', unique=False, on_delete=models.CASCADE)
    owner = models.ForeignKey(Employer, help_text='Collaborator of the project', on_delete=models.CASCADE, null=True,
                              related_name='collaboration_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{} - {}'.format(self.project.name, self.owner.user.username)

    class Meta:
        unique_together = ('project', 'owner')


class Survey(models.Model):
    survey = models.OneToOneField(survey_models.Survey, on_delete=models.CASCADE, unique=True, related_name='pyano_survey')
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
    video = models.OneToOneField(survey_models.Video, on_delete=models.CASCADE, related_name='pyano_video')
    parent = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='videos')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('video', 'parent')

    def __str__(self):
        return self.video.vid

    def get_absolute_url(self):
        return '/worker/survey/review/1/{}/'.format(self.video.id)


class Dataset(Versionable):
    job = VersionedForeignKey(Job, on_delete=models.CASCADE, related_name='datasets')
    name = models.CharField(max_length=255, default='')
    description = models.TextField(default='')
    current_json = models.TextField(default='')


class InformedConsent(models.Model):
    name = models.CharField(max_length=255, help_text=_('Name of the consent form'))
    parent = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='informent_consents')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return 'Informed consent form {} - {}'.format(self.parent.id, self.id)


class ConsentTerm(models.Model):
    text = models.TextField(help_text=_('A term to add to the consent forms'))
    required = models.BooleanField(default=True,
                                   help_text=_('Whether if this term is required or is just an optional warning. If required, users must check for it.'))
    parent = models.ForeignKey(InformedConsent, on_delete=models.CASCADE, related_name='terms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text


class ConsentConfirmationStatus(models.Model):
    worker = models.ForeignKey(PyanoUser, on_delete=models.CASCADE, related_name='consent_agreements')
    consent = models.ForeignKey(InformedConsent, on_delete=models.CASCADE, related_name='consent_agreements')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return 'User {} agreed with consent {}'.format(self.worker.id, self.consent.id)

    class Meta:
        unique_together = ('worker', 'consent')


class BadWorker(models.Model):
    worker = models.ForeignKey(PyanoUser, on_delete=models.CASCADE, related_name='bad_reputations')
    bad_at = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="bad_workers")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return 'Worker {} was marked as a bad worker at project {}'.format(self.worker.id, self.bad_at_id)

    class Meta:
        unique_together = ('worker', 'bad_at')




