from django.conf.urls import url, include

from rest_framework import routers

from api import views

router = routers.DefaultRouter()
router.register(r'accountrole', views.AccountRoleViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^oai/$', views.oai, name='OAI_list_records'),
]
