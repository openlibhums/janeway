"""
Utilities for designing and working with models
"""
__copyright__ = "Copyright 2018 Birkbeck, University of London"
__author__ = "Birkbeck Centre for Technology and Publishing"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.db import models, IntegrityError, transaction
from django.http.request import split_domain_port
from django.utils import translation
from django.conf import settings

from modeltranslation.manager import MultilingualManager, MultilingualQuerySet
from modeltranslation.utils import auto_populate

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
            path=path or "",
        )


class PGCaseInsensitivedMixin():
    """Activates the citext postgres extension for the given field"""
    def db_type(self, connection):
        if connection.vendor == "postgresql":
            return "citext"
        elif connection.vendor == "sqlite":
            return "text collate nocase"
        else:
            return super().db_type(connection)


class PGCaseInsensitiveEmailField(PGCaseInsensitivedMixin, models.EmailField):
    pass


def merge_models(src, dest):
    """ Moves relations from `src` to `dest` and deletes src
    :param src: Model instance to be removed
    :param dest: Model instance into which src will be merged
    """
    model = src._meta.model
    if dest._meta.model != model:
        raise TypeError("Can't merge a %s with a %s", model, dest._meta.model)
    fields = src._meta.get_fields()
    for field in fields:
        if field.many_to_many:
            # These can be ManyToManyRel or ManyToManyField depending on the
            # direction the relationship was declared.
            if isinstance(field, models.Field):
                related_model = field.related_model
                remote_field = field.remote_field.name
                manager = getattr(dest, field.get_attname())
            else:
                accessor = getattr(src, field.get_accessor_name())
                manager = getattr(dest, field.get_accessor_name())
            # Query all related objects via through, in case there is a custom
            # Through model
            remote_field = manager.source_field_name
            related_filter = {remote_field: src}
            objects = manager.through.objects.filter(**related_filter)
        elif field.one_to_many:
            remote_field = field.remote_field.name
            accessor_name = field.get_accessor_name()
            accessor = getattr(src, accessor_name)
            objects = accessor.all()

        for obj in objects:
            try:
                with transaction.atomic():
                    setattr(obj, remote_field, dest)
                    obj.save()
            except IntegrityError:
                # Ignore unique constraint violations
                pass
    src.delete()


class JanewayMultilingualQuerySet(MultilingualQuerySet):

    def check_kwargs(self, **kwargs):
        for k, v in kwargs.items():
            if k.endswith('_{}'.format(settings.LANGUAGE_CODE)):
                return False
        return True

    def check_base_language(self, **kwargs):
        lang = translation.get_language()
        if lang and lang != settings.LANGUAGE_CODE and self.check_kwargs(**kwargs):
            raise Exception(
                'When creating a new translation you must provide'
                ' a translation for the base language, {}'.format(
                    settings.LANGUAGE_CODE
                )
            )

    def get_or_create(self, **kwargs):
        self.check_base_language(**kwargs)
        return super(JanewayMultilingualQuerySet, self).get_or_create(**kwargs)

    def create(self, **kwargs):
        self.check_base_language(**kwargs)
        return super(JanewayMultilingualQuerySet, self).create(**kwargs)

    def update_or_create(self, **kwargs):
        self.check_base_language(**kwargs)
        return super(JanewayMultilingualQuerySet, self).update_or_create(**kwargs)


class JanewayMultilingualManager(MultilingualManager):
    def get_queryset(self):
        return JanewayMultilingualQuerySet(self.model)