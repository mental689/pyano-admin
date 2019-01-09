import logging

from django.conf import settings
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.views import View

from employer.models import Job

logger = logging.getLogger(__name__)


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
                    surveys = job.surveys.annotate(credit=Sum('credits__amount')).all()
                    context['surveys'] = surveys
                if job.has_vatic:
                    vatics = job.groups.all()
                    context['vatics'] = vatics
            except Exception as e:
                logger.debug(e)
                context['error'] = 'Internal Server Error'
        else:
            context['error'] = 'No ID.'
        return render(request, template_name=self.template_name, context=context)