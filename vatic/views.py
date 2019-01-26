from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views import View

if "pinax.notifications" in settings.INSTALLED_APPS:
    from pinax.notifications import models as notification
    from pinax.notifications.views import NoticeSettingsView
else:
    notification = None

from vatic import models as vatic_models
from vatic.forms import *
from comment.forms import CommentForm
from comment.models import Comment
from search.youtube import download_youtube_video
from vatic.video import *
from worker.models import *
from glob import glob
import uuid


DOWNLOAD_DIR='{}/static/videos'.format(settings.BASE_DIR)
FRAME_DIR='{}/static/frames'.format(settings.BASE_DIR)


class IndexView(LoginRequiredMixin, View):
    template_name = 'vatic/index.html'

    def get(self, request, *args, **kwargs):
        return render(request, template_name=self.template_name, context={})


class VATICListView(LoginRequiredMixin, View):
    template_name = 'vatic/list.html'

    def get(self, request, *args, **kwargs):
        jobs = vatic_models.Job.objects.filter(completed=False).all()
        return render(request, template_name=self.template_name, context={'jobs': jobs})


class VATICDownloadView(LoginRequiredMixin, View):
    template_name = 'vatic/download.html'

    def post(self, request, *args, **kwargs):
        length = int(request.POST.get('length', 300))
        width = int(request.POST.get('width', 720))
        height = int(request.POST.get('height', 480))
        noresize = not bool(request.POST.get('resize', True))
        labels = request.POST.get('labels', '')
        groupId = int(request.POST.get('group', 1))
        videoID = request.POST.get('videoID', None)
        if videoID is None:
            return render(request, template_name=self.template_name, context={'error': 'videoID is required.'})
        video = survey_models.Video.objects.filter(id=videoID).first()
        if video is None:
            return render(request, template_name=self.template_name, context={'error': 'Video is not found.'})
        if not os.path.exists(DOWNLOAD_DIR):
            os.makedirs(DOWNLOAD_DIR)
        try:
            download_youtube_video(youtube_ids=[video.vid], output_folder=DOWNLOAD_DIR)
        except Exception as e:
            logger.debug(e)
            return render(request, template_name=self.template_name, context={'error': 'Download error.'})
        try:
            files = glob(DOWNLOAD_DIR+'/' + video.vid + '.*')
            extractor = Extractor(video_path=files[0],
                              output_path=os.path.join(FRAME_DIR, '{}'.format(video.vid)),
                              width=width, height=height, no_resize=noresize)
            extractor()
        except Exception as e:
            logger.debug(e)
            return render(request, template_name=self.template_name, context={'error': 'Frame extraction error.'})
        try:
            loader = Loader(location=os.path.join(FRAME_DIR, '{}'.format(video.vid)),
                        labels=labels.split(','), pyano_video_id=videoID, length=length)
            group = JobGroup.objects.filter(id=groupId).first()
            loader(group=group)
        except Exception as e:
            logger.debug(e)
            return render(request, template_name=self.template_name, context={'error': 'Segment loading error. {}'.format(e)})
        return render(request, template_name=self.template_name, context={})


class AddJobGroupView(LoginRequiredMixin, View):
    template_name = 'vatic/jobgroup/add.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_employer:
            return render(request, template_name=self.template_name, context={'status': 400})
        form = AddJobGroupForm()
        return render(request, template_name=self.template_name, context={'form': form})

    def post(self, request, *args, **kwargs):
        form = AddJobGroupForm(request.POST)
        if form.is_valid():
            form.save()
        return render(request, template_name=self.template_name, context={'status': 200})


class DetailJobGroupView(LoginRequiredMixin, View):
    template_name = 'vatic/jobgroup/detail.html'

    def get(self, request, *args, **kwargs):
        id = request.GET.get('id', None)
        if id is None:
            return render(request, template_name=self.template_name, context={'status': 400})
        group = JobGroup.objects.filter(id=id).first()
        if group is None:
            return render(request, template_name=self.template_name, context={'status': 400})
        jobs = group.jobs.filter(completed=False).annotate(num_paths=Count('solutions__paths'))
        return render(request, template_name=self.template_name, context={'jobs': jobs, 'group': group})


class JobView(LoginRequiredMixin, View):
    template_name = 'vatic/index.html'

    def get(self, request, *args, **kwargs):
        id = request.GET.get('id',None)
        if id is None:
            return redirect(to='/')
        job = vatic_models.Job.objects.filter(id=id).first()
        if job is None:
            return redirect(to='/')
        return render(request, template_name=self.template_name, context={'job':job, 'id': id})


