"""
Utilities for designing and working with models
"""
__copyright__ = "Copyright 2018 Birkbeck, University of London"
__author__ = "Birkbeck Centre for Technology and Publishing"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from contextlib import contextmanager
from io import BytesIO
import re
import sys
import warnings
from bleach import clean

from django import forms
from django.apps import apps
from django.contrib import admin
from django.core.paginator import EmptyPage, Paginator
from django.contrib.postgres.lookups import SearchLookup as PGSearchLookup
from django.contrib.postgres.search import (
    SearchVector as DjangoSearchVector,
    SearchVectorField,
)
from django.core import validators
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import(
    connection,
    IntegrityError,
    models,
    ProgrammingError,
    transaction,
)
from django.db.backends.utils import truncate_name
from django.db.models import fields, Q, Manager
from django.db.models.fields.related import ForeignObjectRel, ManyToManyField
from django.db.models.functions import Coalesce, Greatest
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
from django.utils import translation, timezone
from django.conf import settings
from django.db.models.query import QuerySet
from django.shortcuts import reverse

from django_bleach.models import BleachField
from django_bleach.forms import BleachField as BleachFormField

from modeltranslation.manager import MultilingualManager, MultilingualQuerySet
from modeltranslation.utils import auto_populate
from PIL import Image
import xml.etree.cElementTree as et
from tinymce.widgets import TinyMCE

from utils.const import (
    get_allowed_html_tags_minimal,
    get_allowed_attributes_minimal,
)
from utils.logger import get_logger

logger = get_logger(__name__)


class AbstractSiteModel(models.Model):
    """Adds site-like functionality to any model"""
    SCHEMES = {
        True: "https",
        False: "http",
    }
    AUTH_SUCCESS_URL = "website_index"

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

    def site_url(self, path='', query=''):
        # This is here to avoid circular imports
        from utils import logic
        return logic.build_url(
            netloc=self.domain,
            scheme=self._get_scheme(),
            path=path,
            query=query,
        )

    def _get_scheme(self):
        scheme = self.SCHEMES[self.is_secure]
        if settings.DEBUG is True:
            scheme = self.SCHEMES[False]
        return scheme

    def auth_success_url(self, next_url=''):
        """
        Gets the standard redirect url for a successful authentication.
        """
        return next_url or reverse(self.AUTH_SUCCESS_URL)


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


class LastModifiedModelQuerySet(models.query.QuerySet):
    def update(self, *args, **kwargs):
        kwargs['last_modified'] = timezone.now()
        super().update(*args, **kwargs)


class LastModifiedModelManager(models.Manager):
    def get_queryset(self):
        # this is to use your custom queryset methods
        return LastModifiedModelQuerySet(self.model, using=self._db)


