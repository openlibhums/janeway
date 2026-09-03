from django.urls import path
from core.homepage_elements.news import views

urlpatterns = [
    # Featured Articles
    path("", views.news_config, name="news_config"),
]
