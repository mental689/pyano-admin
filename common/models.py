from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.validators import EmailValidator, RegexValidator
from django.utils.timezone import now, timedelta
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import *
from django_countries.fields import CountryField
from tinymce.models import HTMLField
# Create your models here.


class PyanoUserManager(UserManager):
    pass


class PyanoUser(AbstractUser):
    first_name = models.CharField(_('first name'), max_length=30, blank=False, null=False)
    last_name = models.CharField(_('last name'), max_length=150, blank=False, null=False)
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
    is_employer = models.BooleanField(default=False, help_text=_('Whether to apply as a project owner.'))
    is_reviewer = models.BooleanField(default=False, help_text=_('Whether to apply as a reviewer.'))
    is_annotator = models.BooleanField(default=False, help_text=_('Whether to apply as an annotator.'))
    # other information
    affiliation = models.CharField(max_length=255, help_text=_('Optional. Affiliation'), blank=True)
    SEX = (
        (1, 'Male'),
        (2, 'Female'),
        (3, 'None of above'),
    )
    sex = models.IntegerField(choices=SEX, blank=False, default=3, help_text=_('Sex'))
    # JOB fields from https://career.berkeley.edu/InfoLab/CareerFields
    CARRER_FIELDS = (
        (1, 'Architecture, Planning & Environmental Design'),
        (2, 'Arts,Culture & Entertainment'),
        (3, 'Business'),
        (4, 'Communications'),
        (5, 'Education'),
        (6, 'Engineering & Computer Science'),
        (7, 'Environment'),
        (8, 'Government'),
        (9, 'Health & Medicine'),
        (10, 'International'),
        (11, 'Law & Public Policy'),
        (12, 'Social Impact/Community Service'),
        (13, 'Sciences-Biological & Physical'),
        (14, 'Others')
    )
    job_name = models.IntegerField(choices=CARRER_FIELDS, blank=False, null=False, default=5,
                                   help_text=_('Required. See https://career.berkeley.edu/InfoLab/CareerFields to choose the right field.'))
    phone = models.CharField(max_length=255, help_text=_('Optional. Phone number'), blank=True)
    location = models.CharField(max_length=255, help_text=_('Optional. Location'), blank=True)
    # country_code = models.IntegerField(help_text=_('country code'), blank=False, default=1)
    country = CountryField(blank=False, default='US', help_text=_('Required. Country'), null=False)
    birthday = models.DateField(null=True, help_text=_('Required. Birthday'))

    def get_age(self):
        if self.birthday is not None:
            return int((now().date()-self.birthday).days/365)
        else:
            return "-"
        
    def get_full_name(self):
        """
        Override the get_full_name() function to ensure that only project owners and staffs can display their full names.
        Basically, workers will not display their full names anywhere in this website.
        :return:
        """
        if self.is_reviewer:
            return "Reviewer {}".format(self.id) # Reviewer name is not revealed.
        elif self.is_annotator:
            return "Annotator {}".format(self.id) # Annotator name is masked, too.
        else:
            return super(PyanoUser, self).get_full_name()


class SystemSetting(models.Model):
    key = models.CharField(max_length=255, default='youtube_dev_key', unique=True)
    value = HTMLField(default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key


