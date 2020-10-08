from urllib.parse import (
    quote,
    unquote,
    urlencode,
    parse_qsl,
)

from dateutil import parser as date_parser
from django.views.generic.list import BaseListView
from django.views.generic.base import TemplateResponseMixin

from api.oai import exceptions


class OAIModelView(BaseListView, TemplateResponseMixin):
    """ Base class for OAI views generated from model Querysets """
    content_type = "application/xml"
    # `oai_dc` is the only required metadata format by OAI spec
    metadata_formats = {"oai_dc"}

    def get_queryset(self):
        qs = super().get_queryset()
        filtered = self.apply_filters(qs)
        return filtered

    def get(self, *args, **kwargs):
        self.validate_metadata_format()
        return super().get(*args, **kwargs)

    def apply_filters(self, qs):
        for attr in (a for a in dir(self) if a.startswith("filter_")):
            filter_ = getattr(self, attr)
            qs = filter_(qs)
        return qs

    def validate_metadata_format(self):
        prefix = self.request.GET.get("metadataPrefix")
        if prefix and prefix not in self.metadata_formats:
            raise exceptions.OAIUnsupportedMetadataFormat()


class OAIPaginationMixin():
    page_kwarg = "token_page"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._decoded_token = {}

    def get_context_data(self, **kwargs):
        self.kwargs["token_page"] = self.page
        context = super().get_context_data(**kwargs)
        if context["is_paginated"] and context["page_obj"].has_next():
            context["resumption_token"] = self.encode_token(context)
            total_items = context["paginator"].count
            if total_items == 0:
                raise exceptions.OAINoRecordsMatch()
            context["total"] = total_items
        return context

    def get_token_context(self, context):
        return {
                "page": context["page_obj"].next_page_number(),
        }

    def encode_token(self, context):
        return quote(urlencode(self.get_token_context(context)))

    def _decode_token(self):
        if not self._decoded_token and "resumptionToken" in self.request.GET:
            raw_token = self.request.GET["resumptionToken"]
            try:
                self._decoded_token = dict(parse_qsl(unquote(raw_token)))
            except ValueError:
                raise exceptions.OAIBadToken()

    @property
    def page(self):
        self._decode_token()
        if self._decoded_token:
            return int(self._decoded_token.get("page", 1))
        return None


class OAIDateFilterMixin(OAIPaginationMixin):

    def filter_by_date_range(self, qs):
        try:
            if self.from_:
                from_date = date_parser.parse(self.from_)
                qs = qs.filter(date_published__gte=from_date)
            if self.until:
                until_date = date_parser.parse(self.until)
                qs = qs.filter(date_published__lte=until_date)
            return qs
        except ValueError:
            raise exceptions.OAIBadArgument()

    def get_token_context(self, context):
        # We need to consider previous filters when generating the new token
        token_context = super().get_token_context(context)
        if self.until:
            token_context["until"] = self.until
        elif "until" in self.request.GET:
            token_context["until"] = self.request.GET["until"]
        if self.from_:
            token_context["from"] = self.from_
        elif "from" in self.request.GET:
            token_context["from"] = self.request.GET["from"]
        return token_context

    @property
    def from_(self):
        self._decode_token()
        if self._decoded_token and "from" in self._decoded_token:
            return self._decoded_token.get("from")
        else:
            return self.request.GET.get("from")

    @property
    def until(self):
        date_str = None
        self._decode_token()
        if self._decoded_token and "until" in self._decoded_token:
            date_str = self._decoded_token.get("until")
        else:
            date_str = self.request.GET.get("until")
        return date_str


class OAIPagedModelView(OAIDateFilterMixin, OAIModelView):
    pass
