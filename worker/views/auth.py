from django.shortcuts import redirect, render
import logging

from django.shortcuts import redirect, render
from django.views.generic import View
from django_comments_xtd.models import Comment
from django.db.models import Count, Sum, Q, Avg
from survey import models as survey_models

from common.forms import AddWorkerForm
from search.models import *
from vatic.models import Solution
from worker.models import *

logger = logging.getLogger(__name__)


class ProfileView(View):
    template_name = 'common/profile.html'

    def get(self,request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(to='{}/login/?next=/accounts/profile'.format(settings.LOGIN_URL))
        if not request.user.is_annotator and not request.user.is_reviewer:
            return redirect(to='/')
        context = {}
        if request.user.is_annotator:
            this_month_searches = KeywordSearch.objects.filter(worker=request.user, created_at__gte=now()-timedelta(+30))
            last_month_searches = KeywordSearch.objects.filter(worker=request.user, created_at__gte=now()-timedelta(+60),
                                                               created_at__lt=now()-timedelta(+30))
            context['this_month_searches'] = this_month_searches
            context['last_month_searches'] = last_month_searches
            if last_month_searches.count() == 0:
                context['up_searches'] = 'Last month data is NA'
            else:
                context['up_searches'] = (this_month_searches.count() - last_month_searches.count()) / last_month_searches.count() * 100
            this_month_suvery_answers = survey_models.Response.objects.filter(created__gte=now()-timedelta(+30),
                                                                              user=request.user).annotate(earning=Sum('survey__pyano_survey__credits__amount'))
            last_month_survey_answers = survey_models.Response.objects.filter(created__gte=now() - timedelta(+60),
                                                                              created__lt=now()-timedelta(+30),
                                                                              user=request.user).annotate(earning=Sum('survey__pyano_survey__credits__amount'))
            context['this_month_suvery_answers'] = this_month_suvery_answers
            context['last_month_survey_answers'] = last_month_survey_answers
            context['this_month_earning'] = sum([response.earning for response in this_month_suvery_answers])
            if last_month_survey_answers.count() != 0:
                context['up_answers'] = (this_month_suvery_answers.count()-last_month_survey_answers.count())/last_month_survey_answers.count() * 100
            else:
                context['up_answers'] = 'Last month data is NA'
            this_month_vatics = Solution.objects.filter(created_at__gte=now() - timedelta(+30),
                                                        submitter__user=request.user)
            last_month_vatics = Solution.objects.filter(created_at__gte=now() - timedelta(+60),
                                                        created_at__lt=now() - timedelta(+30),
                                                        submitter__user=request.user)
            context['this_month_vatics'] = this_month_vatics
            context['last_month_vatics'] = last_month_vatics
            if last_month_vatics.count() != 0:
                context['up_vatics'] = (this_month_vatics.count() - last_month_vatics.count()) / last_month_vatics.count() * 100
            else:
                context['up_vatics'] = 'Last month data is NA'
        elif request.user.is_reviewer:
            this_month_comments = Comment.objects.filter(user=request.user,
                                                         is_removed=False,
                                                         content_type__app_label__contains='survey',
                                                         submit_date__gte=now()-timedelta(+30))
            last_month_comments = Comment.objects.filter(user=request.user,
                                                         is_removed=False,
                                                         content_type__app_label__contains='survey',
                                                         submit_date__gte=now() - timedelta(+60),
                                                         submit_date__lt=now()-timedelta(+30))
            if last_month_comments.count() > 0:
                context['up_comments'] = (this_month_comments.count() - last_month_comments.count())/last_month_comments.count() * 100
            else:
                context['up_comments'] = 'Last month data is NA'
            context['this_month_comments'] = this_month_comments
            context['last_month_comments'] = last_month_comments
            context['num_comments'] = Comment.objects.filter(user=request.user, is_removed=False).count()
        return render(request, template_name=self.template_name, context=context)


class AddWorkerView(View):
    template_name = 'worker/register.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            redirect(to='/')
        form = AddWorkerForm()
        return render(request, template_name=self.template_name, context={'form': form})

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            redirect(to='/')
        context = {}
        try:
            form = AddWorkerForm(request.POST)
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
                return render(request, template_name=self.template_name, context=context)
        except Exception as e:
            logger.debug(e)
            context['error'] = 'Internal Server Error! Failed to register your information. {}'.format(e)
            return render(request, template_name=self.template_name, context=context)
        return redirect(to='/login/')
