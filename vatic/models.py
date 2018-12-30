import logging

import vision
from django.db import models
from django.utils.translation import ugettext_lazy as _
from survey import models as surveys
from vision.track.interpolation import LinearFill

from employer.models import Employer, Credit
from vatic.tools.qa import tolerable
from worker.models import Annotator


# Create your models here.


class Video(models.Model):
    slug = models.CharField(max_length=250)
    width = models.IntegerField()
    height = models.IntegerField()
    totalframes = models.IntegerField()
    location = models.CharField(max_length=250)
    skip = models.IntegerField(default=0, null=False)
    perobjectbonus = models.FloatField(default=0)
    completionbonus = models.FloatField(default=0)
    pyano_video = models.ForeignKey(surveys.Video, related_name='videos', null=True, on_delete=models.CASCADE)
    isfortraining = models.BooleanField(default=False)
    blowradius = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @staticmethod
    def getframepath(frame, base=None):
        l1 = int(frame / 10000)
        l2 = int(frame / 100)
        path = "{0}/{1}/{2}.jpg".format(l1, l2, frame)
        if base is not None:
            path = "{0}/{1}".format(base, path)
        return path

    def cost(self):
        cost = 0
        for segment in self.segments.all():
            cost += segment.cost
        return cost

    def numjobs(self):
        count = 0
        for segment in self.segments.all():
            for job in segment.jobs.all():
                count += 1
        return count

    def numcompleted(self):
        count = 0
        for segment in self.segments.all():
            for job in segment.jobs.all():
                if job.completed:
                    count += 1
        return count


