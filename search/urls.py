from django.urls import path
from search.views import KeywordSearchJSONOutcomeView, KeywordSearchView
urlpatterns = [
    path('ks/outcome/', KeywordSearchJSONOutcomeView.as_view(), name='search_ks_outcome'),
    path('', KeywordSearchView.as_view(), name='search_index')
]