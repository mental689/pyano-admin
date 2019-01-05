from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth import forms as auth_forms

from employer.views.auth import ProfileView, AddEmployerView
from employer.views.common import IndexView
from employer.views.topics import AddTopicView, TopicListView, TopicDetailView, ChangeTopicView
from employer.views.jobs import AddJobView, ListJobView, DetailJobView, ChangeJobView
from employer.views.surveys import AddSurveyView, SurveyDetailView, DeleteSurveyView, EditSurveyView

urlpatterns = [
    path('', IndexView.as_view(), name='home'),
    path('accounts/profile/', ProfileView.as_view(), name='profile'),
    path('employer/register/', AddEmployerView.as_view(), name='add_employer'),
    path('login/', auth_views.LoginView.as_view(template_name='common/login.html',
                                                authentication_form=auth_forms.AuthenticationForm), name='login'),
    path('logout/',auth_views.LogoutView.as_view(), name='logout'),
    path('topic/add/', AddTopicView.as_view(), name='add_topic'),
    path('topic/list/', TopicListView.as_view(), name='list_topic'),
    path('topic/details/', TopicDetailView.as_view(), name='detail_topic'),
    path('topic/edit/', ChangeTopicView.as_view(), name='change_topic'),
    path('job/add/', AddJobView.as_view(), name='add_jobic'),
    path('job/list/', ListJobView.as_view(), name='list_job'),
    path('job/details/', DetailJobView.as_view(), name='detail_job'),
    path('job/edit/', ChangeJobView.as_view(), name='change_job'),
    path('survey/add/', AddSurveyView.as_view(), name='add_survey'),
    path('survey/detail/', SurveyDetailView.as_view(), name='detail_survey'),
    path('survey/delete/', DeleteSurveyView.as_view(), name='delete_survey'),
    path('survey/edit/', EditSurveyView.as_view(), name='edit_survey'),
]
