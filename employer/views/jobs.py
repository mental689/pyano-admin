from django.views import View
from django.shortcuts import redirect, render
from django.conf import settings
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils.timezone import now, timedelta
from employer.forms import AddJobForm
from employer.models import Job, Topic
from common.models import PyanoUser
from search.models import KeywordSearch, QBESearch
from survey.models import Survey

import logging, os
from time import time
import datetime
LOG_FILE = "./log/employer_jobs_{}.log".format(time())
if not os.path.exists("./log"):
    os.makedirs("./log")
formatter = logging.Formatter(fmt="[%(asctime)s]\t[%(levelname)s]\t[%(message)s]")
logger = logging.getLogger("youtube")
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(fmt=formatter)
logger.addHandler(hdlr=file_handler)


def daterange(start_date, end_date):
    """
    Generate an iterator of dates between the two given dates.
    taken from http://stackoverflow.com/questions/1060279/
    """
    for n in range(int((end_date - start_date).days)):
        yield (start_date + datetime.timedelta(n)).date()


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
    template_name = 'employer/job/detail.html'

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
                ks_by_date = tasks['ks'].annotate(day=TruncDate('created_at')).values('day').annotate(
                    c=Count('id')).values('day', 'c')
                data = {}
                for k in ks_by_date:
                    data[k['day']] = k['c']
                tasks['ks_by_date'] = [{'day': d.strftime('%Y-%m-%d'), 'c': data[d] if d in data else 0} for d in
                                       daterange(start_date=now()-timedelta(+30), end_date=now()+timedelta(+1))]
                tasks['ks_by_keywords'] = tasks['ks'].values('keyword').annotate(c=Count('id')).values('keyword',
                                                                                                       'c').order_by(
                    '-c')[:5]
            if job.has_qbe_search:
                tasks['qbe'] = QBESearch.objects.filter(parent=job)
            if job.has_survey:
                tasks['survey'] = job.surveys.annotate(credit=Sum('credits__amount')).all()
                answers = []
                for survey in tasks['survey']:
                    answer = survey.survey.responses.annotate(day=TruncDate('created')).values('day').annotate(c=Count('id')).values('day', 'c')
                    data = {}
                    for k in answer:
                        data[k['day']] = k['c']
                    data2 = [{'day': d.strftime('%Y-%m-%d'), 'c': data[d] if d in data else 0} for d in daterange(start_date=now()-timedelta(+30), end_date=now()+timedelta(+1))]
                    answers.append({'id': survey.id, 'data': data2})
                tasks['answers_by_date'] = answers
                users = PyanoUser.objects.all().annotate(c=Count('responses')).values('username', 'c').order_by('-c')[:5]

                tasks['users_surveys'] = users
        return render(request, template_name=self.template_name, context={'job': job, 'tasks': tasks})


class ChangeJobView(View):
    template_name = 'employer/job/change.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(
                to='{}/login/?next=/job/change/?id={}'.format(settings.LOGIN_URL, request.GET.get('id', None)))
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
