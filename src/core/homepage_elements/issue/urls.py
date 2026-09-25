from django.urls import path
from core.homepage_elements.issue import views

urlpatterns = [
    # Featured Articles
    path("manager/currentissue/", views.current_issue, name="current_issue_setup"),
]
