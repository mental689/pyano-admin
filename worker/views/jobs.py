from django.views import View
from django.shortcuts import redirect, render
from django.conf import settings
from django.db.models import Count
from employer.forms import AddJobForm
from employer.models import Job
from employer.models import Survey as PyanoSurvey
from search.models import KeywordSearch, QBESearch

import logging


class ListJobView(View):
    template_name = 'worker/job/list.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            redirect(to='{}/login/?next=/worker/jobs/'.format(settings.LOGIN_URL))
        jobs = Job.objects.filter(is_completed=False)
        return render(request, template_name=self.template_name, context={'jobs': jobs})


class JobDetailView(View):
    template_name = 'worker/job/detail.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            redirect(to='{}/login/?next=/worker/job/?id={}'.format(settings.LOGIN_URL, request.GET.get('id', None)))
        id = request.GET.get('id', None)
        context = {}
        if id is not None:
            try:
                job = Job.objects.filter(id=id).first()
                if job is None:
                    context['error'] = 'Project is not found.'
                context['job'] = job
                if job.has_survey:
                    surveys = job.surveys.annotate(num_videos=Count('parent__videos')).all()
                    context['surveys'] = surveys
            except Exception as e:
                context['error'] = 'Internal Server Error'
        else:
            context['error'] = 'No ID.'
        return render(request, template_name=self.template_name, context=context)