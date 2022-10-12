from django.urls import re_path
from core.homepage_elements.issue import views

urlpatterns = [
    # Featured Articles
    re_path(r'^manager/currentissue/$', views.current_issue, name='current_issue_setup'),
]
