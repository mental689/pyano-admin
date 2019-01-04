from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.validators import EmailValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import *
# Create your models here.


class PyanoUserManager(UserManager):
    pass


class PyanoUser(AbstractUser):
    # email is required for employer
    email = models.EmailField(_('email address'), help_text=_('Required. Must be a valid email.'), blank=False, null=False, unique=True, validators=[EmailValidator])
    # password is required
    password = models.CharField(_('password'),
                                help_text=_('Required. Minimum length is 8. '
                                            'A common password or a password which is too similar to username, fullname or email will be rejected.'
                                            'A password must have non-numeric characters.'),
                                max_length=256, blank=False, null=False,
                                validators=[MinimumLengthValidator(8).validate,
                                            UserAttributeSimilarityValidator(
                                                user_attributes=(
                                                    'username', 'first_name', 'last_name',
                                                    'email', 'affiliation',
                                                    'location')).validate,
                                            CommonPasswordValidator,
                                            NumericPasswordValidator]
                                )
    # user types
    is_employer = models.BooleanField(default=False)
    is_reviewer = models.BooleanField(default=False)
    is_annotator = models.BooleanField(default=False)
    # other information
    affiliation = models.CharField(max_length=255, help_text=_('Affiliation'), blank=True)
    phone = models.CharField(max_length=255, help_text=_('Phone number'), blank=True)
    location = models.CharField(max_length=255, help_text=_('location'), blank=True)
    country_code = models.IntegerField(help_text=_('country code'), blank=False, default=1)


class SystemSetting(models.Model):
    key = models.CharField(max_length=255, default='youtube_dev_key', unique=True)
    value = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


