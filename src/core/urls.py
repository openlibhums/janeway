__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.conf.urls import include, url
from django.urls import path, re_path
from django.contrib import admin
from django.views.generic import TemplateView
from django.conf import settings
from django.views.static import serve

from press import views as press_views

include('events.registration')

urlpatterns = [
    re_path(r'^$', press_views.index, name='website_index'),
    re_path(r'^admin/', admin.site.urls),
    path('summernote/', include('django_summernote.urls')),
    path('', include('core.include_urls')),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        url(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
        url(r'^404/$', TemplateView.as_view(template_name='404.html')),
        url(r'^500/$', TemplateView.as_view(template_name='500.html')),
        path('__debug__/', include(debug_toolbar.urls)),
    ]
