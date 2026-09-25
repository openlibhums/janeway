from django.urls import path
from core.homepage_elements.featured import views

urlpatterns = [
    # Featured Articles
    path("manager/", views.featured_articles, name="featured_articles_setup"),
    path("manager/order/", views.featured_articles_order, name="featured_order"),
]
