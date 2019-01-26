from django.shortcuts import redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

from vatic.models import Assignment
from worker.models import SurveyAssignment


class InvitationListView(LoginRequiredMixin, View):
    template_name = 'worker/review/list.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_reviewer:
            return redirect(to='/')
        assignments = SurveyAssignment.objects.filter(reviewer__user=request.user)
        vatics = Assignment.objects.filter(worker__user=request.user)
        context = {'surveys': assignments, 'vatics': vatics}
        return render(request, template_name=self.template_name, context=context)

