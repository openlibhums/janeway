from urllib.parse import (
    quote,
    unquote,
    urlencode,
    parse_qsl,
)

from dateutil import parser as date_parser
from django.views.generic.list import BaseListView
from django.views.generic.base import TemplateResponseMixin


class OAIModelView(BaseListView, TemplateResponseMixin):
    """ Base class for OAI views generated from model Querysets """
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


class OAIPaginationMixin():

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._decoded_token = {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context["is_paginated"] and context["page_obj"].has_next():
            context["resumption_token"] = self.encode_token(context)
            context["total"] = context["paginator"].count
        return context

    def get_token_context(self, context):
        return {
                "page": context["page_obj"].next_page_number(),
                "until": self.request.GET.get("until"),
                "from": self.request.GET.get("from"),
        }

    def encode_token(self, context):
        return quote(urlencode(self.get_token_context(context)))

    def _decode_token(self):
        if not self._decoded_token and "resumptionToken" in self.request.GET:
            raw_token = self.request.GET["resumptionToken"]
            self._decoded_token = dict(parse_qsl(unquote(raw_token)))

    @property
    def from_(self):
        self._decode_token()
        if self._decoded_token:
            return self._decoded_token.get("from")
        else:
            return self.request.GET.get("from")

    @property
    def until(self):
        self._decode_token()
        if self._decoded_token:
            return self._decoded_token.get("until")
        else:
            return self.request.GET.get("until")

    @property
    def page(self):
        self._decode_token()
        return self._decoded_token["from"]

    def filter_by_range(self, qs):
        if self.from_:
            from_date = date_parser.parse(self._from)
            qs = qs.filter(date_published__gte=from_date)
        if self.until:
            until_date = date_parser.parse(self.until)
            qs = qs.filter(date_published__gte=until_date)
        return qs


class OAIPagedModelView(OAIPaginationMixin, OAIModelView):
    pass
