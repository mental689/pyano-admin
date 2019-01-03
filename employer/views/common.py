from django.views import View
from django.shortcuts import redirect, render
from django.conf import settings
from employer.forms import AddTopicForm

import logging


class IndexView(View):
    template_name = 'employer/index.html'

    def get(self, request, *args, **kwargs):
        return render(request, template_name=self.template_name, context={})