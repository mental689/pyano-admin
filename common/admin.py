from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from common.models import *
from common.forms import *

# Register your models here.


class PyanoAdmin(UserAdmin):
    model = PyanoUser


admin.site.register(PyanoUser, PyanoAdmin)
admin.site.register(SystemSetting)