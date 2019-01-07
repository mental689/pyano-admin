from django.conf import settings
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.views import View
from survey.models import Response, Video, Survey, Answer

from employer.models import Survey as PyanoSurvey
from worker.models import SurveyAssignment

import logging
logger = logging.getLogger(__name__)


class SurveyReviewView(View):
    template_name = 'survey/review.html'

    def get(self, request, sid):
        context = {}
        if not request.user.is_authenticated:
            return redirect(to="/login/?next=/worker/survey/review/{}/".format(settings.LOGIN_URL,sid))
        survey = PyanoSurvey.objects.filter(survey__id=sid).first()
        if survey is None:
            context['error'] = 'Survey ID {} is not found.'.format(sid)
            return render(request, template_name=self.template_name, context=context)
        # Check if the reviewer is assigned to this job
        assignment = SurveyAssignment.objects.filter(reviewer__user=request.user, job__id=sid)
        if assignment.count() < 1 and survey.parent.topic.owner.user != request.user:
            context['error'] = 'You are not assigned.'
            return render(request, template_name=self.template_name, context=context)
        context['survey'] = survey
        context['videos'] = survey.parent.videos.annotate(
            num_answers=Count('video__responses', filter=Q(video__responses__survey=survey.survey))).all()

        return render(request, template_name=self.template_name, context=context)


class SurveyVideoReviewView(View):
    template_name = 'survey/survey_for_review.html'

    def get(self, request, sid, vid):
        context = {}
        if not request.user.is_authenticated:
            return redirect(to="/login/?next=/worker/survey/review/{}/{}/".format(sid,vid))
        # Check if the reviewer is assigned to this job
        video = Video.objects.filter(id=vid).first()
        survey = Survey.objects.filter(id=sid).first()
        if video is None or survey is None:
            return redirect(to='/')
        context['video'] = video
        context['survey'] = survey
        assignment = SurveyAssignment.objects.filter(reviewer__user=request.user, job=survey, video=video).first()
        if assignment is None:
            if request.user.is_employer:
                pyano_survey = PyanoSurvey.objects.filter(survey=survey, parent__topic__owner__user=request.user).first()
                if pyano_survey is None:
                    return redirect(to="/")
            else:
                return redirect(to="/") # just redirect to homepage
        responses = Response.objects.filter(survey=survey, video=video)
        context['responses'] = responses
        return render(request, template_name=self.template_name, context=context)

