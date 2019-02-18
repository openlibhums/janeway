"""
Utilities for designing and working with models
"""
__copyright__ = "Copyright 2018 Birkbeck, University of London"
__author__ = "Birkbeck Centre for Technology and Publishing"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.db import models
from django.http.request import split_domain_port

from utils import logic


class AbstractSiteModel(models.Model):
    """Adds site-like functionality to any model"""
    SCHEMES = {
        True: "https",
        False: "http",
    }

    domain = models.CharField(
        max_length=255, default="www.example.com", unique=True)
    is_secure = models.BooleanField(
        default=False,
        help_text="If the site should redirect to HTTPS, mark this.",
    )

    class Meta:
        abstract = True

    @classmethod
    def get_by_request(cls, request):
        domain = request.get_host()
        # Lookup by domain with/without port
        try:
            obj = cls.objects.get(domain=domain)
        except cls.DoesNotExist:
            # Lookup without port
            domain, _port = split_domain_port(domain)
            obj = cls.objects.get(domain=domain)
        return obj

    def site_url(self, path=None):
        return logic.build_url(
            netloc=self.domain,
            scheme=self.SCHEMES[self.is_secure],
            path=path,
        )
