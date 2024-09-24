from django.urls import re_path, include
from django.conf import settings

from rest_framework import routers
from rest_framework.schemas import get_schema_view
from rest_framework.urlpatterns import format_suffix_patterns

from api import views
from api.oai import views as oai_views

router = routers.DefaultRouter()
router.register(r'accountrole', views.AccountRoleViewSet, 'accountrole')
router.register(r'journals', views.JournalViewSet, 'journal')
router.register(r'issues', views.IssueViewSet, 'issue')
router.register(r'articles', views.ArticleViewSet, 'article')

router.register(r'licences', views.LicenceViewSet, 'licence')
router.register(r'keywords', views.KeywordsViewSet, 'keywords')
router.register(r'accounts', views.AccountViewSet, 'accounts')

router.register(r'preprints', views.PreprintViewSet, 'repository_preprints')
router.register(r'repository_licenses', views.PreprintLicenses, 'repository_licenses')
router.register(r'repository_fields', views.RepositoryFields, 'repository_fields')
router.register(r'preprint_files', views.PreprintFiles, 'repository_preprint_files')
router.register(r'user_preprints', views.UserPreprintsViewSet, 'repository_user_preprints')
router.register(r'repository_subjects', views.RepositorySubjects, 'repository_preprint_subjects')
router.register(r'published_preprints', views.PublishedPreprintViewSet, 'repository_published_preprint')
router.register(r'version_queue', views.RepositoryVersionQueue, 'repository_version_queue')
router.register(r'user_info', views.UserInfo, 'api_user_info')

if settings.API_ENABLE_SUBMISSION_ACCOUNT_SEARCH:
    router.register(
        r'submission_account_search',
        views.SubmissionAccountSearch,
        'submission_account_search',
    )
    router.register(
        r'register',
        views.RegisterAccount,
        'register_account',
    )
    router.register(
        r'activate',
        views.ActivateAccount,
        'activate_account',
    )

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    re_path(r'^', include(router.urls)),
    re_path(r'^oai/$', oai_views.oai_view_factory, name='OAI_list_records'),
    re_path(r'^kbart/$', views.kbart, name='kbart'),
    re_path(r'^kbart/csv$', views.kbart_csv, name='kbart'),
    re_path(r'^schema/$', get_schema_view(title="Janeway API", description="API for Janeway", version="0.0.1"), name='openapi-schema'),
    re_path(r'^swagger_ui/$', views.swagger_ui, name='swagger_ui'),
    re_path(r'^redoc/$', views.redoc, name='redoc'),
]
