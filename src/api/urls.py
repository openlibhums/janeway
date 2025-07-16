from django.urls import re_path, include

from rest_framework import routers
from rest_framework.schemas import get_schema_view

from api import views
from api.oai import views as oai_views

router = routers.DefaultRouter()
router.register(r"accountrole", views.AccountRoleViewSet, "accountrole")
router.register(r"journals", views.JournalViewSet, "journal")
router.register(r"issues", views.IssueViewSet, "issue")
router.register(r"articles", views.ArticleViewSet, "article")
router.register(r"preprints", views.PreprintViewSet, "preprint")
router.register(r"licences", views.LicenceViewSet, "licence")
router.register(r"keywords", views.KeywordsViewSet, "keywords")
router.register(r"accounts", views.AccountViewSet, "accounts")

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    re_path(r"^", include(router.urls)),
    re_path(r"^oai/$", oai_views.oai_view_factory, name="OAI_list_records"),
    re_path(r"^kbart/$", views.kbart, name="kbart"),
    re_path(r"^kbart/csv$", views.kbart_csv, name="kbart"),
    re_path(
        r"^schema/$",
        get_schema_view(
            title="Janeway API", description="API for Janeway", version="0.0.1"
        ),
        name="openapi-schema",
    ),
    re_path(r"^swagger_ui/$", views.swagger_ui, name="swagger_ui"),
    re_path(r"^redoc/$", views.redoc, name="redoc"),
]
