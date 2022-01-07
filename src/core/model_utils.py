"""
Utilities for designing and working with models
"""
__copyright__ = "Copyright 2018 Birkbeck, University of London"
__author__ = "Birkbeck Centre for Technology and Publishing"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from contextlib import contextmanager
from io import BytesIO
import sys

from django import forms
from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models, IntegrityError, transaction
from django.db.models import fields
from django.db.models.fields.related import ForeignObjectRel, ManyToManyField
from django.core.validators import (
    FileExtensionValidator,
    get_available_image_extensions,
)
from django.db.models.fields.related_descriptors import (
    create_forward_many_to_many_manager,
    ManyToManyDescriptor,
)
from django.http.request import split_domain_port
from django.utils.functional import cached_property
from django.utils import translation
from django.conf import settings
from modeltranslation.manager import MultilingualManager, MultilingualQuerySet
from modeltranslation.utils import auto_populate
from PIL import Image
import xml.etree.cElementTree as et

from utils import logic


class AbstractSiteModel(models.Model):
    """Adds site-like functionality to any model"""
    SCHEMES = {
        True: "https",
        False: "http",
    }

    domain = models.CharField(
        max_length=255, unique=True, blank=True, null=True)
    is_secure = models.BooleanField(
        default=False,
        help_text="If the site should redirect to HTTPS, mark this.",
    )

    class Meta:
        abstract = True

    @classmethod
    def get_by_request(cls, request):
        """ Returns the site object relevant for the given request
        :param request: A Django Request object
        :return: The site object and the path under which the object was matched
        """
        path = None
        domain = request.get_host()
        # Lookup by domain
        try:
            obj = cls.get_by_domain(domain)
        except cls.DoesNotExist:
            obj = None
        return obj, path

    @classmethod
    def get_by_domain(cls, domain):
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


class M2MOrderedThroughField(ManyToManyField):
    """ Orders m2m related objects by their 'through' Model

    When a 'through' model declares an ordering in its Meta
    options, it is ignored by Django's default manager.
    This field adds the through model to the ordering logic
    of the manager so that if the through model declares
    an ordering logic, it will be used in the join query
    """
    def contribute_to_class(self, cls, *args, **kwargs):
        super_return = super().contribute_to_class(cls, *args, **kwargs)
        setattr(cls, self.name, M2MOrderedThroughDescriptor(self.remote_field, reverse=False))
        return super_return


class M2MOrderedThroughDescriptor(ManyToManyDescriptor):

    @cached_property
    def related_manager_cls(self):
        related_model = self.rel.related_model if self.reverse else self.rel.model
        related_manager = create_forward_many_to_many_manager(
                        related_model._default_manager.__class__,
                        self.rel,
                        reverse=self.reverse,
        )
        return create_m2m_ordered_through_manager(related_manager, self.rel)


@contextmanager
def allow_m2m_operation(through):
    """ Enables m2m operations on through models

    This is done by flagging the model as auto_created dynamically. It only
    works if all your extra fields on the through model have defaults declared.
    """
    cached = through._meta.auto_created
    through._meta.auto_created = True
    try:
        yield
    finally:
        through._meta.auto_created = cached


def create_m2m_ordered_through_manager(related_manager, rel):
    class M2MOrderedThroughManager(related_manager):
        def _apply_ordering(self, queryset):
            # Check for custom related name (there should be a
            # .get_related_name() but I can't find anything like it)
            related_name = self.source_field.remote_field.related_name
            if not related_name:
                related_name = self.through._meta.model_name

            # equivalent of my_object.relation.all().order_by(related_name)
            return queryset.extra(order_by=[related_name])

        def get_queryset(self, *args, **kwargs):
            """ Here is where we can finally apply our ordering logic"""
            qs = super().get_queryset(*args, **kwargs)
            return self._apply_ordering(qs)

        def add(self, *objs):
            with allow_m2m_operation(rel.through):
                return super().add(*objs)

        def remove(self, *objs):
            with allow_m2m_operation(rel.through):
                return super().remove(*objs)

        def clear(self):
            with allow_m2m_operation(rel.through):
                return super().clear()


    return M2MOrderedThroughManager


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


class SVGImageField(models.ImageField):
    def formfield(self, **kwargs):
        defaults = {'form_class': SVGImageFieldForm}
        defaults.update(kwargs)
        return super().formfield(**defaults)


def validate_image_or_svg_file_extension(value):
    allowed_extensions = get_available_image_extensions() + ["svg"]
    return FileExtensionValidator(allowed_extensions=allowed_extensions)(value)


class SVGImageFieldForm(forms.ImageField):
    default_validators = [validate_image_or_svg_file_extension]

    def to_python(self, data):
        """
        Checks that the file-upload field data contains a valid image or SVG.
        """
        # We call the grand-parent and re-implement the parent checking for SVG
        super_result = super(forms.ImageField, self).to_python(data)
        if super_result is None:
            return None

        # Data can be a readable object, a templfile or a filepath
        if hasattr(data, 'temporary_file_path'):
            file_obj = data.temporary_file_path()
        else:
            if hasattr(data, 'read'):
                file_obj = BytesIO(data.read())
            else:
                file_obj = BytesIO(data['content'])

        try:
            # load() could spot a truncated JPEG, but it loads the entire
            # image in memory, which is a DoS vector. See #3848 and #18520.
            image = Image.open(file_obj)
            image.verify()

            # Annotating so subclasses can reuse it for their own validation
            super_result.image = image
            super_result.content_type = Image.MIME[image.format]
        except Exception as e:
            # Handle SVG here
            if not is_svg(file_obj):
                raise ValidationError(
                    self.error_messages['invalid_image'],
                    code='invalid_image',
                ).with_traceback(sys.exc_info()[2])
        if hasattr(super_result, 'seek') and callable(super_result.seek):
            super_result.seek(0)
        return super_result


def is_svg(f):
    """
    Check if provided file is svg
    """
    f.seek(0)
    tag = None
    try:
        for event, el in et.iterparse(f, ('start',)):
            tag = el.tag
            break
    except et.ParseError:
        pass
    return tag == '{http://www.w3.org/2000/svg}svg'
