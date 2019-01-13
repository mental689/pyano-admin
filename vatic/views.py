from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views import View
from django.db.models import Count, Q, Sum

from vatic.models import *
from vatic.forms import *
from search.youtube import download_youtube_video
from vatic.video import *
import json
from glob import glob
import uuid


DOWNLOAD_DIR='{}/static/videos'.format(settings.BASE_DIR)
FRAME_DIR='{}/static/frames'.format(settings.BASE_DIR)


class IndexView(View):
    template_name = 'vatic/index.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(to="{}?next=/vatic".format(settings.LOGIN_URL))
        return render(request, template_name=self.template_name, context={})


class VATICListView(View):
    template_name = 'vatic/list.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(to="{}?next=/vatic/list".format(settings.LOGIN_URL))
        jobs = Job.objects.filter(completed=False).all()
        return render(request, template_name=self.template_name, context={'jobs': jobs})


class VATICDownloadView(View):
    template_name = 'vatic/download.html'

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return render(request, template_name=self.template_name, context={'error': 'Login is required.'})
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


class AddJobGroupView(View):
    template_name = 'vatic/jobgroup/add.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(to='{}/?next=/vatic/group/add/'.format(settings.LOGIN_URL))
        if not request.user.is_employer:
            return render(request, template_name=self.template_name, context={'status': 400})
        form = AddJobGroupForm()
        return render(request, template_name=self.template_name, context={'form': form})

    def post(self, request, *args, **kwargs):
        form = AddJobGroupForm(request.POST)
        if form.is_valid():
            form.save()
        return render(request, template_name=self.template_name, context={'status': 200})


class DetailJobGroupView(View):
    template_name = 'vatic/jobgroup/detail.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(to='{}/?next=/vatic/group/detail/?id={}'.format(settings.LOGIN_URL, request.GET.get('id', None)))
        id = request.GET.get('id', None)
        if id is None:
            return render(request, template_name=self.template_name, context={'status': 400})
        group = JobGroup.objects.filter(id=id).first()
        if group is None:
            return render(request, template_name=self.template_name, context={'status': 400})
        jobs = group.jobs.annotate(num_paths=Count('solutions__paths'))
        return render(request, template_name=self.template_name, context={'jobs': jobs, 'group': group})


class JobView(View):
    template_name = 'vatic/index.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(to="{}?next=/vatic/job/?id={}".format(settings.LOGIN_URL, request.GET.get('id',None)))
        id = request.GET.get('id',None)
        if id is None:
            return redirect(to='/')
        job = Job.objects.filter(id=id).first()
        if job is None:
            return redirect(to='/')
        return render(request, template_name=self.template_name, context={'job':job, 'id': id})



