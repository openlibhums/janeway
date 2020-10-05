"""
An implementation of the OAI-PMH interface
"""
from django.views.generic.list import BaseListView
from django.views.generic.base import TemplateResponseMixin
from django.views.generic import ListView

from submission import models as submission_models


def oai_view_factory(request, *args, **kwargs):
    verb = request.GET.get("verb")
    view = ROUTES.get(verb)
    return view(request, *args, **kwargs)


class OAIModelView(BaseListView, TemplateResponseMixin):
    content_type = "application/xml"

    def get_queryset(self):
        qs = super().get_queryset()
        filtered = self.apply_filters(qs)
        return filtered

    def apply_filters(self, qs):
        for attr in (a for a in dir(self) if a.startswith("filter_")):
            filter_ = getattr(self, attr)
            qs = filter_(qs)
        return qs


class OAIListRecords(OAIModelView):
    template_name = "apis/OAI.xml"
    queryset = submission_models.Article.objects.all()

    def filter_by_journal(self, qs):
        if self.request.journal:
            return qs.filter(journal=self.request.journal)
        return qs


ROUTES = {
    "ListRecords": OAIListRecords.as_view(),
}
