from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.views.generic import CreateView, View
from worker.models import *
from worker.forms import *
from common.forms import AddWorkerForm
import logging


class ProfileView(View):
    template_name = 'worker/index.html'

    def get(self,request, *args, **kwargs):
        return render(request, template_name=self.template_name, context={})


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
            user = form.save()
            if form.Meta.model.is_annotator:
                annotator = Annotator()
                annotator.user = user
                annotator.save()
            else:
                reviewer = Reviewer()
                reviewer.user = user
                reviewer.save()
        except Exception as e:
            context['status'] = 400
            context['error'] = 'Internal Server Error! Failed to register your information.'
            return render(request, template_name=self.template_name, context=context)
        context['status'] = 200
        return redirect(to='/login/')
