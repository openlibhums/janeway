from django.urls import path
from core.homepage_elements.carousel import views

urlpatterns = [
    path("settings/", views.settings_carousel, name="carousel_settings"),
]
