from django.shortcuts import redirect, render
import logging

from django.shortcuts import redirect, render
from django.views.generic import View
from django_comments_xtd.models import Comment
from django.db.models import Count, Sum, Q, Avg
from django.db.models.functions import TruncDate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.timezone import now, timedelta
from survey import models as survey_models

from common.forms import AddWorkerForm
from search.models import *
from vatic.models import Solution
from employer.views.jobs import daterange
from worker.models import *

logger = logging.getLogger(__name__)


class ProfileView(LoginRequiredMixin, View):
    """
    Private profile view for workers.
    Basically, workers will not have access to common features such as public profiles or avatars.
    Those basic features only available for project owners and staffs.
    """
    template_name = 'common/profile.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_annotator and not request.user.is_reviewer:
            return redirect(to='/')
        context = {}
        if request.user.is_annotator:
            this_month_searches = KeywordSearch.objects.filter(worker=request.user,
                                                               created_at__gte=now() - timedelta(+30))
            last_month_searches = KeywordSearch.objects.filter(worker=request.user,
                                                               created_at__gte=now() - timedelta(+60),
                                                               created_at__lt=now() - timedelta(+30))
            context['this_month_searches'] = this_month_searches
            context['last_month_searches'] = last_month_searches
            if last_month_searches.count() == 0:
                context['up_searches'] = 'N/A'
            else:
                context['up_searches'] = '{:.2f} %'.format(
                    (this_month_searches.count() - last_month_searches.count()) / last_month_searches.count() * 100
                )
            this_month_suvery_answers = survey_models.Response.objects.filter(created__gte=now() - timedelta(+30),
                                                                              user=request.user).annotate(
                earning=Sum('survey__pyano_survey__credits__amount'))
            last_month_survey_answers = survey_models.Response.objects.filter(created__gte=now() - timedelta(+60),
                                                                              created__lt=now() - timedelta(+30),
                                                                              user=request.user).annotate(
                earning=Sum('survey__pyano_survey__credits__amount'))
            context['this_month_suvery_answers'] = this_month_suvery_answers
            context['last_month_survey_answers'] = last_month_survey_answers
            context['this_month_earning'] = sum([response.earning for response in this_month_suvery_answers])
            context['last_month_earning'] = sum([response.earning for response in last_month_survey_answers])
            if last_month_survey_answers.count() != 0:
                context['up_answers'] = '{:.2f} %'.format((
                                                                      this_month_suvery_answers.count() - last_month_survey_answers.count()) / last_month_survey_answers.count() * 100)
            else:
                context['up_answers'] = 'N/A'
            this_month_vatics = Solution.objects.filter(created_at__gte=now() - timedelta(+30),
                                                        submitter__user=request.user)  # .annotate(earning=Sum('job__group__credits__amount'))
            last_month_vatics = Solution.objects.filter(created_at__gte=now() - timedelta(+60),
                                                        created_at__lt=now() - timedelta(+30),
                                                        submitter__user=request.user)  # .annotate(earning=Sum('job__group__credits__amount'))
            context['this_month_vatics'] = this_month_vatics
            context['last_month_vatics'] = last_month_vatics
            context['this_month_earning'] += sum(
                [va.job.group.cost if va.job.completed else 0 for va in this_month_vatics])
            context['last_month_earning'] += sum(
                [va.job.group.cost if va.job.completed else 0 for va in last_month_vatics])
            if last_month_vatics.count() != 0:
                context['up_vatics'] = '{:.2f} %'.format(
                    (this_month_vatics.count() - last_month_vatics.count()) / last_month_vatics.count() * 100)
            else:
                context['up_vatics'] = 'N/A'
            if context['last_month_earning'] != 0:
                context['up_earning'] = '{:.2f} %'.format(
                    (context['this_month_earning'] - context['last_month_earning']) / context[
                        'last_month_earning'] * 100)
            else:
                context['up_earning'] = 'N/A'
            # Comments
            this_month_comments = Comment.objects.filter(is_removed=False,
                                                         user__is_annotator=False,
                                                         content_type__app_label__contains='vatic',
                                                         object_pk__in=[s.job.id for s in this_month_vatics],
                                                         submit_date__gte=now() - timedelta(+30))
            last_month_comments = Comment.objects.filter(is_removed=False,
                                                         user__is_annotator=False,
                                                         content_type__app_label__contains='vatic',
                                                         object_pk__in=[s.job.id for s in last_month_vatics],
                                                         submit_date__gte=now() - timedelta(+60),
                                                         submit_date__lt=now() - timedelta(+30))
            context['this_month_comments'] = this_month_comments
            context['last_month_comments'] = last_month_comments
        elif request.user.is_reviewer:
            this_month_comments = Comment.objects.filter(user=request.user,
                                                         is_removed=False,
                                                         content_type__app_label__contains='vatic',
                                                         submit_date__gte=now() - timedelta(+30))
            this_month_comments_by_date = Comment.objects.filter(user=request.user,
                                                                 is_removed=False,
                                                                 content_type__app_label__contains='vatic',
                                                                 submit_date__gte=now() - timedelta(+30)) \
                .annotate(day=TruncDate('submit_date')).values('day').annotate(created_count=Count('id'))
            data = {}
            for k in this_month_comments_by_date:
                data[k['day']] = k['created_count']
            context['this_month_comments_by_date'] = [data[d] if d in data else 0 for d in
                                                      daterange(start_date=now() - timedelta(+30),
                                                                end_date=now() + timedelta(+1))]
            last_month_comments = Comment.objects.filter(user=request.user,
                                                         is_removed=False,
                                                         content_type__app_label__contains='vatic',
                                                         submit_date__gte=now() - timedelta(+60),
                                                         submit_date__lt=now() - timedelta(+30))
            all_comments = Comment.objects.filter(user=request.user, is_removed=False,
                                                  content_type__app_label__contains='vatic')
            object_pks = list(set([c.object_pk for c in all_comments]))
            this_month_author_responses = Comment.objects.filter(~Q(user=request.user),
                                                                 user__is_annotator=True,
                                                                 is_removed=False,
                                                                 object_pk__in=object_pks,
                                                                 content_type__app_label__contains='vatic',
                                                                 submit_date__gte=now() - timedelta(+30))
            last_month_author_responses = Comment.objects.filter(~Q(user=request.user),
                                                                 user__is_annotator=True,
                                                                 is_removed=False,
                                                                 object_pk__in=object_pks,
                                                                 content_type__app_label__contains='vatic',
                                                                 submit_date__gte=now() - timedelta(+60),
                                                                 submit_date__lt=now() - timedelta(+30))
            if last_month_comments.count() > 0:
                context['up_comments'] = '{:.2f} %'.format(
                    (this_month_comments.count() - last_month_comments.count()) / last_month_comments.count() * 100
                )
            else:
                context['up_comments'] = 'N/A'
            context['this_month_comments'] = this_month_comments
            context['last_month_comments'] = last_month_comments
            context['num_comments'] = Comment.objects.filter(user=request.user, is_removed=False).count()
            context['this_month_author_responses'] = this_month_author_responses
            context['last_month_author_responses'] = last_month_author_responses
        return render(request, template_name=self.template_name, context=context)


class AddWorkerView(View):
    template_name = 'worker/register.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            redirect(to='/worker/profile/')
        form = AddWorkerForm()
        return render(request, template_name=self.template_name, context={'form': form})

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            redirect(to='/worker/profile/')
        context = {}
        form = AddWorkerForm(request.POST)
        try:
            if form.is_valid():
                user = form.save()
                if form.instance.is_annotator:
                    annotator = Annotator()
                    annotator.user = user
                    annotator.save()
                else:
                    reviewer = Reviewer()
                    reviewer.user = user
                    reviewer.save()
            else:
                context['error'] = 'Your information is invalid'
                context['form'] = form
                return render(request, template_name=self.template_name, context=context)
        except Exception as e:
            logger.debug(e)
            context['form'] = form
            context['error'] = 'Internal Server Error! Failed to register your information. {}'.format(e)
            return render(request, template_name=self.template_name, context=context)
        return redirect(to='/login/')
