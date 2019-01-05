from django.views import View
from django.shortcuts import redirect, render
from django.conf import settings
from employer.forms import AddTopicForm
from common.models import SystemSetting

import logging


class IndexView(View):
    template_name = 'employer/index.html'

    def get(self, request, *args, **kwargs):
        welcome_msg = SystemSetting.objects.filter(key='site_explaination').first().value
        return render(request, template_name=self.template_name, context={'content': welcome_msg})