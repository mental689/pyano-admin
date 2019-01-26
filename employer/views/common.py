import logging

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

from employer.models import *
from employer.views.jobs import daterange
from search.models import KeywordSearch, QBESearch

logger = logging.getLogger(__name__)


class IndexView(LoginRequiredMixin, View):
    template_name = 'employer/index.html'

    def get(self, request, *args, **kwargs):
        welcome_msg = SystemSetting.objects.filter(key='site_explaination').first().value
        return render(request, template_name=self.template_name, context={'content': welcome_msg})


class PublishDatasetView(View):
    """
    This view will provide link to download a JSON file contains:
    1. Links to videos and frames (publicly available at ./static/{videos,frames})
    2. Video segments, labels, attributes
    3. Annotations
        3.1 Space-time VATIC annotations (all solutions from annotators and reviewers comments).
        3.2 Survey answers and reviewers' comments for survey stage. Reviewers and annotators' names will not be revealed.
        3.3 Search results (with searched keyword and returned json from YouTube Data API).
    NOTE: At this stage, there will be no personal information of users (annotators and reviewers) will be published together with the dataset.
    We acknowledge that this might be important sometimes, for e.g, to follow-up researches, then we will consider privacy options in a future PYANO.
    Currently, PYANO don't handle such tasks relating to privacy.
    """
    template_name = 'employer/publish.html'

    def get(self, request, *args, **kwargs):
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
        return render(request, template_name=self.template_name, context={'job': job, 'tasks': tasks})