from django.urls import path
from worker.views.auth import AddWorkerView, ProfileView
from worker.views.jobs import ListJobView, JobDetailView
urlpatterns = [
    path('', ProfileView.as_view(), name='index'),
    path('register/', AddWorkerView.as_view(), name='add_worker'),
    path('jobs/', ListJobView.as_view(), name='jobs_worker'),
    path('job/', JobDetailView.as_view(), name='detail_job')
]