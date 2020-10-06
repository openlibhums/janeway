"""
A django implementation of the OAI-PMH interface
"""
from django.utils import timezone

from api.oai.base import OAIPagedModelView
from submission import models as submission_models

# We default `verb` to ListRecords for backwards compatibility.
DEFAULT_ENDPOINT = "ListRecords"

def oai_view_factory(request, *args, **kwargs):
    """ Maps an incoming OAI request to a django CB view
    The OAI protocol uses a querystring parameter (verb) to determine
    the resource being queried. This is not supported by Django's URL
    router, so we do our own mapping here and pass this factory to the
    url constructor instead of a view. As a result, all the OAI endpoints
    will have the same django view name.
    """
    verb = request.GET.get("verb", DEFAULT_ENDPOINT)
    view = ROUTES.get(verb)
    return view(request, *args, **kwargs)


class OAIListRecords(OAIPagedModelView):
    template_name = "apis/OAI_ListRecords.xml"
    queryset = submission_models.Article.objects.all()
    paginate_by = 50

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