class AbstractLastModifiedModel(models.Model):
    # A mapping from these models last modified field relations and their models
    _LAST_MODIFIED_FIELDS_MAP = {}
    _LAST_MODIFIED_ACCESSORS = {}

    last_modified = models.DateTimeField(
        auto_now=True,
        editable=True
    )
    objects = LastModifiedModelManager()

    class Meta:
        abstract = True

    @property
    def model_key(self):
        return (type(self), self.pk)

    @classmethod
    def get_last_modified_field_map(cls, visited_fields=None):

        # Early return of cached calculation
        if cls._LAST_MODIFIED_FIELDS_MAP:
            return cls._LAST_MODIFIED_FIELDS_MAP

        field_map = {}
        if visited_fields is None:
            visited_fields = set()

        local_fields = cls._meta.get_fields()
        for field in local_fields:
            if (
                (field.many_to_many
                or field.one_to_many
                or field.many_to_one)
                and field not in visited_fields
            ):
                model = field.remote_field.model
                if issubclass(model, AbstractLastModifiedModel):
                    # Avoid infinite recursion when models are doubly linked
                    visited_fields.add(field.remote_field)
                    visited_fields.add(field)

                    field_map[field.name] = model

        # Workout relations of child nodes
        for field, model in tuple(field_map.items()):
            other_map = model.get_last_modified_field_map(visited_fields)
            for other_field_name, other_model in other_map.items():
                field_map[f"{field}__{other_field_name}"] = other_model

        # The below caching method is not ideal, however
        cls._LAST_MODIFIED_FIELDS_MAP = field_map
        return field_map

    @classmethod
    def get_last_modified_accessors(cls):
        if cls._LAST_MODIFIED_ACCESSORS:
            return cls._LAST_MODIFIED_ACCESSORS

        field_map = cls.get_last_modified_field_map()
        accessors = set(
            # sqlite's MAX returns NULL if any value is NULL
            Coalesce(
                f"{field}__last_modified",
                timezone.make_aware(timezone.datetime.fromtimestamp(0))
            )
            for field in field_map.keys()
        )

        cls._LAST_MODIFIED_ACCESSORS = accessors
        return cls.get_last_modified_accessors()


    def best_last_modified_date(self, visited_nodes=None):
        """ Determines the last modified date considering all related objects
        Any relationship which is an instance of this class will have its
        `last_modified` date considered for calculating the last_modified date
        for the instance from which this method is called
        :param visited_nodes: A set of visited objects to ignore. It avoids
            infinite recursion when 2 models are circularly related.
            encoded as set of pairs of object model and PK
        :return: The most recent last_modified date of all related models.
        """
        last_modified_keys = list(self.get_last_modified_accessors())
        annotated_query = self._meta.model.objects.filter(id=self.id).annotate(
            best_last_mod_date=Greatest(
                self.last_modified,
                *last_modified_keys,
                output_field=models.DateTimeField(),
            ),
        )
        result = annotated_query.values("best_last_mod_date").first()
        return result["best_last_mod_date"]


class SearchLookup(PGSearchLookup):
    """ A Search lookup that works across multiple databases.
    Django dropped support for the search lookup when using MySQLin 1.10
    This lookup attempts to restore some of that behaviour so that MySQL users
    can still benefit of some form of full text search. For any other vendors,
    the search performs a simple LIKE match. For Postgres, the behaviour from
    contrib.postgres.lookups.SearchLookup is preserved
    """
    lookup_name = 'search'

    def as_mysql(self, compiler, connection):
       lhs, lhs_params = self.process_lhs(compiler, connection)
       rhs, rhs_params = self.process_rhs(compiler, connection)
       params = lhs_params + rhs_params
       return 'MATCH (%s) AGAINST (%s IN BOOLEAN MODE)' % (lhs, rhs), params

    def as_postgresql(self, compiler, connection):
        return super().as_sql(compiler, connection)


    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return 'MATCH (%s) AGAINST (%s IN BOOLEAN MODE)' % (lhs, rhs), params

    def process_lhs(self, compiler, connection):
        if connection.vendor != 'postgresql':
            return models.Lookup.process_lhs(self, compiler, connection)
        else:
            return super().process_lhs(compiler, connection)

    def process_rhs(self, compiler, connection):
        if connection.vendor != 'postgresql':
            return models.Lookup.process_rhs(self, compiler, connection)
        else:
            return super().process_rhs(compiler, connection)

SearchVectorField.register_lookup(SearchLookup)
models.CharField.register_lookup(SearchLookup)


