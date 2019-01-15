from django.db import models
from tinymce.models import HTMLField
from worker.models import *
from vatic.models import *
from survey.models import *

# Create your models here.

SCORES = (
    (1, 'Strong reject'),
    (2, 'Reject'),
    (3, 'Weak reject'),
    (4, 'Borderline'),
    (5, 'Weak accept'),
    (6, 'Accept'),
    (7, 'Strong accept')
)


class Comment(models.Model):
    reviewer = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name='comments')
    score = models.IntegerField(choices=SCORES, default=4)
    comment = HTMLField()
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='comments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

