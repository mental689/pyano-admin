"""
This file contains re-implementation of some methods in VATIC annotation tool from Irvine California.
"""
import json

from django.http import JsonResponse
from django.views import View

from vatic.video import *

import logging
logger = logging.getLogger(__name__)


class VATICJobView(View):  # equal to getjob in VATIC
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Login is required.'})
        id = request.GET.get('id')
        verified = request.GET.get('verified')
        logger.debug('id: {}'.format(id))
        job = Job.objects.filter(id=id).first()
        if job is not None:
            logger.debug("Found job {0}".format(job.id))
            # find if a solution is assigned to this user and this job
            solution = Solution.objects.filter(job=job, submitter__user=request.user).first()
            annotator = Annotator.objects.filter(user=request.user).first()
            employer = Employer.objects.filter(user=request.user).first()
            if solution is None and employer is None:
                solution = Solution()
                solution.job = job
                if annotator is None:
                    return JsonResponse({'error': 'No annotator is found.'})
                solution.submitter = annotator
                try:
                    solution.save()
                except Exception as e:
                    logger.error(e)
                    return JsonResponse({'error': 'Internal Server Error. We cannot process your request now.'})

            v = job.segment.video
            train_of = TrainingTest.objects.filter(video_test=v)
            if int(verified) and len(train_of) > 0:
                # swap segment with the training segment
                training = True
                segment = train_of[0].segments[0]
                logger.debug("Swapping actual segment with training segment")
            else:
                training = False
                segment = job.segment

            video = segment.video
            labels = dict((l.id, l.text) for l in video.labels.all())

            attributes = {}
            for label in video.labels.all():
                attributes[label.id] = dict((a.id, a.text) for a in label.attributes.all())

            logger.debug("Giving user frames {0} to {1} of {2}".format(video.slug,
                                                                        segment.start,
                                                                        segment.stop))

            result = {"start": segment.start,
                      "stop": segment.stop,
                      "slug": video.slug,
                      "width": video.width,
                      "height": video.height,
                      "skip": video.skip,
                      "perobject": video.perobjectbonus,
                      "completion": video.completionbonus,
                      "blowradius": video.blowradius,
                      "jobid": job.id,
                      # "solutionid": solution.id,
                      "training": int(training),
                      "labels": labels,
                      "attributes": attributes}
            return JsonResponse(result)
        return JsonResponse({'error': 'No job found.', 'request': request.GET})


class VATICBoxesForJobView(View):  # getboxesforjob
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'No permission.'})
        id = request.GET.get('id')
        employer = Employer.objects.filter(user=request.user).first()
        result = []
        if employer is None:
            solution = Solution.objects.filter(job__id=id, submitter__user=request.user).first()
            if solution is not None:
                for path in solution.paths.all():
                    attrs = [(x.attribute.id, x.frame, x.value) for x in path.attributes.all()]
                    result.append({"label": path.label.id,
                                   "boxes": [tuple(x) for x in path.getboxes()],
                                   "attributes": attrs})
        else:
            # Owners of a project can see all solutions
            solutions = Solution.objects.filter(job__id=id).all()
            for solution in solutions:
                for path in solution.paths.all():
                    attrs = [(x.attribute.id, x.frame, x.value) for x in path.attributes.all()]
                    result.append({"label": path.label.id,
                                   "boxes": [tuple(x) for x in path.getboxes()],
                                   "attributes": attrs})
        return JsonResponse({'result': result})


