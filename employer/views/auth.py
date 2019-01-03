from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.views.generic import CreateView, View
from employer.models import *
from employer.forms import *


class ProfileView(View):
    template_name = 'employer/profile.html'

    def get(self,request, *args, **kwargs):
        return render(request, template_name=self.template_name, context={})