class ReviewJobView(LoginRequiredMixin, View):
    """
    The view for reviewers and meta-reviewers of the job.
    """
    template_name = 'vatic/review.html'

    def get(self, request, *args, **kwargs):
        id = request.GET.get('id',None)
        if id is None:
            return redirect(to='/')
        reviewer = Reviewer.objects.filter(user=request.user, vatic_assignments__job__id=id).first()
        employer = Employer.objects.filter(user=request.user).first()
        if reviewer is None and employer is None:
            return redirect(to='/')
        job = vatic_models.Job.objects.filter(id=id).first()
        if job is None:
            return redirect(to='/')
        is_owner = True # whether if the job is owned by the owner.
        if employer is not None:
            job = vatic_models.Job.objects.filter(id=id, group__parent__topic__owner=employer).first()
            if job is None:
                is_owner = False
        else:
            is_owner = False
        # logger.info(job.group.parent.topic.owner)
        form = CommentForm()
        meta_comment = Comment.objects.filter(job=job).first()
        return render(request, template_name=self.template_name, context={'job':job, 'id': id,
                                                                          'form': form, "is_owner": is_owner,
                                                                          'meta_comment': meta_comment})

    def post(self, request, *args, **kwargs):
        id = request.POST.get('id', None)
        employer = Employer.objects.filter(user=request.user).first()
        if employer is None:
            return redirect(to="/")
        job = vatic_models.Job.objects.filter(id=id, group__parent__topic__owner=employer).first()
        if job is None:
            return redirect(to='/')
        try:
            form = CommentForm(request.POST)
            if form.is_valid():
                form.instance.reviewer = employer
                form.instance.job = job
                if form.instance.score > 5:
                    job.completed = True # accepted job is marked as completed. Weak-accepted works and below will be considered further.
                    job.save()
                if form.is_valid():
                    form.save()
        except Exception as e:
            logger.debug(e)
            print(e)
            return JsonResponse({'error': '{}'.format(e)})
        return redirect(to="/vatic/review/?id={}".format(id))


if notification:
    class VATICJobNoticeSettingsView(NoticeSettingsView):
        job = None

        @property
        def scoping(self):
            return self.request.job


class InvitationView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        id = request.POST.get('id', None)
        if id is None:
            return JsonResponse({'error': 'No ID is provided.'})
        job = vatic_models.Job.objects.filter(id=id, group__parent__topic__owner__user=request.user).first()
        if job is None:
            return JsonResponse({'error': 'Jobs of this user are not found.'})
        annotators = Annotator.objects.all() # all annotators who has not been assigned to this job
        users = [annotator.user for annotator in annotators]
        if notification:
            try:
                notification.send(users, 'vatic_job_invite', {'from_user': request.user}, scoping=job)
            except Exception as e:
                logger.debug(e)
                return JsonResponse({'error': 'Internal Server Error: {}'.format(e)})
        else:
            return JsonResponse({'error': 'Cannot connect to notification app.'})
        return JsonResponse({'msg': 'Invited {} annotators to the job.'.format(len(users))})


class ReviewerInviteView(LoginRequiredMixin, View):
    template_name = 'vatic/invite_reviewer.html'

    def get(self, request, *args, **kwargs):
        context = {}
        id = request.GET.get('id', None)
        if id is None:
            context['error'] = 'No ID is provided.'
        else:
            job = vatic_models.Job.objects.filter(id=id, group__parent__topic__owner__user=request.user).first()
            if job is None:
                context['error'] = 'No job is provided.'
            else:
                context['job'] = job
                reviewers = Reviewer.objects.filter(~Q(vatic_assignments__job=job))
                context['reviewers'] = reviewers
        return render(request, template_name=self.template_name, context=context)

    def post(self, request, *args, **kwargs):
        uid = request.POST.get('rid', None)
        jid = request.POST.get('jid', None)
        if uid is None or jid is None:
            return JsonResponse({'error': 'Your information is defective.'})
        reviewer = Reviewer.objects.filter(user__id=uid).first()
        job = vatic_models.Job.objects.filter(id=jid, group__parent__topic__owner__user=request.user).first()
        if reviewer is None:
            return JsonResponse({'error': 'Your reviewer information is not identified.'})
        if job is None:
            return JsonResponse({'error': 'Your job information is not identified.'})
        assignment = Assignment.objects.filter(worker=reviewer, job=job).first()
        if assignment is None:
            assignment = Assignment(worker=reviewer, job=job, uuid=uuid.uuid4())
            assignment.save()
        return JsonResponse({})
