from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser, UserManager

# Create your models here.


class PyanoUserManager(UserManager):
    pass


class PyanoUser(AbstractUser):
    # email is required for employer
    email = models.EmailField(_('email address'), blank=False, null=False, unique=True)
    # user types
    is_employer = models.BooleanField(default=False)
    is_reviewer = models.BooleanField(default=False)
    is_annotator = models.BooleanField(default=False)
    # other information
    affiliation = models.CharField(max_length=255, help_text=_('Affiliation'), blank=True)
    phone = models.CharField(max_length=255, help_text=_('Phone number'), blank=True)
    location = models.CharField(max_length=255, help_text=_('location'), blank=True)
    country_code = models.IntegerField(help_text=_('country code'), blank=False, default=1)


