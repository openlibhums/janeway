from django.conf.urls import url
from core.homepage_elements.carousel import views

urlpatterns = [
    url(r'^settings/$', views.settings_carousel, name='carousel_settings'),
]
