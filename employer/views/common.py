import logging

from django.shortcuts import render
from django.views import View

from common.models import SystemSetting

logger = logging.getLogger(__name__)

class IndexView(View):
    template_name = 'employer/index.html'

    def get(self, request, *args, **kwargs):
        welcome_msg = SystemSetting.objects.filter(key='site_explaination').first().value
        return render(request, template_name=self.template_name, context={'content': welcome_msg})