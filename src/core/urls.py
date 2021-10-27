__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView
from django.conf import settings
from django.views.static import serve

from press import views as press_views
from core import error_views
from utils.logger import get_logger

logger = get_logger(__name__)

include('events.registration')

urlpatterns = [
    url(r'^$', press_views.index, name='website_index'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^summernote/', include('django_summernote.urls')),
    url(r'', include('core.include_urls')),
]

try:
    if settings.DEBUG or settings.IN_TEST_RUNNER:
        import debug_toolbar

        urlpatterns += [
            url(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
            url(r'^404/$', error_views.handler404),
            url(r'^500/$', error_views.handler500),
            url(r'^__debug__/', include(debug_toolbar.urls)),
        ]
except AttributeError:
    pass


if settings.HIJACK_USERS_ENABLED:
    try:
        urlpatterns += [
            url(r'^control_user/', include('hijack.urls', namespace='hijack')),
        ]
    except AttributeError:
        logger.warning('Could not import Hijack URLs.')

handler404 = 'core.error_views.handler404'
handler500 = 'core.error_views.handler500'
