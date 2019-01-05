from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.views.generic import CreateView, View
from employer.models import *
from employer.forms import *
from common.forms import AddUserForm
import logging


class ProfileView(View):
    template_name = 'common/profile.html'

    def get(self,request, *args, **kwargs):
        return render(request, template_name=self.template_name, context={})


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
            context['status'] = 200
        except Exception as e:
            logging.error(e)
            context['status'] = 400
            context['error'] = 'Internal Server Error'
            return render(request, template_name=self.template_name, context=context)
        return redirect(to='/login/')
