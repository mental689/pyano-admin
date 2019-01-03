from django.views import View
from django.shortcuts import redirect, render
from django.conf import settings
from employer.forms import AddJobForm
from employer.models import Job

import logging


class AddJobView(View):
    template_name = 'employer/job/add.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            redirect(to='{}/login/?next=/job/add/'.format(settings.LOGIN_URL))
        form = AddJobForm()
        return render(request, template_name=self.template_name, context={'form': form})

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            redirect(to='{}/login/?next=/job/add/'.format(settings.LOGIN_URL))
        context = {}
        try:
            form = AddJobForm(request.POST)
            form.Meta.model.is_completed = False
            form.save()
            context['status'] = 200
        except Exception as e:
            logging.error(e)
            context['status'] = 400
            context['error'] = 'Internal Server Error'
            render(request, template_name=self.template_name, context=context)
        return redirect(to='/job/list/')


class ListJobView(View):
    template_name = 'employer/job/list.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            redirect(to='{}/login/?next=/topic/list/'.format(settings.LOGIN_URL))
        jobs = Job.objects.filter(topic__owner__user=request.user)
        return render(request, template_name=self.template_name, context={'jobs': jobs})