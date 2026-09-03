from django.urls import path
from core.homepage_elements.popular import views

urlpatterns = [
    # Featured Articles
    path("manager/", views.featured_articles, name="popular_articles_setup"),
]