class Label(models.Model):
    text = models.CharField(max_length=250)
    video = models.ForeignKey(Video, related_name='labels', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Attribute(models.Model):
    text = models.CharField(max_length=250)
    label = models.ForeignKey(Label, related_name='attributes', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text


class Segment(models.Model):
    """
    The original  uses a segment as unit of jobs.
    """
    video = models.ForeignKey(Video, related_name='segments', on_delete=models.CASCADE)
    start = models.IntegerField(null=False)
    stop = models.IntegerField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def paths(self):
        paths = []
        for job in self.jobs.all():
            if job.useful:
                paths.extend(job.paths)
        return paths

    def cost(self):
        cost = 0
        for job in self.jobs.all():
            cost += job.cost
        return cost


class JobGroup(models.Model):
    title = models.CharField(max_length=250, null=False)
    description = models.CharField(max_length=250, null=False)
    duration = models.IntegerField(null=False)
    cost = models.ForeignKey(Credit, related_name='jobgroups', on_delete=models.CASCADE)
    keywords = models.CharField(max_length=250, null=False)
    height = models.IntegerField(null=False, default=650)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Job(models.Model):
    segment = models.ForeignKey(Segment, related_name='jobs', on_delete=models.CASCADE, help_text=_('Segment'))
    istraining = models.BooleanField(default=False, help_text=_('Is this job for training?'))
    group = models.ForeignKey(JobGroup, related_name='jobs', on_delete=models.CASCADE, help_text=_('Group'))
    completed = models.BooleanField(default=False, help_text=_('Is the job completed?'))
    paid = models.BooleanField(default=False, help_text=_('Is the annotator paid?'))
    published = models.BooleanField(default=False, help_text=_('Is this published?'))
    ready = models.BooleanField(default=False, help_text=_('Whether if the job is ready.'))
    bonus = models.FloatField(default=0, help_text=_('Bonus'))
    uuid = models.CharField(_("Job unique identifier"), max_length=255, unique=True, help_text=_('UUID'))
    training_overlap = models.FloatField(default=0.25, null=False)
    training_tolerance = models.FloatField(default=0.2, null=False)
    training_mistakes = models.IntegerField(default=0, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def getpage(self):
        return "?id={0}".format(self.id)

    def markastraining(self):
        """
        Marks this job as the result of a training run. This will automatically
        swap this job over to the training video and produce a replacement.
        """
        replacement = Job(segment=self.segment, group=self.group)
        self.segment = self.segment.video.trainwith.segments[0]
        self.group = self.segment.jobs[0].group
        self.istraining = True

        logging.debug("Job is now training and replacement built")

        return replacement

    def invalidate(self):
        """
        Invalidates this path because it is poor work. The new job will be
        respawned automatically for different workers to complete.
        """
        self.useful = False
        # is this a training task? if yes, we don't want to respawn
        if not self.istraining:
            return Job(segment=self.segment, group=self.group)

    def trainingjob(self):
        train_of = TrainingOf.objects.filter(video_test=self.segment.video)
        if len(train_of) > 0:
            return train_of[0]
        return None

    def validator(self):
        return tolerable(self.training_overlap, self.training_tolerance, self.training_mistakes)

    def cost(self):
        if not self.completed:
            return 0
        return self.group.cost.point + self.bonus

    def __iter__(self):
        return self.paths


class Path(models.Model):
    job = models.ForeignKey(Job, related_name='paths', on_delete=models.CASCADE)
    label = models.ForeignKey(Label, related_name='paths', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    interpolatecache = None

    def getboxes(self, interpolate=False, bind=False, label=False):
        result = [x.getbox() for x in self.boxes.all()]
        result.sort(key=lambda x: x.frame)
        if interpolate:
            if not self.interpolatecache:
                self.interpolatecache = LinearFill(result)
            result = self.interpolatecache

        if bind:
            result = Path.bindattributes(self.attributes.all(), result)

        if label:
            for box in result:
                box.attributes.insert(0, self.label.text)

        return result

    def bindattributes(self, attributes, boxes):
        attributes = sorted(attributes, key=lambda x: x.frame)

        byid = {}
        for attribute in attributes:
            if attribute.attributeid not in byid:
                byid[attribute.attributeid] = []
            byid[attribute.attributeid].append(attribute)

        for attributes in byid.values():
            for prev, cur in zip(attributes, attributes[1:]):
                if prev.value:
                    for box in boxes:
                        if prev.frame <= box.frame < cur.frame:
                            if prev.attribute not in box.attributes.all():
                                box.attributes.append(prev.attribute)
            last = attributes[-1]
            if last.value:
                for box in boxes:
                    if last.frame <= box.frame:
                        if last.attribute not in box.attributes:
                            box.attributes.append(last.attribute)

        return boxes

    def __repr__(self):
        return "<Path {0}>".format(self.id)


class AttributeAnnotation(models.Model):
    path = models.ForeignKey(Path, related_name='attributes', on_delete=models.CASCADE)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    frame = models.IntegerField()
    value = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __repr__(self):
        return ("AttributeAnnotation(pathid = {0}, "
                "attributeid = {1}, "
                "frame = {2}, "
                "value = {3})").format(self.path.id,
                                       self.attribute.id,
                                       self.frame,
                                       self.value)


class Box(models.Model):
    path = models.ForeignKey(Path, related_name='boxes', on_delete=models.CASCADE)
    xtl = models.IntegerField()
    ytl = models.IntegerField()
    xbr = models.IntegerField()
    ybr = models.IntegerField()
    frame = models.IntegerField()
    occluded = models.BooleanField(default=False)
    outside = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def getbox(self):
        return vision.Box(self.xtl, self.ytl, self.xbr, self.ybr,
                          self.frame, self.outside, self.occluded, 0)


class BoxAttribute(models.Model):
    box = models.ForeignKey(Box, related_name='boxes2attributes', on_delete=models.CASCADE)
    attribute = models.ForeignKey(Box, related_name='attributes2boxes', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class TrainingTest(models.Model):
    video_test = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='testvideos')
    video_train = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='trainvideos')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Assignment(models.Model):
    worker = models.ForeignKey(Annotator, on_delete=models.CASCADE, related_name='assignments')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='assignments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Bid(models.Model):
    candidate = models.ForeignKey(Annotator, on_delete=models.CASCADE, related_name='bids')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='bids')
    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(Employer, on_delete=models.CASCADE, related_name='approved_bids', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
