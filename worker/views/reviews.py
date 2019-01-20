from django.views import View
from django.shortcuts import redirect, render
from django.conf import settings
from django.db.models import Count, Q, Sum
from django.http import JsonResponse

from survey.models import Survey, Video
from employer.models import Survey as PyanoSurvey
from employer.models import Video as PyanoVideo
from employer.models import Credit
from employer.forms import *
from worker.models import Reviewer, SurveyAssignment
from vatic.models import Assignment
from django_comments_xtd.models import Comment


class InvitationListView(View):
    template_name = 'worker/review/list.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_reviewer:
            return redirect(to='/')
        assignments = SurveyAssignment.objects.filter(reviewer__user=request.user)
        vatics = Assignment.objects.filter(worker__user=request.user)
        context = {'surveys': assignments, 'vatics': vatics}
        return render(request, template_name=self.template_name, context=context)

