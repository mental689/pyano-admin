from django.urls import path
from django.conf.urls import url
from vatic.views import IndexView
from vatic.irvine import VATICJobView, VATICBoxesForJobView, VATICSaveJobView, VATICValidateJobView


urlpatterns = [
    url(r'^', IndexView.as_view(), name='vatic'),
    url(r'^getjob', VATICJobView.as_view(), name='getjob'),
    url(r'^getboxesforjob', VATICBoxesForJobView.as_view(), name='getboxesforjob'),
    url(r'^validatejob', VATICValidateJobView.as_view(), name='validatejob'),
    url(r'^savejob', VATICSaveJobView.as_view(), name='savejob')
]