from django.contrib import admin

from vatic.models import *

# Register your models here.


admin.site.register(JobGroup)
admin.site.register(Job)
admin.site.register(Video)
admin.site.register(Assignment)
admin.site.register(Label)
admin.site.register(Box)
admin.site.register(BoxAttribute)
admin.site.register(Attribute)
admin.site.register(AttributeAnnotation)
admin.site.register(Segment)
admin.site.register(Path)
admin.site.register(TrainingTest)