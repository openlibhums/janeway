from django.conf.urls import url
from core.homepage_elements.featured import views

urlpatterns = [
    # Featured Articles
    url(r'^manager/$', views.featured_articles, name='featured_articles_setup'),
    url(r'^manager/order/$', views.featured_articles_order, name='featured_order'),
]
