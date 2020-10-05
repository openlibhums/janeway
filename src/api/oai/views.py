"""
A django implementation of the OAI-PMH interface
"""
from django.utils import timezone

from api.oai.base import OAIModelView
from submission import models as submission_models


def oai_view_factory(request, *args, **kwargs):
    verb = request.GET.get("verb")
    view = ROUTES.get(verb)
    return view(request, *args, **kwargs)


class OAIListRecords(OAIModelView):
    template_name = "apis/OAI_ListRecords.xml"
    queryset = submission_models.Article.objects.all()

    def filter_by_journal(self, qs):
        if self.request.journal:
            return qs.filter(journal=self.request.journal)
        return qs

    def filter_is_published(self, qs):
        return qs.filter(
            stage=submission_models.STAGE_PUBLISHED,
            date_published__lte=timezone.now(),
        )


ROUTES = {
    "ListRecords": OAIListRecords.as_view(),
}
