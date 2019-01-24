import logging

from django.conf import settings
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import redirect, render
from django.utils.timezone import now, timedelta
from django.views import View

from common.models import PyanoUser
from employer.forms import AddJobForm
from employer.models import Job, Topic
from search.models import KeywordSearch, QBESearch
from vatic.models import Solution, Path, Box
from worker.models import Annotator

logger = logging.getLogger(__name__)
import datetime


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
        except Exception as e:
            logging.debug(e)
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
                                       daterange(start_date=now() - timedelta(+30), end_date=now() + timedelta(+1))]
                tasks['ks_by_keywords'] = tasks['ks'].values('keyword').annotate(c=Count('id')).values('keyword',
                                                                                                       'c').order_by(
                    '-c')[:5]
            if job.has_qbe_search:
                tasks['qbe'] = QBESearch.objects.filter(parent=job)
            if job.has_survey:
                tasks['survey'] = job.surveys.annotate(credit=Sum('credits__amount')).all()
                answers = []
                for survey in tasks['survey']:
                    answer = survey.survey.responses.annotate(day=TruncDate('created')).values('day').annotate(
                        c=Count('id')).values('day', 'c')
                    data = {}
                    for k in answer:
                        data[k['day']] = k['c']
                    data2 = [{'day': d.strftime('%Y-%m-%d'), 'c': data[d] if d in data else 0} for d in
                             daterange(start_date=now() - timedelta(+30), end_date=now() + timedelta(+1))]
                    answers.append({'id': survey.id, 'data': data2})
                tasks['answers_by_date'] = answers
                users = PyanoUser.objects.all().annotate(c=Count('responses')).values('username', 'c').order_by('-c')[
                        :5]

                tasks['users_surveys'] = users
            if job.has_vatic:
                tasks['vatics'] = job.groups.annotate(num_solutions=Count('jobs__solutions')).all()
                solutions = []
                paths = []
                boxes = []
                for group in tasks['vatics']:
                    vatic_solution_by_date = Solution.objects.filter(
                        job__group=group,
                        created_at__gte=now() - timedelta(+30),  # last 30 days
                    ).annotate(day=TruncDate('created_at')).values('day').annotate(c=Count('day')).values('day', 'c')
                    data = {}
                    for k in vatic_solution_by_date:
                        data[k['day']] = k['c']
                        data2 = [{'day': d.strftime('%Y-%m-%d'), 'c': data[d] if d in data else 0}
                                 for d in
                                 daterange(start_date=now() - timedelta(+30),
                                           end_date=now() + timedelta(+1))]
                    solutions.append({'id': group.id, 'data': data2, 'title': group.title})

                    vatic_path_by_date = Path.objects.filter(
                        solution__job__group=group,
                        created_at__gte=now() - timedelta(+30)
                    ).annotate(day=TruncDate('created_at')).values('day').annotate(c=Count('day')).values('day', 'c')
                    data = {}
                    for k in vatic_path_by_date:
                        data[k['day']] = k['c']
                        data2 = [{'day': d.strftime('%Y-%m-%d'), 'c': data[d] if d in data else 0}
                                 for d in
                                 daterange(start_date=now() - timedelta(+30),
                                           end_date=now() + timedelta(+1))]
                    paths.append({'id': group.id, 'data': data2, 'title': group.title})

                    vatic_box_by_date = Box.objects.filter(
                        path__solution__job__group=group,
                        created_at__gte=now() - timedelta(+30)
                    ).annotate(day=TruncDate('created_at')).values('day').annotate(c=Count('day')).values('day', 'c')
                    data = {}
                    for k in vatic_box_by_date:
                        data[k['day']] = k['c']
                        data2 = [{'day': d.strftime('%Y-%m-%d'), 'c': data[d] if d in data else 0}
                                 for d in
                                 daterange(start_date=now() - timedelta(+30),
                                           end_date=now() + timedelta(+1))]
                    boxes.append({'id': group.id, 'data': data2, 'title': group.title})
                tasks['vatic_solution_by_date'] = solutions
                tasks['vatic_path_by_date'] = paths
                tasks['vatic_box_by_date'] = boxes

                # Contributions of participants
                users = Annotator.objects.all().annotate(c=Count('solutions')).values('user__username', 'c').order_by('-c')[
                        :5]
                users_2 = Annotator.objects.all().annotate(c=Count('solutions__paths')).values('user__username', 'c').order_by(
                    '-c')[:5]
                users_3 = Annotator.objects.all().annotate(c=Count('solutions__paths__boxes')).values('user__username',
                                                                                               'c').order_by(
                    '-c')[:5]
                tasks['vatics_users'] = users
                tasks['vatics_users_paths'] = users_2
                tasks['vatics_users_boxes'] = users_3

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
        except Exception as e:
            logger.debug(e)
            context['error'] = 'Internal Server Error while saving topic'
            render(request, template_name=self.template_name, context=context)
        return redirect(to='/job/list/')