class BaseSearchManagerMixin(Manager):
    search_lookups = set()

    def search(self, search_term, search_filters, sort=None, site=None):
        if connection.vendor == "postgresql":
            return self.postgres_search(search_term, search_filters, sort, site)
        elif connection.vendor == "mysql":
            return self.mysql_search(search_term, search_filters, sort, site)
        else:
            return self._search(search_term, search_filters, sort, site)

    def _search(self, search_term, search_filters, sort=None, site=None):
        """ This is a copy of search from journal.views.old_search with filters
        """
        articles = self.get_queryset()
        if search_term:
            escaped = re.escape(search_term)
            split_term = [re.escape(word) for word in search_term.split(" ")]
            split_term.append(escaped)
            search_regex = "^({})$".format(
                "|".join({name for name in split_term})
            )
            q_object = Q()
            if search_filters.get("title"):
                q_object = q_object | Q(title__icontains=search_term)
            if search_filters.get("abstract"):
                q_object = q_object | Q(abstract__icontains=search_term)
            if search_filters.get("keywords"):
                q_object = q_object | Q(keywords__word=search_term)
            if search_filters.get("authors"):
                q_object = q_object | (
                    Q(frozenauthor__first_name__iregex=search_regex) |
                    Q(frozenauthor__last_name__iregex=search_regex)
                )
            articles = articles.filter(q_object)
            if site:
                # TODO: Support other site types
                articles = articles.filter(journal=site)

        return articles.distinct()

    def postgres_search(self, search_term, search_filters, sort=None, site=None):
        return self._search(search_term, search_filters, sort, site)

    def mysql_search(self, search_term, search_filters, sort=None, site=None):
        return self._search(search_term, search_filters, sort, site)

    def get_search_lookups(self):
        return self.search_lookups

class SearchVector(DjangoSearchVector):
    """ An Extension of SearchVector that works with SearchVectorField

    Django's implementation assumes that the `to_tsvector` function needs
    to be called with the provided column, except that when the field is already
    a SearchVectorField, there is no need. Django's implementation in 2.2
    (405c8363362063542e9e79beac53c8437d389520) also attempts to cast the
    column data into a TextField, prior to casting to the tsvector, which we
    override under `set_source_expressions`

    """
    def set_source_expressions(self, _):
        """ Ignore Django's implementation
        We don't require the expressions to be re-casted during the as_sql call
        """
        pass

    # Override template to ignore function
    function = None
    template = '%(expressions)s'


def search_model_admin(request, model, q=None, queryset=None):
    """
    A simple search using the admin search functionality,
    for use in class-based views where our methods for
    article search do not suit.
    :param request: A Django request object
    :param model: Any model that has search_fields specified in its admin
    :param q: the search term
    :param queryset: a pre-existing queryset to filter by the search term
    """
    if not q:
        q = request.POST['q'] if request.POST else request.GET['q']
    if not queryset:
        queryset = model.objects.all()
    registered_admin = admin.site._registry[model]
    return registered_admin.get_search_results(request, queryset, q)


class JanewayBleachField(BleachField):
    """ An override of BleachField to avoid casting SafeString from db
    Bleachfield automatically casts the default return type (string) into
    a SafeString, which is okay when using the value for HTML rendering but
    not when using the value elsewhere (XML encoding)
    https://github.com/marksweb/django-bleach/blob/504b3784c525886ba1974eb9ecbff89314688491/django_bleach/models.py#L76
    """

    def from_db_value(self, value, expression, connection):
        return value

    def pre_save(self, model_instance, *args, **kwargs):
        data = getattr(model_instance, self.attname)
        try:
            return super().pre_save(model_instance, *args, **kwargs)
        except TypeError:
            # Gracefully ignore typerrors on BleachField
            return data


class JanewayBleachFormField(BleachFormField):
    """
    An override of BleachFormField
    to avoid the same unwanted effects that
    JanewayBleachField avoids.
    """

    widget = TinyMCE

    def to_python(self, value):
        if value in self.empty_values:
            return self.empty_value
        return clean(value, **self.bleach_options)


class MiniHTMLFormField(JanewayBleachFormField):
    """
    A form field to hold limited HTML phrasing content,
    generally for use inline or on one line.
    It uses a much smaller bleach allowlist
    and loads by default with a minimal TinyMCE widget.
    It is the default formfield used by JanewayBleachCharField.
    """

    def __init__(self, *args, **kwargs):
        # These kwargs have to be set this way because otherwise
        # they will be ignored by the Django Bleach implementation of
        # BleachField.formfield
        # https://github.com/marksweb/django-bleach/blob/d675d09423ddb440b4c83c8a82bd8b853f4603c7/django_bleach/models.py#L42-L61
        kwargs['allowed_tags'] = get_allowed_html_tags_minimal()
        kwargs['allowed_attributes'] = get_allowed_attributes_minimal()
        kwargs['widget'] = TinyMCE(
            mce_attrs={
                'plugins': 'help code',
                'menubar': '',
                'forced_root_block': 'div',
                'toolbar': 'help removeformat | undo redo | ' \
                           'bold italic superscript subscript',
                'height': '8rem',
                'resize': True,
                'elementpath': False,
            }
        )
        super().__init__(*args, **kwargs)


