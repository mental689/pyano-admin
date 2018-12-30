from django.contrib.auth import login
from django.shortcuts import redirect
from django.views.generic import CreateView
from employer.models import *
from employer.forms import *


class SignupView(CreateView):
    model = PyanoUser
