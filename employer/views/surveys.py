from django.views import View
from django.shortcuts import redirect, render
from django.conf import settings

from survey.models import Survey, Video
from employer.models import Survey as PyanoSurvey
from employer.models import Video as PyanoVideo
from employer.forms import *

import logging, os
from time import time
LOG_FILE = "./log/survey_{}.log".format(time())
if not os.path.exists("./log"):
    os.makedirs("./log")
formatter = logging.Formatter(fmt="[%(asctime)s]\t[%(levelname)s]\t[%(message)s]")
logger = logging.getLogger("survey")
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(fmt=formatter)
logger.addHandler(hdlr=file_handler)


class SurveyDetailView(View):
    template_name = 'employer/survey/detail.html'

    def get(self, request, *args, **kwarg):
        if not request.user.is_authenticated:
            return redirect(to='{}/login/?next=/survey/add/?id={}'.format(settings.LOGTIN_URL,
                                                                                 request.GET.get('id', None)))
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
        context['videos'] = survey.parent.videos.all()

        return render(request, template_name=self.template_name, context=context)


class AddSurveyView(View):
    template_name = 'employer/survey/add.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(to='{}/login/?next=/survey/add/?projectId={}'.format(settings.LOGTIN_URL,request.GET.get('projectId', None)))
        projectId = request.GET.get('projectId', None)
        if projectId is None:
            return redirect(to='/')
        form = AddSurveyForm()
        QuestionsFormSet = inlineformset_factory(Survey, Question, fields=('text', 'type', 'order', 'required', 'choices'))
        formset = QuestionsFormSet()
        job = Job.objects.filter(id=projectId).first()
        return render(request, template_name=self.template_name, context={'formset': formset, 'main_form': form, 'job': job})

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(to='{}/login/?next=/survey/add/'.format(settings.LOGTIN_URL))
        projectId = request.GET.get('projectId', None)
        if projectId is None:
            return redirect(to='/')
        # survey
        form = AddSurveyForm(request.POST)
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
                (request.POST.get('questions-{}-type'.format(i + 1), '') not in ['text', 'short-text'] and \
                     request.POST.get('questions-{}-choices'.format(i + 1), '') != '') and \
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
        return render(request, self.template_name, context={})

