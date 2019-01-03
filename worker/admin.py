from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from worker.models import *
from employer.forms import *

# Register your models here.

admin.site.register(Reviewer)
admin.site.register(Annotator)
admin.site.register(SurveyAssignment)
