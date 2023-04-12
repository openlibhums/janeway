from django.urls import re_path
from core.homepage_elements.carousel import views

urlpatterns = [
    re_path(r'^settings/$', views.settings_carousel, name='carousel_settings'),
]
