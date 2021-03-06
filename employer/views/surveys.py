import logging
import uuid

from django.conf import settings
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

from employer.forms import *
from employer.models import Credit
from employer.models import Survey as PyanoSurvey
from worker.models import Reviewer, SurveyAssignment

logger = logging.getLogger(__name__)


class SurveyDetailView(LoginRequiredMixin, View):
    template_name = 'employer/survey/detail.html'

    def get(self, request, *args, **kwarg):
        id = request.GET.get('id', None)
        context = {}
        if id is None:
            context['error'] = 'No ID'
            return render(request, template_name=self.template_name, context=context)
        survey = PyanoSurvey.objects.filter(id=id).first()
        if survey is None:
            context['error'] = 'No survey found'
            return render(request, template_name=self.template_name, context=context)
        context['survey'] = survey
        context['videos'] = survey.parent.videos.annotate(num_answers=Count('video__responses', filter=Q(video__responses__survey=survey.survey))).all()

        return render(request, template_name=self.template_name, context=context)


class DeleteSurveyView(LoginRequiredMixin, View):
    template_name = 'employer/survey/delete.html'

    def get(self, request, *args, **kwarg):
        id = request.GET.get('id', None)
        context = {}
        if id is None:
            context['error'] = 'No ID'
            return render(request, template_name=self.template_name, context=context)
        surveys = PyanoSurvey.objects.filter(id=id).all()
        if surveys.count() == 0:
            context['error'] = 'No survey found'
            return render(request, template_name=self.template_name, context=context)
        else:
            for survey in surveys:
                survey.delete()
                survey.survey.delete()
        return render(request, template_name=self.template_name, context=context)


class AddSurveyView(LoginRequiredMixin, View):
    template_name = 'employer/survey/add.html'

    def get(self, request, *args, **kwargs):
        projectId = request.GET.get('projectId', None)
        if projectId is None:
            return redirect(to='/')
        form = AddSurveyForm()
        QuestionsFormSet = inlineformset_factory(Survey, Question, fields=('text', 'type', 'order', 'required', 'choices'))
        formset = QuestionsFormSet()
        job = Job.objects.filter(id=projectId).first()
        return render(request, template_name=self.template_name, context={'formset': formset, 'main_form': form, 'job': job})

    def post(self, request, *args, **kwargs):
        # survey
        form = AddSurveyForm(request.POST)
        if form.is_valid():
            instance = form.save()
        # pyano
        projectId = request.GET.get('projectId', None)
        survey = PyanoSurvey()
        survey.survey = instance
        survey.parent = Job.objects.filter(id=projectId).first()
        survey.guideline = request.POST.get('guideline', '')
        survey.save()
        # questions
        nq = int(request.POST.get('num_of_questions'))
        logger.info(nq)
        for i in range(nq):
            if request.POST.get('questions-{}-text'.format(i+1), '') != '' and \
                    request.POST.get('questions-{}-type'.format(i + 1), '') != '':
                question = Question()
                question.category = None
                question.text = request.POST.get('questions-{}-text'.format(i+1))
                question.type = request.POST.get('questions-{}-type'.format(i+1))
                order = request.POST.get('questions-{}-order'.format(i+1), None)
                try:
                    order = int(order)
                except:
                    order = 1
                question.order = order
                question.required = bool(request.POST.get('questions-{}-required'.format(i+1), True))
                question.choices = request.POST.get('questions-{}-choices'.format(i+1))
                question.survey = instance
                question.save()
        # credits
        credit = float(request.POST.get('credit', 0.0))
        c = Credit()
        c.amount = credit
        c.job = survey
        c.save()
        return render(request, self.template_name, context={})


class EditSurveyView(LoginRequiredMixin, View):
    template_name = 'employer/survey/change.html'

    def get(self, request, *args, **kwargs):
        id = request.GET.get('id', None)
        survey = PyanoSurvey.objects.filter(id=id).annotate(num_questions=Count('survey__questions')).first()
        if survey is None:
            return redirect(to='/')
        form = AddSurveyForm()
        QuestionsFormSet = inlineformset_factory(Survey, Question,
                                                 fields=('text', 'type', 'order', 'required', 'choices'))
        formset = QuestionsFormSet(instance=survey.survey)
        credit = Credit.objects.filter(job=survey).first()
        return render(request, template_name=self.template_name, context={'survey': survey, 'main_form': form,
                                                                          'formset': formset, 'credit': credit})

    def post(self, request, *args, **kwargs):
        id = request.POST.get('id', None)
        # pyano
        survey = PyanoSurvey.objects.filter(id=id).annotate(num_questions=Count('survey__questions')).first()
        survey.guideline = request.POST.get('guideline', '')
        survey.survey.name = request.POST.get('name', '')
        survey.survey.need_logged_user = bool(request.POST.get('need_logged_user', True))
        survey.survey.display_by_question = bool(request.POST.get('display_by_question', False))
        survey.survey.randomize_questions = bool(request.POST.get('randomize_questions', True))
        survey.survey.save()
        survey.save()
        # questions
        QuestionsFormSet = inlineformset_factory(Survey, Question,
                                                 fields=('text', 'type', 'order', 'required', 'choices'))
        formset = QuestionsFormSet(request.POST, request.FILES, instance=survey.survey)
        if formset.is_valid():
            formset.save()
        # credits
        credit = float(request.POST.get('credit', 0.0))
        c = Credit.objects.filter(job=survey).first()
        c.amount = credit
        c.save()
        return redirect(to='/job/list/')


class InviteReviewerView(LoginRequiredMixin, View):
    template_name = 'employer/invite_reviewer.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_employer:
            return redirect(to="/")
        id = request.GET.get('id', None)
        context = {}
        if id is None:
            context['error'] = 'No ID'
            return render(request, template_name=self.template_name, context=context)
        survey = PyanoSurvey.objects.filter(id=id).first()
        if survey is None:
            context['error'] = 'No survey found'
            return render(request, template_name=self.template_name, context=context)
        context['survey'] = survey
        reviewers = Reviewer.objects.filter(~Q(assignments__job=survey.survey)) # who are not assigned to this job
        # reviewers = reviewers.annotate(submitted_comments=Count('pyanousers_comments'))
        context['reviewers'] = reviewers
        return render(request, template_name=self.template_name, context=context)

    def post(self, request, *args, **kwargs):
        if not request.user.is_employer:
            return redirect(to="/")
        rid = request.POST.get('rid', None)
        sid = request.POST.get('sid', None)
        if rid is None or sid is None:
            return JsonResponse({'error': 'Reviewer ID or Survey ID is not presented.'})
        survey = PyanoSurvey.objects.filter(id=sid).first()
        if survey is None:
            return JsonResponse({'error': 'No survey is found.'})
        videos = survey.parent.videos.all()
        reviewer = Reviewer.objects.filter(user__id=rid).first()
        if reviewer is None:
            return JsonResponse({'error': 'Cannot find the reviewer.'})
        for video in videos:
            assignment = SurveyAssignment()
            assignment.reviewer = reviewer
            assignment.job = survey.survey
            assignment.video = video.video
            assignment.uuid = uuid.uuid4()
            try:
                assignment.save()
            except Exception as e:
                logger.debug(e)
        return JsonResponse({'message': 'The reviewer {} was successfully invited to your project.'.format(reviewer.user.get_full_name())})


