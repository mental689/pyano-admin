from django.views import View
from django.shortcuts import redirect, render
from django.conf import settings
from employer.forms import AddJobForm
from employer.models import Job, Topic
from search.models import KeywordSearch, QBESearch
from survey.models import Survey

import logging


class AddJobView(View):
    template_name = 'employer/job/add.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(to='{}/login/?next=/job/add/'.format(settings.LOGIN_URL))
        if not request.user.is_employer:
            return redirect(to="/")
        form = AddJobForm()
        return render(request, template_name=self.template_name, context={'form': form})

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(to='{}/login/?next=/job/add/'.format(settings.LOGIN_URL))
        if not request.user.is_employer:
            return redirect(to="/")
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
            return redirect(to='{}/login/?next=/topic/list/'.format(settings.LOGIN_URL))
        if not request.user.is_employer:
            return redirect(to="/")
        jobs = Job.objects.filter(topic__owner__user=request.user)
        return render(request, template_name=self.template_name, context={'jobs': jobs})


class DetailJobView(View):
    template_name ='employer/job/detail.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(to='{}/login/?next=/job/list/'.format(settings.LOGIN_URL))
        if not request.user.is_employer:
            return redirect(to="/")
        id = request.GET.get('id', None)
        job = None
        if id is not None:
            job = Job.objects.filter(id=id).first()
            tasks = {}
            if job.has_keyword_search:
                tasks['ks'] = KeywordSearch.objects.filter(parent=job)
            if job.has_qbe_search:
                tasks['qbe'] = QBESearch.objects.filter(parent=job)
            if job.has_survey:
                tasks['survey'] = job.surveys.all()
        return render(request, template_name=self.template_name, context={'job': job, 'tasks': tasks})


class ChangeJobView(View):
    template_name = 'employer/job/change.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(to='{}/login/?next=/job/change/?id={}'.format(settings.LOGIN_URL, request.GET.get('id', None)))
        if not request.user.is_employer:
            return redirect(to="/")
        id = request.GET.get('id', None)
        if id is not None:
            job = Job.objects.filter(id=id).first()
        else:
            job = None
        topics = Topic.objects.all()
        return render(request, template_name=self.template_name, context={'id': id, 'job': job, 'topics': topics})

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(to='{}/login/?next=/'.format(settings.LOGIN_URL))
        if not request.user.is_employer:
            return redirect(to="/")
        context = {}
        try:
            id = request.POST.get('id', None)
            job = Job.objects.filter(id=id).first()
            name = request.POST.get('name', None)
            if name is not None:
                job.name = name
            topic = Topic.objects.filter(id=request.POST.get('id', None)).first()
            if topic is not None:
                job.topic = topic
            job.has_keyword_search = bool(request.POST.get('ks', True))
            job.has_qbe_search = bool(request.POST.get('qbe', False))
            job.has_survey = bool(request.POST.get('survey', True))
            job.has_vatic = bool(request.POST.get('vatic', True))
            job.allow_invitation = bool(request.POST.get('invitation', True))
            job.guideline = request.POST.get('guideline', '')
            job.save()
            context['status'] = 200
        except Exception as e:
            logging.error(e)
            context['status'] = 400
            context['error'] = 'Internal Server Error while saving topic'
            render(request, template_name=self.template_name, context=context)
        return redirect(to='/job/list/')