class JanewayBleachCharField(JanewayBleachField):
    """
    An override of JanewayBleachField to use a minimal form field
    and widget but get sanitization.
    """

    def formfield(self, *args, **kwargs):
        defaults = {'form_class': MiniHTMLFormField}
        defaults.update(kwargs)
        return super().formfield(*args, **defaults)


def default_press():
    try:
        Press = apps.get_model("press", "Press")
        return Press.objects.first()
    except ProgrammingError:
        # Initial migration will attempt to call this,
        # even when no EditorialGroups are created
        return


def default_press_id():
    default_press_obj = default_press()
    if default_press_obj:
        return default_press_obj.pk


class DynamicChoiceField(models.CharField):
    def __init__(self, dynamic_choices=(), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dynamic_choices = dynamic_choices

    def formfield(self, *args, **kwargs):
        form_element = super().formfield(**kwargs)
        for choice in self.dynamic_choices:
            form_element.choices.append(choice)
        return form_element

    def validate(self, value, model_instance):
        """
        Validates value and throws ValidationError.
        """
        try:
            super().validate(value, model_instance)
        except ValidationError as e:
            # If the raised exception is for invalid choice we check if the
            # choice is in dynamic choices.
            if e.code == 'invalid_choice':
                potential_values = set(
                    item[0] for item in self.dynamic_choices
                )
                if value not in potential_values:
                    raise


class DateTimePickerInput(forms.DateTimeInput):
    format_key = 'DATETIME_INPUT_FORMATS'
    template_name = 'admin/core/widgets/datetimepicker.html'


class DateTimePickerFormField(forms.DateTimeField):
    widget = DateTimePickerInput


class DateTimePickerModelField(models.DateTimeField):
    def formfield(self, **kwargs):
        kwargs['form_class'] = DateTimePickerFormField
        return super().formfield(**kwargs)

@property
def NotImplementedField(self):
    raise NotImplementedError


class SafePaginator(Paginator):
    """
    A paginator for avoiding an uncaught exception
    caused by passing a page parameter that is out of range.
    """
    def validate_number(self, number):
        try:
            return super().validate_number(number)
        except EmptyPage:
            if number > 1:
                return self.num_pages
            else:
                raise


def check_exclusive_fields_constraint(model_label, fields, blank=True):
    """
    Checks that only one of several exclusive fields is populated.
    For example, CreditRecord has author, frozen_author, and preprint_author,
    but only one should be populated.
    If blank=True, allows for all fields to be blank.
    Set this as one of the constraints in a model's Meta.constraints.
    :param model_label: snake-case name of model like 'credit_record'
    :param fields: iterable of field names that should be exclusive
    """
    main_query = models.Q()

    # Do main validation
    for this_field in fields:
        query_piece = models.Q()
        query_piece &= Q((f'{this_field}__isnull', False))
        other_fields = [field for field in fields if field != this_field]
        for other_field in other_fields:
            query_piece &= Q((f'{other_field}__isnull', True))
        main_query |= Q(query_piece)

    # Allow for all fields to be blank
    if blank == True:
        query_piece = models.Q()
        for field in fields:
            query_piece &= models.Q((f'{field}__isnull', True))
            main_query |= query_piece
    fields_str = "_".join(list(fields))

    long_name = f'exclusive_fields_{model_label}_{fields_str}'
    # Our supported databases have a max length of 64 chars for constraints
    name = truncate_name(long_name, length=64)
    constraint = models.CheckConstraint(
        check=main_query,
        name=name,
    )
    return constraint


# Regex for use by AffiliationCompatibleQueryset
AFFILIATION_COMPATIBLE_PATTERNS = (
    (
        # Account and FrozenAuthor had 'institution'
        re.compile(r'^institution'),
        'controlledaffiliation__organization__labels__value',
    ),
    (
        # PreprintAuthor had 'affiliation'
        re.compile(r'^affiliation'),
        'controlledaffiliation__organization__labels__value',
    ),
    (
        # Account and FrozenAuthor had 'department'
        re.compile(r'^department'),
        'controlledaffiliation__department',
    ),
    (
        # Account and FrozenAuthor had 'country'
        re.compile(r'^country'),
        'controlledaffiliation__organization__locations__country',
    )
)


class AffiliationCompatibleQueryset(models.query.QuerySet):
    """
    The Account, FrozenAuthor, PreprintAuthor models used to have
    fields like 'institution', 'affiliation', 'department', and 'country'.
    When we migrated this data to the ControlledAffiliation model, we preserved
    the old fields via this queryset class. It maps the old lookups to
    new ones to provide what the caller expects on most single-instance methods.
    Bulk methods are not supported.
    """

    # The field name on ControlledAffiliation that refers to this queryset's model
    AFFILIATION_RELATED_NAME = NotImplementedField

    def _warn_old_lookups_used(self, old_lookups):
        object_name = self.model._meta.object_name
        warnings.warn(
            f'Deprecated fields were called on {object_name}: '
            f'{old_lookups}',
            DeprecationWarning,
        )

    def _pop_old_affiliation_lookups(self, kwargs):
        """
        Pops old affiliation-related lookups off queryset kwargs so they
        can be handled separately in custom create() and update() methods.
        """
        old_kwargs = {
            'institution': kwargs.pop('institution', '') or kwargs.pop('affiliation', ''),
            'department': kwargs.pop('department', ''),
            'country': kwargs.pop('country', ''),
        }
        # Filter out empty fields
        used_kwargs = {k: v for k, v in old_kwargs.items() if v}
        if used_kwargs:
            self._warn_old_lookups_used(list(used_kwargs.keys()))
        return used_kwargs

    def _remap_old_affiliation_lookups(self, kwargs):
        """
        Checks for old affiliation-related field names on queryset lookups
        and remaps them to new names for get() and filter() methods.
        """
        old_lookups = []
        new_kwargs = {}
        for lookup in kwargs.keys():
            for prog, replacement in AFFILIATION_COMPATIBLE_PATTERNS:
                if prog.match(lookup):
                    old_lookups.append(lookup)
                    new_lookup = prog.sub(replacement, lookup)
                    new_kwargs[new_lookup] = kwargs[lookup]
        for lookup in old_lookups:
            kwargs.pop(lookup)
        if old_lookups:
            self._warn_old_lookups_used(old_lookups)
        kwargs.update(new_kwargs)
        return kwargs

    def _create_affiliation(self, affil_kwargs, obj):
        affil_kwargs[self.AFFILIATION_RELATED_NAME] = obj
        many_to_one = self.model._meta.fields_map['controlledaffiliation']
        ControlledAffiliation = many_to_one.related_model
        affiliation, _ = ControlledAffiliation.get_or_create_without_ror(
            **affil_kwargs
        )
        return affiliation

    def get(self, *args, **kwargs):
        kwargs = self._remap_old_affiliation_lookups(kwargs)
        return super().get(*args, **kwargs)

    def create(self, **kwargs):
        affil_kwargs = self._pop_old_affiliation_lookups(kwargs)
        obj = super().create(**kwargs)
        if affil_kwargs:
            self._create_affiliation(affil_kwargs, obj)
        return obj

    def filter(self, *args, **kwargs):
        kwargs = self._remap_old_affiliation_lookups(kwargs)
        return super().filter(*args, **kwargs)
