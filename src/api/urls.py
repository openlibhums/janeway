from django.conf.urls import url, include

from rest_framework import routers

from api import views
from api.oai import views as oai_views

router = routers.DefaultRouter()
router.register(r'accountrole', views.AccountRoleViewSet, 'accountrole')
router.register(r'journals', views.JournalViewSet, 'journal')
router.register(r'issues', views.IssueViewSet, 'issue')
router.register(r'articles', views.ArticleViewSet, 'article')
router.register(r'licences', views.LicenceViewSet, 'licence')
router.register(r'keywords', views.KeywordsViewSet, 'keywords')

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^oai/$', oai_views.oai_view_factory, name='OAI_list_records'),
    url(r'^kbart/$', views.kbart, name='kbart'),
    url(r'^kbart/csv$', views.kbart_csv, name='kbart'),
]
