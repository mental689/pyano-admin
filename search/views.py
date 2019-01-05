from django.shortcuts import render, redirect
from django.views import View
from django.http import HttpResponse, JsonResponse
from search.models import *
from employer.models import Job
from employer.models import Video as PyanoVideo
from worker.models import Annotator
from common.models import *
from survey.models import Video as SurveyVideo
from django.conf import settings

from search.youtube import *


# Create your views here.


class KeywordSearchJSONOutcomeView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(to="/")
        id = request.GET.get('id', None)
        if id is not None:
            try:
                record = KeywordSearch.objects.filter(id=id).first()
                return HttpResponse(record.outcome)
            except Exception as e:
                logger.error(e)
                return JsonResponse({})
        return JsonResponse({})


class KeywordSearchView(View):
    template_name = 'search/index.html'

    def _get_dev_key(self):
        try:
            dev_keys = SystemSetting.objects.filter(key="youtube_dev_key").first()
            if dev_keys is None:
                logger.error("No Youtube API devkeys found!")
                return None
            return dev_keys.value
        except Exception as e:
            logger.error(e)
            return None

    def _search_youtube(self, keyword, user, job, cc=True, hd=False, duration="any"):
        dev_key = self._get_dev_key()
        if dev_key is None:
            return None
        yt = build_youtube_instance(dev_key)
        results = search_youtube(youtube=yt, q=keyword.strip(), download_cc_only=cc, download_high_quality=hd,
                                 duration_type=duration)
        # insert data
        key = KeywordSearch()
        key.keyword = keyword.strip()
        key.worker = user
        key.parent = job
        key.outcome = results
        try:
            key.save()
        except Exception as e:
            logger.error(e)
        logger.info("Finished searching on YouTube with keyword {}".format(keyword))

        videos = []
        for r in results:
            if 'id' in r and 'kind' in r['id'] and 'videoId' in r['id'] and r['id']['kind'] == "youtube#video":
                videos.append(r)
                sv = SurveyVideo.objects.filter(vid=r['id']['videoId']).first()
                if sv is None:
                    sv = SurveyVideo()
                    sv.url = "https://youtube.com/watch?v={}".format(r['id']['videoId'])
                    sv.vid = r['id']['videoId']
                    sv.channelId = r['snippet']['channelId']
                    blocks = BlockedChannel.objects.filter(
                        channelId=sv.channelId)  # videos from blocked channels won't be added in to our database again.
                    if blocks.count() > 0:
                        continue
                    sv.type = 0
                    sv.start = 0
                    sv.end = 0
                    try:
                        sv.save()
                        v = PyanoVideo()
                        v.video = sv
                        v.parent = job
                        v.save()
                    except Exception as e:
                        logger.error(e)
                        continue
                else:
                    # Just add this video to new job
                    try:
                        v = PyanoVideo()
                        v.video = sv
                        v.parent = job
                        v.save()
                    except Exception as e: # possible errors occur when UNIQUE constraints ('video' and 'parent' fields together) are not satisfied.
                        logger.error(e)
                        continue
        return videos

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(
                to="/login/?next=/search/?projectId={}".format(settings.LOGIN_URL, request.GET.get('projectId', None)))
        context = {}
        try:
            annotator = Annotator.objects.filter(user=request.user).first()
        except Exception as e:
            context["error"] = "Internal Server Error"
        if annotator is None:
            context['error'] = "You are not an annotator! This job is only available for annotators. " \
                               "Reviewers and project owners can see outcomes."
            return render(request, template_name=self.template_name, context=context)
        context['annotator'] = annotator
        projectId = request.GET.get('projectId', None)
        if projectId is not None:
            try:
                job = Job.objects.filter(id=projectId, is_completed=False).first()
                if job is None:
                    context['error'] = 'No project found!'
                context['job'] = job
            except Exception as e:
                context['error'] = "Internal Server Error"
        else:
            context['error'] = 'No project found!'
        return render(request, template_name=self.template_name, context=context)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(
                to="/login/?next=/search/?projectId={}".format(settings.LOGIN_URL, request.POST.get('projectId', None)))
        context = {}
        try:
            annotator = Annotator.objects.filter(user=request.user).first()
        except Exception as e:
            context["error"] = "Internal Server Error"
        if annotator is None:
            context['error'] = "You are not an annotator! This job is only available for annotators. " \
                               "Reviewers and project owners can see outcomes."
            return JsonResponse(context)
        # context['annotator'] = annotator
        projectId = request.POST.get("projectId", None)
        logger.info(projectId)
        if projectId is not None:
            try:
                job = Job.objects.filter(id=projectId, is_completed=False).first()
                if job is None:
                    context['error'] = 'No project found!'
                    return JsonResponse(context)
                # search
                cc = bool(request.POST.get('cc', True))
                hd = bool(request.POST.get('hd', False))
                duration = "any"
                if bool(request.POST.get('long', False)):
                    duration = 'long'
                keywords = request.POST.get('keywords', '').split(',')
                results = []
                for keyword in keywords:
                    videos = self._search_youtube(keyword=keyword,
                                                  user=request.user,
                                                  job=job,
                                                  cc=cc, hd=hd, duration=duration)
                    results.extend(videos)
                context['videos'] = results
            except Exception as e:
                context['error'] = "Internal Server Error"
                logger.error(e)
        else:
            context['error'] = 'No project found!'
        return JsonResponse(context)
