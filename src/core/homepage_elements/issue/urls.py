from django.conf.urls import url
from core.homepage_elements.issue import views

urlpatterns = [
    # Featured Articles
    url(r'^manager/currentissue/$', views.current_issue, name='current_issue_setup'),
]
