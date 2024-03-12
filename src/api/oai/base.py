from urllib.parse import (
    quote,
    unquote,
    urlencode,
    parse_qsl,
)
from datetime import datetime

from dateutil import parser as date_parser
from django.views.generic.list import BaseListView
from django.views.generic.base import View, TemplateResponseMixin
from django.utils.timezone import make_aware, utc

from api.oai import exceptions
from utils.http import allow_mutating_GET


metadata_formats = [
    {
        'prefix': 'oai_dc',
        'schema': 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd',
        'metadataNamespace': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
    },
    {
        'prefix': 'jats',
        'schema': 'https://jats.nlm.nih.gov/publishing/0.4/xsd/JATS-journalpublishing0.xsd',
        'metadataNamespace': 'http://jats.nlm.nih.gov',
    }
]


class OAIModelView(BaseListView, TemplateResponseMixin):
    """ Base class for OAI views generated from model Querysets """
    content_type = "application/xml"

    metadata_prefix = 'oai_dc'

    metadata_formats_set = {
        format.get('prefix') for format in metadata_formats
    }

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
        if self.metadata_prefix \
                and self.metadata_prefix not in self.metadata_formats_set:
            raise exceptions.OAIUnsupportedMetadataFormat()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["metadata_prefix"] = self.request.GET.get("metadataPrefix",
                                                          "oai_dc")
        return context


class OAIPaginationMixin(View):
    """ A Mixin allowing views to be paginated via OAI resumptionToken

    The resumptionToken is a query parameter that allows a consumer of the OAI
    interface to resume consuming elements of a listed query when the bounds
    of such list are larger than the maximum number of records allowed per
    response. This is achieved by encoding the page number details in the
    querystring as the resumptionToken itself.
    Furthermore, any filters provided as queryparams need to be encoded
    into the resumptionToken as per the spec, it is not mandatory for the
    consumer to provide filters on subsequent queries for the same list. This
    is addressed in the `dispatch` method where we have no option but to mutate
    the self.request.GET member in order to inject those querystring filters.
    """
    page_kwarg = "token_page"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._decoded_token = {}

    def dispatch(self, *args, **kwargs):
        """ Adds resumptionToken encoded parameters into request.GET

        This makes the implementation of resumptionToken transparent to any
        child views that will see all encoded filters in the resumptionToken
        as GET parameters
        """
        self._decode_token()
        with allow_mutating_GET(self.request):
            for key, value in self._decoded_token.items():
                self.request.GET[key] = value
        return super().dispatch(*args, **kwargs)

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
        token_data = {}
        for key, value in self.request.GET.items():
            # verb is an exception as per OAI spec
            if key not in {'resumptionToken', "verb"}:
                token_data[key] = value
        token_data.update(self.get_token_context(context))

        return quote(urlencode(token_data))

    def _decode_token(self):
        if not self._decoded_token and "resumptionToken" in self.request.GET:
            raw_token = self.request.GET["resumptionToken"]
            try:
                self._decoded_token = dict(parse_qsl(unquote(raw_token)))
            except ValueError:
                raise exceptions.OAIBadToken()

    @property
    def page(self):
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
                # grab the until string and check if it is timezone aware
                # if it is not, add a default H:m:sZ.
                if not until_date.tzinfo:
                    untile_date = until_date.replace(
                            hour=23, minute=59, second=59, tzinfo=utc,
                    )

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
        if self._decoded_token and "from" in self._decoded_token.items():
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
