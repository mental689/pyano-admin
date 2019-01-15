from django.urls import path
from vatic.views import IndexView, VATICDownloadView, AddJobGroupView, DetailJobGroupView, JobView, InvitationView, \
    ReviewerInviteView, ReviewJobView
from vatic.irvine import VATICJobView, VATICBoxesForJobView, VATICSaveJobView, VATICValidateJobView


urlpatterns = [
    path('', IndexView.as_view(), name='vatic'),
    path('getjob/', VATICJobView.as_view(), name='getjob'),
    path('getboxesforjob/', VATICBoxesForJobView.as_view(), name='getboxesforjob'),
    path('validatejob/', VATICValidateJobView.as_view(), name='validatejob'),
    path('savejob/', VATICSaveJobView.as_view(), name='savejob'),
    path('download/', VATICDownloadView.as_view(), name='download'),
    path('group/add/', AddJobGroupView.as_view(), name='jobgroup_add'),
    path('group/detail/', DetailJobGroupView.as_view(), name='jobgroup_detail'),
    path('job/', JobView.as_view(), name='job'),
    path('review/', ReviewJobView.as_view(), name='review'),
    path('notify/', InvitationView.as_view(), name='invitations'),
    path('invite/', ReviewerInviteView.as_view(), name='invite_reviewer'),
]