# class VATICFinalizeJobView(View):
#     def get(self, request, *args, **kwargs):
#         if not request.user.is_authenticated:
#             return redirect(to="{}?next=/vatic/finalize/".format(settings.LOGIN_URL))
#         if not request.user.is_staff:
#             return redirect(to="/")
#         context = {}
#         id = request.GET.get('id')
#         try:
#             jobs = VATICJob.objects.filter(id=id)
#             for job in jobs.all():
#                 if job.completed: continue
#                 job.completed = True
#                 job.save()
#                 break
#         except Exception as e:
#             logging.error('Internal Server Error: {}'.format(e))
#         return redirect(to="/vatic/list")
#
#
# class VATICCrawlerView(View):
#     template_name = 'vatic/crawler.html'
#
#     def get(self, request, *args, **kwargs):
#         if not request.user.is_authenticated:
#             return redirect(to="{}?next=/vatic/crawler/".format(settings.LOGIN_URL))
#         if not request.user.is_staff:
#             return redirect(to="/")
#         context = {}
#         try:
#             gid = request.GET.get('gid')
#             context['gid'] = gid
#             groups = VATICJobGroup.objects.filter(id=gid)
#             if len(groups) > 0:
#                 group = groups[0]
#                 context['group'] = group
#                 videos = Video.objects.annotate(num_responses=Count('responses'))
#                 videos = videos.filter(num_responses__gt=0)
#                 videos = videos.annotate(num_locks=Count('bans'))
#                 videos = videos.filter(num_locks=0)
#                 context['videos'] = videos
#             else:
#                 context['error'] = 'No group found.'
#         except Exception as e:
#             context['error'] = 'Internal Server Error: {}'.format(e)
#         return render(request, template_name=self.template_name, context=context)
#
#     def post(self, request, *args, **kwargs):
#         if not request.user.is_authenticated:
#             return JsonResponse({'status': 404, 'error': 'No user'})
#         if not request.user.is_staff:
#             return JsonResponse({'status': 404, 'error': 'No staff'})
#         try:
#             id = request.POST.get('id')
#             vid = request.POST.get('vid')
#             gid = request.POST.get('gid')
#             groups = VATICJobGroup.objects.filter(id=gid)
#             if len(groups) == 0:
#                 return JsonResponse({'status': 404, 'error': 'No group'})
#             else:
#                 group = groups[0]
#             videos = Video.objects.filter(id=id)
#             # Check if the video is locked or not
#             if len(videos) > 0:
#                 locks = BannedVideo.objects.filter(video=videos[0])
#                 if len(locks) > 0:
#                     return JsonResponse({'status': 404, 'error': 'Locked videos'})
#             else:
#                 return JsonResponse({'status': 404, 'error': 'No video found'})
#             download_youtube_video(youtube_ids=[vid],
#                                    output_folder=os.path.join(pyano_settings.BASE_DIR, 'static/videos'))
#
#             files = glob(os.path.join(pyano_settings.BASE_DIR, 'static/videos/{}'.format(request.POST.get('vid'))) + '.*')
#             if len(files) > 0:
#                 f = files[0]
#                 output_path = os.path.join(pyano_settings.BASE_DIR, 'static/frames/{}'.format(request.POST.get('vid')))
#                 extractor = VATICExtractor(video_path=f, output_path=output_path)
#                 extractor()
#                 labels = request.POST.get('labels').split(',')
#                 print(labels)
#                 loader = VATICLoader(location=output_path,
#                                      labels=labels,
#                                      pyano_video_id=id)
#                 loader(group)
#             # After having all of this process done, we should lock the video to prevent downloading again.
#             if len(videos) > 0:
#                 lock = BannedVideo()
#                 lock.video = videos[0]
#                 lock.why = 1
#                 lock.save()
#         except Exception as e:
#             return JsonResponse({'status': 404, 'error': e})
#         return JsonResponse({'status': 200})
#
#
# class VideoAnswerView(View):
#     def post(self, request, vid, *args, **kwargs):
#         if not request.user.is_authenticated:
#             return JsonResponse({'status': 404, 'error': 'No user'})
#         if not request.user.is_staff:
#             return JsonResponse({'status': 404, 'error': 'No staff'})
#         answers = {}
#         try:
#             videos = Video.objects.filter(id=vid)
#             if len(videos) > 0:
#                 video = videos[0]
#                 responses = video.responses.all()
#                 for i, response in enumerate(responses):
#                     answers[i] = {'uname': '', 'questions': []}
#                     if not response.user:
#                         answers[i]['uname'] = 'Unknown'
#                     else:
#                         answers[i]['uname'] = response.user.username
#                     ans = response.answers.all()
#                     for an in ans:
#                         q = an.question.text
#                         a = an.body
#                         answers[i]['questions'].append({'question': q, 'answer': a})
#         except Exception as e:
#             return JsonResponse({'status': 404, 'error': e})
#         return JsonResponse({'status': 200, 'answers': answers})
#
#
# class VATICAssignWorker(View):
#     template_name = 'vatic/assignment.html'
#
#     def get(self, request, *args, **kwargs):
#         if not request.user.is_authenticated:
#             return redirect(to="{}?next=/vatic/list".format(settings.LOGIN_URL))
#         if not request.user.is_staff:
#             return redirect(to="/")
#         jobs = VATICJob.objects.filter(completed=False).all()
#         users = User.objects.filter(~Q(email=''))
#         return render(request, template_name=self.template_name, context={'jobs': jobs, 'users': users})
#
#     def post(self, request, *args, **kwargs):
#         if not request.user.is_authenticated:
#             return redirect(to="/")
#         uid = request.POST.get('uid', None)
#         start_jid = int(request.POST.get('sid', 0))
#         end_jid = int(request.POST.get('eid', 100))
#         jobs = VATICJob.objects.filter(completed=False, id__gte=start_jid, id__lte=end_jid).all()
#         aid = uuid.uuid4()
#         if uid is not None:
#             users = User.objects.filter(id=uid)
#             if users.count() > 0:
#                 user = users[0]
#                 for job in jobs:
#                     assign = VATICWorkerJob()
#                     assign.worker = user
#                     assign.job = job
#                     assign.uuid = aid
#                     try:
#                         assign.save()
#                     except:
#                         continue
#                 user.email_user(subject='You have job offers!',
#                                 message="Admins have assigned some important jobs to you. Congratulation! "
#                                         "You can login and visit http://13.58.121.50:8000/vatic/assignment/?uuid={} "
#                                         "to see the list of jobs you have been offered. ".format(aid))
#         return redirect(to="/")
#
#
# class VATICAssignmentView(View):
#     template_name = 'vatic/list.html'
#
#     def get(self, request, *args, **kwargs):
#         if not request.user.is_authenticated:
#             return redirect(to="{}?next=/vatic/assignment/?uuid={}".format(settings.LOGIN_URL, request.GET.get('uuid')))
#         uuid = request.GET.get('uuid')
#         if uuid is None:
#             jobs = []
#         else:
#             assignments = VATICWorkerJob.objects.filter(worker=request.user, uuid=request.GET.get('uuid'))
#             jobs = [a.job for a in assignments]
#         return render(request, template_name=self.template_name, context={'jobs': jobs})
#
#
# class CommentView(View):
#     template_name = 'vatic/submit_review.html'
#
#     def post(self, request, *args, **kwargs):
#         if not request.user.is_authenticated or not request.user.is_staff:
#             return redirect(to='/')
#         id = request.POST.get('id', None)
#         context = {}
#         if id is None:
#             context['error'] = 'Work is not found.'
#             return render(request, template_name=self.template_name, context=context)
#         job = VATICJob.objects.filter(id=id).first()
#         if job is None:
#             context['error'] = 'Job is not found.'
#             return render(request, template_name=self.template_name, context=context)
#         form = ReviewForm(request.POST)
#         form.instance.user = request.user
#         form.instance.job = job
#         form.save()
#         return render(request, template_name=self.template_name, context=context)
#
#
