from django.views import View
from django.shortcuts import redirect, render
from django.conf import settings
from employer.forms import AddTopicForm
from employer.models import Topic, Job
from django.db.models import Count

import logging


class AddTopicView(View):
    template_name = 'employer/topic/add.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            redirect(to='{}/login/?next=/topic/add/'.format(settings.LOGIN_URL))
        form = AddTopicForm()
        return render(request, template_name=self.template_name, context={'form': form})

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            redirect(to='{}/login/?next=/topic/add/'.format(settings.LOGIN_URL))
        context = {}
        try:
            form = AddTopicForm(request.POST)
            form.Meta.model.owner = request.user
            form.save()
            context['status'] = 200
        except Exception as e:
            logging.error(e)
            context['status'] = 400
            context['error'] = 'Internal Server Error'
            render(request, template_name=self.template_name, context=context)
        return redirect(to='/topic/list/')


class ChangeTopicView(View):
    template_name = 'employer/topic/change.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(to='{}/login/?next=/topic/change/?id={}'.format(settings.LOGIN_URL, request.GET.get('id', None)))
        if not request.user.is_employer:
            return redirect(to="/")
        id = request.GET.get('id', None)
        if id is not None:
            topic = Topic.objects.filter(id=id).first()
        else:
            topic = None
        return render(request, template_name=self.template_name, context={'id': id, 'topic': topic})

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(to='{}/login/?next=/'.format(settings.LOGIN_URL))
        if not request.user.is_employer:
            return redirect(to="/")
        context = {}
        try:
            id = request.POST.get('id', None)
            topic = Topic.objects.filter(id=id).first()
            name = request.POST.get('name', None)
            if name is not None:
                topic.name = name
            desc = request.POST.get('description')
            if desc is not None:
                topic.description = desc
            topic.save()
            context['status'] = 200
        except Exception as e:
            logging.error(e)
            context['status'] = 400
            context['error'] = 'Internal Server Error while saving topic'
            render(request, template_name=self.template_name, context=context)
        return redirect(to='/topic/list/')


class TopicListView(View):
    template_name = 'employer/topic/list.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(to='{}/login/?next=/topic/list/'.format(settings.LOGIN_URL))
        if not request.user.is_employer:
            return redirect(to="/")
        topics = Topic.objects.filter(owner__user=request.user).annotate(num_jobs=Count('jobs'))
        return render(request, template_name=self.template_name, context={'topics': topics})


class TopicDetailView(View):
    template_name = 'employer/topic/detail.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(to='{}/login/?next=/topic/details/?id={}'.format(settings.LOGIN_URL, request.GET.get('id', None)))
        if not request.user.is_employer:
            return redirect(to="/")
        topic = Topic.objects.filter(id=request.GET.get('id', None)).first()
        jobs = Job.objects.filter(topic__owner__user=request.user,
                                  topic__id=request.GET.get('id', None))
        return render(request, template_name=self.template_name, context={'jobs': jobs, 'topic': topic})