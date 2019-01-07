from django.urls import path
from worker.views.auth import AddWorkerView, ProfileView
from worker.views.jobs import ListJobView, JobDetailView
from worker.views.survey import SurveyReviewView, SurveyVideoReviewView
from worker.views.reviews import InvitationListView
urlpatterns = [
    path('', ListJobView.as_view(), name='index'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('register/', AddWorkerView.as_view(), name='add_worker'),
    path('jobs/', ListJobView.as_view(), name='jobs_worker'),
    path('job/', JobDetailView.as_view(), name='detail_job'),
    path('survey/review/<int:sid>/', SurveyReviewView.as_view(), name='review_survey'),
    path('survey/review/<int:sid>/<int:vid>/', SurveyVideoReviewView.as_view(), name='review_survey_video'),
    path('invitation/list/', InvitationListView.as_view(), name='invitations'),
]