class VATICSaveJobView(View):  # savejob
    def readpaths(self, solution, tracks):
        logging.debug("Reading {0} total tracks".format(len(tracks)))
        for track in tracks:
            if len(track) < 3: continue
            label, track, attributes = track[0], track[1], track[2]
            path = Path()
            path.solution = solution
            labels = Label.objects.filter(id=label)
            if len(labels) > 0:
                path.label = labels[0]
                path.save()
            else:
                logger.debug("No such label with ID {0}".format(label))
                continue

            logger.debug("Received a {0} track".format(path.label.text))

            visible = False
            for frame, userbox in track.items():
                box = Box()
                box.path = path
                box.xtl = max(int(userbox[0]), 0)
                box.ytl = max(int(userbox[1]), 0)
                box.xbr = max(int(userbox[2]), 0)
                box.ybr = max(int(userbox[3]), 0)
                box.occluded = int(userbox[4])
                box.outside = int(userbox[5])
                box.frame = int(frame)
                if not box.outside:
                    visible = True

                logger.debug("Received box {0}".format(str(box.getbox())))
                box.save()

            if not visible:
                logging.warning("Received empty path! Skipping")
                continue

            for attributeid, timeline in attributes.items():
                attributes = Attribute.objects.filter(id=attributeid)
                if len(attributes) == 0: continue
                else: attribute = attributes[0]
                for frame, value in timeline.items():
                    aa = AttributeAnnotation()
                    aa.attribute = attribute
                    aa.frame = frame
                    aa.value = value
                    aa.path = path
                    aa.save()
                    path.save()

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Login is required.'})
        id = request.POST.get('id')
        tracks = json.loads(request.POST.get('tracks'))
        solution = Solution.objects.filter(job__id=id, submitter__user=request.user).first()
        annotator = Annotator.objects.filter(user=request.user).first()
        if annotator is None:
            return JsonResponse({'error': 'No annotator is found.'}) # Only annotators can do the jobs.
        if solution is not None:
            # assignment = Assignment.objects.filter(worker=request.user, job=solution.job).first()
            # if assignment is None:
            #     return JsonResponse({'error': 'User is not assigned for this job.'})
            if solution.job.completed:
                return JsonResponse({'error': 'Job is completed. You cannot submit after a job is finalized.'})
            for path in solution.paths.all():
                path.delete()
            self.readpaths(solution, tracks)
            solution.save()
        return JsonResponse({})


class VATICValidateJobView(View):
    """
    validatejob: to validate whether if annotator did a training job good or not?
    This class is majorly for training.
    """
    def readpaths(self, tracks):
        paths = []
        logging.debug("Reading {0} total tracks".format(len(tracks)))
        for track in tracks:
            if len(track) < 3: continue
            label, track, attributes = track[0], track[1], track[2]
            path = Path()
            labels = Label.objects.filter(id=label)
            if len(labels) > 0:
                path.label = labels[0]
            else:
                logging.debug("No such label with ID {0}".format(label))
                continue

            logger.debug("Received a {0} track".format(path.label.text))

            visible = False
            for frame, userbox in track.items():
                box = Box()
                box.path = path
                box.xtl = max(int(userbox[0]), 0)
                box.ytl = max(int(userbox[1]), 0)
                box.xbr = max(int(userbox[2]), 0)
                box.ybr = max(int(userbox[3]), 0)
                box.occluded = int(userbox[4])
                box.outside = int(userbox[5])
                box.frame = int(frame)
                if not box.outside:
                    visible = True

                logger.debug("Received box {0}".format(str(box.getbox())))

            if not visible:
                logger.warning("Received empty path! Skipping")
                continue

            for attributeid, timeline in attributes.items():
                attribute = Attribute.objects.filter(id=attributeid)
                for frame, value in timeline.items():
                    aa = AttributeAnnotation()
                    aa.attribute = attribute
                    aa.frame = frame
                    aa.value = value
                    aa.path = path
            paths.append(path)
        return paths

    def post(self, request, *args, **kwargs):
        id = request.POST.get('id')
        tracks = json.loads(request.POST.get('tracks'))
        paths = self.readpaths(tracks)
        solution = Solution.objects.filter(id=id).first()
        matched = False
        if solution is not None:
            matched = solution.job.validator(paths, solution.paths)
        return JsonResponse({'status': matched})

