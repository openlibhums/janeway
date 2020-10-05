from django.views.generic.list import BaseListView
from django.views.generic.base import TemplateResponseMixin
from django.views.generic import ListView

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
