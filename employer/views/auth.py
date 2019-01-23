import logging

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.shortcuts import redirect, render
from django.views.generic import View
from django_comments_xtd.models import Comment
from survey.models import Response

from common.forms import AddUserForm
from employer.models import *
from employer.views.jobs import daterange
from vatic.models import Solution, Path, Box

logger = logging.getLogger(__name__)


class ProfileView(View):
    template_name = 'employer/profile.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_annotator or request.user.is_reviewer:
            return redirect(to="/worker/profile/")
        context = {}
        if request.user.is_employer:
            # Survey answers
            this_month_survey_answers = Response.objects.filter(
                survey__pyano_survey__parent__topic__owner__user=request.user,
                created__gte=now() - timedelta(+30)
            )
            this_month_by_date = Response.objects.filter(
                survey__pyano_survey__parent__topic__owner__user=request.user,
                created__gte=now() - timedelta(+30)
            ).annotate(day=TruncDate('created')).values('day').annotate(created_count=Count('id'))
            data = {}
            for k in this_month_by_date:
                data[k['day']] = k['created_count']
            context['this_month_by_date'] = [data[d] if d in data else 0 for d in
                                             daterange(start_date=now() - timedelta(+30),
                                                       end_date=now() + timedelta(+1))]
            last_month_survey_answers = Response.objects.filter(
                survey__pyano_survey__parent__topic__owner__user=request.user,
                created__gte=now() - timedelta(+60),
                created__lt=now() - timedelta(+30)
            )
            context['this_month_survey_answers'] = this_month_survey_answers
            context['last_month_survey_answers'] = last_month_survey_answers
            if last_month_survey_answers.count() == 0:
                context['up_answers'] = 'N/A'
            else:
                context['up_answers'] = '{:.2f} %'.format(
                    100 * (
                            this_month_survey_answers.count() - last_month_survey_answers.count()) / last_month_survey_answers.count()
                )

            # VATIC solutions
            this_month_vatic_solutions = Solution.objects.filter(
                job__group__parent__topic__owner__user=request.user,
                created_at__gte=now() - timedelta(+30)
            )
            this_month_vatic_by_date = Solution.objects.filter(
                job__group__parent__topic__owner__user=request.user,
                created_at__gte=now() - timedelta(+30)
            ).annotate(day=TruncDate('created_at')).values('day').annotate(created_count=Count('id'))
            data = {}
            for k in this_month_vatic_by_date:
                data[k['day']] = k['created_count']
            context['this_month_vatic_by_date'] = [data[d] if d in data else 0 for d in
                                                   daterange(start_date=now() - timedelta(+30),
                                                             end_date=now() + timedelta(+1))]
            last_month_vatic_solutions = Solution.objects.filter(
                job__group__parent__topic__owner__user=request.user,
                created_at__gte=now() - timedelta(+60),
                created_at__lt=now() - timedelta(+30)
            )
            context['this_month_vatic_solutions'] = this_month_vatic_solutions
            context['last_month_vatic_solutions'] = last_month_vatic_solutions
            if last_month_vatic_solutions.count() == 0:
                context['up_vatics'] = 'N/A'
            else:
                context['up_vatics'] = '{:.2f} %'.format(
                    100 * (
                            this_month_vatic_solutions.count() - last_month_vatic_solutions.count()) / last_month_vatic_solutions.count()
                )

            # Tracks drawn by annotators
            this_month_tracks = Path.objects.filter(
                solution__job__group__parent__topic__owner__user=request.user,
                created_at__gte=now() - timedelta(+30)
            )
            this_month_tracks_by_date = Path.objects.filter(
                solution__job__group__parent__topic__owner__user=request.user,
                created_at__gte=now() - timedelta(+30)
            ).annotate(day=TruncDate('created_at')).values('day').annotate(created_count=Count('id'))
            data = {}
            for k in this_month_tracks_by_date:
                data[k['day']] = k['created_count']
            context['this_month_tracks_by_date'] = [data[d] if d in data else 0 for d in
                                                    daterange(start_date=now() - timedelta(+30),
                                                              end_date=now() + timedelta(+1))]
            last_month_tracks = Path.objects.filter(
                solution__job__group__parent__topic__owner__user=request.user,
                created_at__gte=now() - timedelta(+60),
                created_at__lt=now() - timedelta(+30)
            )
            context['this_month_tracks'] = this_month_tracks
            context['last_month_tracks'] = last_month_tracks
            if last_month_tracks.count() == 0:
                context['up_tracks'] = 'N/A'
            else:
                context['up_tracks'] = '{:.2f} %'.format(
                    100 * (this_month_tracks.count() - last_month_tracks.count()) / last_month_tracks.count()
                )

            # Bounding boxes drawn by annotators
            this_month_boxes = Box.objects.filter(
                path__solution__job__group__parent__topic__owner__user=request.user,
                created_at__gte=now() - timedelta(+30)
            )
            this_month_boxes_by_date = Box.objects.filter(
                path__solution__job__group__parent__topic__owner__user=request.user,
                created_at__gte=now() - timedelta(+30)
            ).annotate(day=TruncDate('created_at')).values('day').annotate(created_count=Count('id'))
            data = {}
            for k in this_month_boxes_by_date:
                data[k['day']] = k['created_count']
            context['this_month_boxes_by_date'] = [data[d] if d in data else 0 for d in
                                                    daterange(start_date=now() - timedelta(+30),
                                                              end_date=now() + timedelta(+1))]
            last_month_boxes = Box.objects.filter(
                path__solution__job__group__parent__topic__owner__user=request.user,
                created_at__gte=now() - timedelta(+60),
                created_at__lt=now() - timedelta(+30)
            )
            context['this_month_boxes'] = this_month_boxes
            context['last_month_boxes'] = last_month_boxes
            if last_month_boxes.count() == 0:
                context['up_boxes'] = 'N/A'
            else:
                context['up_boxes'] = '{:.2f} %'.format(
                    100 * (this_month_boxes.count() - last_month_boxes.count()) / last_month_boxes.count()
                )
            # Comments
            this_month_comments = Comment.objects.filter(
                content_type__app_label__in=['vatic', 'survey'],
                submit_date__gte=now()-timedelta(+30)
            )
            context['this_month_comments'] = this_month_comments
        return render(request, template_name=self.template_name, context=context)


class AddEmployerView(View):
    template_name = 'employer/register.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            redirect(to='/')
        form = AddUserForm()
        return render(request, template_name=self.template_name, context={'form': form})

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            redirect(to='/')
        context = {}
        try:
            form = AddUserForm(request.POST)
            form.Meta.model.is_annotator = False
            form.Meta.model.is_reviewer = False
            form.Meta.model.is_employer = True
            if form.is_valid():
                form.save()
            employer = Employer()
            employer.user = form.instance
            employer.save()
        except Exception as e:
            logger.debug(e)
            context['error'] = 'Internal Server Error'
            return render(request, template_name=self.template_name, context=context)
        return redirect(to='/login/')
