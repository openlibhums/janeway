__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import os
import re
import uuid
import statistics
import json
from datetime import timedelta
from django.utils.html import format_html
import pytz
from hijack.signals import hijack_started, hijack_ended
from iso639 import Lang
from iso639.exceptions import InvalidLanguageValue
import warnings
import tqdm
import zipfile

from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.exceptions import ValidationError
from django.db import (
    connection,
    IntegrityError,
    models,
    transaction,
)
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.functional import cached_property
from django.template.defaultfilters import date
import swapper

from core import files, validators
from core.file_system import JanewayFileSystemStorage
from core.model_utils import (
    AbstractLastModifiedModel,
    AbstractSiteModel,
    AffiliationCompatibleQueryset,
    DynamicChoiceField,
    JanewayBleachField,
    JanewayBleachCharField,
    PGCaseInsensitiveEmailField,
    SearchLookup,
    default_press_id,
    check_exclusive_fields_constraint,
)
from review import models as review_models
from copyediting import models as copyediting_models
from repository import models as repository_models
from utils.models import RORImportError
from submission import models as submission_models
from utils.forms import clean_orcid_id
from submission.models import CreditRecord
from utils.logger import get_logger
from utils import logic as utils_logic
from utils.forms import plain_text_validator
from production import logic as production_logic

fs = JanewayFileSystemStorage()
logger = get_logger(__name__)

IMAGE_GALLEY_TEMPLATE = """
    <img class="responsive-img" src={url} alt="{alt}">
"""


def profile_images_upload_path(instance, filename):
    try:
        filename = str(uuid.uuid4()) + "." + str(filename.split(".")[1])
    except IndexError:
        filename = str(uuid.uuid4())

    path = "profile_images/"
    return os.path.join(path, filename)


SALUTATION_CHOICES = (
    ("Miss", _("Miss")),
    ("Ms", _("Ms")),
    ("Mrs", _("Mrs")),
    ("Mr", _("Mr")),
    ("Mx", _("Mx")),
    ("Dr", _("Dr")),
    ("Prof.", _("Prof.")),
)

COUNTRY_CHOICES = [
    ("AF", "Afghanistan"),
    ("AX", "\xc5land Islands"),
    ("AL", "Albania"),
    ("DZ", "Algeria"),
    ("AS", "American Samoa"),
    ("AD", "Andorra"),
    ("AO", "Angola"),
    ("AI", "Anguilla"),
    ("AQ", "Antarctica"),
    ("AG", "Antigua and Barbuda"),
    ("AR", "Argentina"),
    ("AM", "Armenia"),
    ("AW", "Aruba"),
    ("AU", "Australia"),
    ("AT", "Austria"),
    ("AZ", "Azerbaijan"),
    ("BS", "Bahamas"),
    ("BH", "Bahrain"),
    ("BD", "Bangladesh"),
    ("BB", "Barbados"),
    ("BY", "Belarus"),
    ("BE", "Belgium"),
    ("BZ", "Belize"),
    ("BJ", "Benin"),
    ("BM", "Bermuda"),
    ("BT", "Bhutan"),
    ("BO", "Bolivia, Plurinational State of"),
    ("BQ", "Bonaire, Sint Eustatius and Saba"),
    ("BA", "Bosnia and Herzegovina"),
    ("BW", "Botswana"),
    ("BV", "Bouvet Island"),
    ("BR", "Brazil"),
    ("IO", "British Indian Ocean Territory"),
    ("BN", "Brunei Darussalam"),
    ("BG", "Bulgaria"),
    ("BF", "Burkina Faso"),
    ("BI", "Burundi"),
    ("KH", "Cambodia"),
    ("CM", "Cameroon"),
    ("CA", "Canada"),
    ("CV", "Cape Verde"),
    ("KY", "Cayman Islands"),
    ("CF", "Central African Republic"),
    ("TD", "Chad"),
    ("CL", "Chile"),
    ("CN", "China"),
    ("CX", "Christmas Island"),
    ("CC", "Cocos (Keeling) Islands"),
    ("CO", "Colombia"),
    ("KM", "Comoros"),
    ("CG", "Congo"),
    ("CD", "Congo, The Democratic Republic of the"),
    ("CK", "Cook Islands"),
    ("CR", "Costa Rica"),
    ("CI", "C\xf4te d'Ivoire"),
    ("HR", "Croatia"),
    ("CU", "Cuba"),
    ("CW", "Cura\xe7ao"),
    ("CY", "Cyprus"),
    ("CZ", "Czech Republic"),
    ("DK", "Denmark"),
    ("DJ", "Djibouti"),
    ("DM", "Dominica"),
    ("DO", "Dominican Republic"),
    ("EC", "Ecuador"),
    ("EG", "Egypt"),
    ("SV", "El Salvador"),
    ("GQ", "Equatorial Guinea"),
    ("ER", "Eritrea"),
    ("EE", "Estonia"),
    ("ET", "Ethiopia"),
    ("FK", "Falkland Islands (Malvinas)"),
    ("FO", "Faroe Islands"),
    ("FJ", "Fiji"),
    ("FI", "Finland"),
    ("FR", "France"),
    ("GF", "French Guiana"),
    ("PF", "French Polynesia"),
    ("TF", "French Southern Territories"),
    ("GA", "Gabon"),
    ("GM", "Gambia"),
    ("GE", "Georgia"),
    ("DE", "Germany"),
    ("GH", "Ghana"),
    ("GI", "Gibraltar"),
    ("GR", "Greece"),
    ("GL", "Greenland"),
    ("GD", "Grenada"),
    ("GP", "Guadeloupe"),
    ("GU", "Guam"),
    ("GT", "Guatemala"),
    ("GG", "Guernsey"),
    ("GN", "Guinea"),
    ("GW", "Guinea-Bissau"),
    ("GY", "Guyana"),
    ("HT", "Haiti"),
    ("HM", "Heard Island and McDonald Islands"),
    ("VA", "Holy See (Vatican City State)"),
    ("HN", "Honduras"),
    ("HK", "Hong Kong"),
    ("HU", "Hungary"),
    ("IS", "Iceland"),
    ("IN", "India"),
    ("ID", "Indonesia"),
    ("IR", "Iran, Islamic Republic of"),
    ("IQ", "Iraq"),
    ("IE", "Ireland"),
    ("IM", "Isle of Man"),
    ("IL", "Israel"),
    ("IT", "Italy"),
    ("JM", "Jamaica"),
    ("JP", "Japan"),
    ("JE", "Jersey"),
    ("JO", "Jordan"),
    ("KZ", "Kazakhstan"),
    ("KE", "Kenya"),
    ("KI", "Kiribati"),
    ("KP", "Korea, Democratic People's Republic of"),
    ("KR", "Korea, Republic of"),
    ("KW", "Kuwait"),
    ("KG", "Kyrgyzstan"),
    ("LA", "Lao People's Democratic Republic"),
    ("LV", "Latvia"),
    ("LB", "Lebanon"),
    ("LS", "Lesotho"),
    ("LR", "Liberia"),
    ("LY", "Libya"),
    ("LI", "Liechtenstein"),
    ("LT", "Lithuania"),
    ("LU", "Luxembourg"),
    ("MO", "Macao"),
    ("MK", "Macedonia, Republic of"),
    ("MG", "Madagascar"),
    ("MW", "Malawi"),
    ("MY", "Malaysia"),
    ("MV", "Maldives"),
    ("ML", "Mali"),
    ("MT", "Malta"),
    ("MH", "Marshall Islands"),
    ("MQ", "Martinique"),
    ("MR", "Mauritania"),
    ("MU", "Mauritius"),
    ("YT", "Mayotte"),
    ("MX", "Mexico"),
    ("FM", "Micronesia, Federated States of"),
    ("MD", "Moldova, Republic of"),
    ("MC", "Monaco"),
    ("MN", "Mongolia"),
    ("ME", "Montenegro"),
    ("MS", "Montserrat"),
    ("MA", "Morocco"),
    ("MZ", "Mozambique"),
    ("MM", "Myanmar"),
    ("NA", "Namibia"),
    ("NR", "Nauru"),
    ("NP", "Nepal"),
    ("NL", "Netherlands"),
    ("NC", "New Caledonia"),
    ("NZ", "New Zealand"),
    ("NI", "Nicaragua"),
    ("NE", "Niger"),
    ("NG", "Nigeria"),
    ("NU", "Niue"),
    ("NF", "Norfolk Island"),
    ("MP", "Northern Mariana Islands"),
    ("NO", "Norway"),
    ("OM", "Oman"),
    ("PK", "Pakistan"),
    ("PW", "Palau"),
    ("PS", "Palestine, State of"),
    ("PA", "Panama"),
    ("PG", "Papua New Guinea"),
    ("PY", "Paraguay"),
    ("PE", "Peru"),
    ("PH", "Philippines"),
    ("PN", "Pitcairn"),
    ("PL", "Poland"),
    ("PT", "Portugal"),
    ("PR", "Puerto Rico"),
    ("QA", "Qatar"),
    ("RE", "R\xe9union"),
    ("RO", "Romania"),
    ("RU", "Russian Federation"),
    ("RW", "Rwanda"),
    ("BL", "Saint Barth\xe9lemy"),
    ("SH", "Saint Helena, Ascension and Tristan da Cunha"),
    ("KN", "Saint Kitts and Nevis"),
    ("LC", "Saint Lucia"),
    ("MF", "Saint Martin (French part)"),
    ("PM", "Saint Pierre and Miquelon"),
    ("VC", "Saint Vincent and the Grenadines"),
    ("WS", "Samoa"),
    ("SM", "San Marino"),
    ("ST", "Sao Tome and Principe"),
    ("SA", "Saudi Arabia"),
    ("SN", "Senegal"),
    ("RS", "Serbia"),
    ("SC", "Seychelles"),
    ("SL", "Sierra Leone"),
    ("SG", "Singapore"),
    ("SX", "Sint Maarten (Dutch part)"),
    ("SK", "Slovakia"),
    ("SI", "Slovenia"),
    ("SB", "Solomon Islands"),
    ("SO", "Somalia"),
    ("ZA", "South Africa"),
    ("GS", "South Georgia and the South Sandwich Islands"),
    ("ES", "Spain"),
    ("LK", "Sri Lanka"),
    ("SD", "Sudan"),
    ("SR", "Suriname"),
    ("SS", "South Sudan"),
    ("SJ", "Svalbard and Jan Mayen"),
    ("SZ", "Swaziland"),
    ("SE", "Sweden"),
    ("CH", "Switzerland"),
    ("SY", "Syrian Arab Republic"),
    ("TW", "Taiwan, Province of China"),
    ("TJ", "Tajikistan"),
    ("TZ", "Tanzania, United Republic of"),
    ("TH", "Thailand"),
    ("TL", "Timor-Leste"),
    ("TG", "Togo"),
    ("TK", "Tokelau"),
    ("TO", "Tonga"),
    ("TT", "Trinidad and Tobago"),
    ("TN", "Tunisia"),
    ("TR", "Turkey"),
    ("TM", "Turkmenistan"),
    ("TC", "Turks and Caicos Islands"),
    ("TV", "Tuvalu"),
    ("UG", "Uganda"),
    ("UA", "Ukraine"),
    ("AE", "United Arab Emirates"),
    ("GB", "United Kingdom"),
    ("US", "United States"),
    ("UM", "United States Minor Outlying Islands"),
    ("UY", "Uruguay"),
    ("UZ", "Uzbekistan"),
    ("VU", "Vanuatu"),
    ("VE", "Venezuela, Bolivarian Republic of"),
    ("VN", "Viet Nam"),
    ("VG", "Virgin Islands, British"),
    ("VI", "Virgin Islands, U.S."),
    ("WF", "Wallis and Futuna"),
    ("EH", "Western Sahara"),
    ("YE", "Yemen"),
    ("ZM", "Zambia"),
    ("ZW", "Zimbabwe"),
]

TIMEZONE_CHOICES = tuple(zip(pytz.all_timezones, pytz.all_timezones))

SUMMERNOTE_SENTINEL = "<p><br></p>"


class Country(models.Model):
    code = models.TextField(max_length=5)
    name = models.TextField(max_length=255)

    class Meta:
        ordering = ("name", "code")
        verbose_name_plural = "countries"

    def __str__(self):
        return self.name


class AccountQuerySet(AffiliationCompatibleQueryset):
    AFFILIATION_RELATED_NAME = "account"

    def create(self, **kwargs):
        # Remove kwargs pointing to deprecated fields so they
        # can be handled by AffiliationCompatibleQueryset methods
        affil_kwargs = self._pop_old_affiliation_lookups(kwargs)

        # We overload this method to call .clean here and
        # ensure emails are normalized prior to insertion
        obj = self.model(**kwargs)
        obj.clean()
        self._for_write = True
        obj.save(force_insert=True, using=self.db)

        # Handle the deprecated fields using
        # AffiliationCompatibleQueryset methods
        if affil_kwargs:
            self._create_affiliation(affil_kwargs, obj)
        return obj


class AccountManager(BaseUserManager):
    def create_user(self, username=None, password=None, email=None, **kwargs):
        """Creates a user from the given username or email
        In Janeway, users rely on email addresses to log in. For compatibility
        with 3rd party libraries, we allow a username argument, however only a
        email address will be accepted as the username and email.
        """
        if not email and username:
            email = username
            if "username" in kwargs:
                del kwargs["username"]
        try:
            validate_email(email)
            email = self.normalize_email(email)
        except (ValidationError, TypeError, ValueError):
            raise ValueError(f"{email} not a valid email address.")

        account = self.model(
            # The original case of the email is preserved
            # in the email field
            email=email,
            # The email is lowercased in the username field
            # so that we can perform case-insensitive checking
            # and avoid creating duplicate accounts
            username=email.lower(),
        )

        account.set_password(password)
        account.save()

        return account

    def create_superuser(self, email, password, **kwargs):
        kwargs["email"] = email
        kwargs["password"] = password
        account = self.create_user(**kwargs)

        account.is_staff = True
        account.is_admin = True
        account.is_active = True
        account.is_superuser = True
        account.save()

        return account

    def get_queryset(self):
        return AccountQuerySet(self.model)


class Account(AbstractBaseUser, PermissionsMixin):
    email = PGCaseInsensitiveEmailField(unique=True, verbose_name=_("Email"))
    username = models.CharField(max_length=254, unique=True, verbose_name=_("Username"))

    first_name = models.CharField(
        max_length=300,
        blank=False,
        verbose_name=_("First name"),
        validators=[plain_text_validator],
    )
    middle_name = models.CharField(
        max_length=300,
        blank=True,
        verbose_name=_("Middle name"),
        validators=[plain_text_validator],
    )
    last_name = models.CharField(
        max_length=300,
        blank=False,
        verbose_name=_("Last name"),
        validators=[plain_text_validator],
    )

    # activation_code is deprecated
    activation_code = models.CharField(max_length=100, null=True, blank=True)
    salutation = models.CharField(
        max_length=10,
        choices=SALUTATION_CHOICES,
        blank=True,
        verbose_name=_("Salutation"),
        validators=[plain_text_validator],
    )
    suffix = models.CharField(
        max_length=300,
        blank=True,
        verbose_name=_("Name suffix"),
        validators=[plain_text_validator],
    )
    biography = JanewayBleachField(
        blank=True,
        verbose_name=_("Biography"),
    )
    orcid = models.CharField(
        max_length=40, null=True, blank=True, verbose_name=_("ORCiD")
    )
    twitter = models.CharField(
        max_length=300, null=True, blank=True, verbose_name=_("Twitter Handle")
    )
    facebook = models.CharField(
        max_length=300, null=True, blank=True, verbose_name=_("Facebook Handle")
    )
    linkedin = models.CharField(
        max_length=300, null=True, blank=True, verbose_name=_("Linkedin Profile")
    )
    website = models.URLField(
        max_length=300, null=True, blank=True, verbose_name=_("Website")
    )
    github = models.CharField(
        max_length=300, null=True, blank=True, verbose_name=_("Github Username")
    )
    profile_image = models.ImageField(
        upload_to=profile_images_upload_path,
        null=True,
        blank=True,
        storage=fs,
        verbose_name=("Profile Image"),
    )
    email_sent = models.DateTimeField(blank=True, null=True)
    date_confirmed = models.DateTimeField(blank=True, null=True)
    confirmation_code = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_("Confirmation Code"),
        help_text="A UUID created upon registration and retrieved "
        "for authentication during account activation",
    )
    signature = JanewayBleachField(
        blank=True,
        verbose_name=_("Signature"),
    )
    interest = models.ManyToManyField("Interest", null=True, blank=True)
    preferred_timezone = DynamicChoiceField(
        max_length=300,
        null=True,
        blank=True,
        choices=tuple(),
        dynamic_choices=TIMEZONE_CHOICES,
        verbose_name=_("Preferred Timezone"),
    )

    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    enable_digest = models.BooleanField(
        default=False,
        verbose_name=_("Enable Digest"),
    )
    enable_public_profile = models.BooleanField(
        default=False,
        help_text=_("If enabled, your basic profile will be available to the public."),
        verbose_name=_("Enable public profile"),
    )

    date_joined = models.DateTimeField(default=timezone.now)

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    name_prefix = models.CharField(
        max_length=10,
        blank=True,
        help_text="The 'name_prefix' field is deprecated. Use 'salutation'.",
    )

    objects = AccountManager()

    USERNAME_FIELD = "email"

    class Meta:
        ordering = ("first_name", "last_name", "username")
        unique_together = ("email", "username")

    def __getattribute__(self, name):
        if name == "name_prefix":
            warnings.warn(
                "The 'name_prefix' field is deprecated. Use 'salutation'.",
                DeprecationWarning,
                stacklevel=2,
            )
        return super().__getattribute__(name)

    def clean(self, *args, **kwargs):
        """Normalizes the email address

        The username is lowercased instead, to cope with a bug present for
        accounts imported/registered prior to v.1.3.8
        https://github.com/BirkbeckCTP/janeway/issues/1497
        The username being unique and lowercase at clean time avoids
        the creation of duplicate email addresses where the casing might
        be different.
        """
        self.email = self.__class__.objects.normalize_email(self.email)
        self.username = self.email.lower()
        super().clean(*args, **kwargs)

    def __str__(self):
        return self.full_name()

    def password_policy_check(self, request, password):
        rules = [lambda s: len(password) >= request.press.password_length or "length"]

        if request.press.password_upper:
            rules.append(lambda password: any(x.isupper() for x in password) or "upper")

        if request.press.password_number:
            rules.append(lambda password: any(x.isdigit() for x in password) or "digit")

        problems = [p for p in [r(password) for r in rules] if p != True]

        return problems

    def string_id(self):
        return str(self.id)

    @property
    def real_email(self):
        if not self.email.endswith(settings.DUMMY_EMAIL_DOMAIN):
            return self.email
        else:
            return ""

    def get_full_name(self):
        """Deprecated in 1.5.2"""
        return self.full_name()

    def get_short_name(self):
        return self.first_name

    @property
    def first_names(self):
        return " ".join([self.first_name, self.middle_name])

    def full_name(self):
        """
        A string formed from all the name fields and the name suffix.
        """
        name_elements = [
            self.first_name,
            self.middle_name,
            self.last_name,
            self.suffix,
        ]
        return " ".join([name for name in name_elements if name])

    def salutation_name(self):
        """
        Used in salutations of templated emails.
        """
        if self.salutation:
            return "%s %s" % (self.salutation, self.last_name)
        else:
            return "%s %s" % (self.first_name, self.last_name)

    def initials(self):
        if self.first_name and self.last_name:
            if self.middle_name:
                return "%s%s%s" % (
                    self.first_name[:1],
                    self.middle_name[:1],
                    self.last_name[:1],
                )
            else:
                return "%s%s" % (self.first_name[:1], self.last_name[:1])
        else:
            return "N/A"

    def affiliation(self):
        """
        Use `primary_affiliation` or `affiliations` instead.

        For backwards compatibility, this is a method.
        Different from repository.models.Preprint.affiliation,
        which is a property.
        :rtype: str
        """
        return self.primary_affiliation(as_object=False)

    def primary_affiliation(self, as_object=True):
        return ControlledAffiliation.get_primary(
            affiliated_object=self,
            as_object=as_object,
        )

    @property
    def affiliations(self):
        return ControlledAffiliation.objects.filter(account=self)

    @property
    def institution(self):
        affil = self.primary_affiliation()
        return str(affil.organization) if affil else ""

    @institution.setter
    def institution(self, value):
        ControlledAffiliation.get_or_create_without_ror(
            institution=value,
            account=self,
        )

    @property
    def department(self):
        affil = self.primary_affiliation()
        return str(affil.department) if affil else ""

    @department.setter
    def department(self, value):
        ControlledAffiliation.get_or_create_without_ror(
            department=value,
            account=self,
        )

    @property
    def country(self):
        affil = self.primary_affiliation()
        organization = affil.organization if affil else None
        return organization.country if organization else None

    @country.setter
    def country(self, value):
        ControlledAffiliation.get_or_create_without_ror(
            country=value,
            account=self,
        )

    def active_reviews(self):
        return review_models.ReviewAssignment.objects.filter(
            reviewer=self,
            is_complete=False,
        )

    def active_copyedits(self):
        return copyediting_models.CopyeditAssignment.objects.filter(
            copyeditor=self, copyedit_acknowledged=False
        )

    def active_typesets(self):
        """
        Gathers typesetting tasks a user account has and returns a list of them.
        :return: List of objects
        """
        from production import models as production_models
        from proofing import models as proofing_models

        task_list = list()
        typeset_tasks = production_models.TypesetTask.objects.filter(
            typesetter=self, completed__isnull=True
        )
        proofing_tasks = proofing_models.TypesetterProofingTask.objects.filter(
            typesetter=self, completed__isnull=True
        )

        for task in typeset_tasks:
            task_list.append(task)

        for task in proofing_tasks:
            task_list.append(task)

        return task_list

    def add_account_role(self, role_slug, journal):
        role = Role.objects.get(slug=role_slug)
        return AccountRole.objects.get_or_create(role=role, user=self, journal=journal)

    def remove_account_role(self, role_slug, journal):
        role = Role.objects.get(slug=role_slug)
        AccountRole.objects.get(role=role, user=self, journal=journal).delete()

    @cached_property
    def roles(self):
        account_roles = AccountRole.objects.filter(
            user=self,
        )
        journal_roles_map = {}
        for account_role in account_roles:
            journal_roles_map.setdefault(account_role.journal.code, set())
            journal_roles_map[account_role.journal.code].add(account_role.role.slug)
        return journal_roles_map

    def roles_for_journal(self, journal):
        return [
            account_role.role
            for account_role in AccountRole.objects.filter(user=self, journal=journal)
        ]

    def check_role(self, journal, role, staff_override=True):
        if staff_override and (self.is_staff or self.is_journal_manager(journal)):
            return True
        else:
            return AccountRole.objects.filter(
                user=self,
                journal=journal,
                role__slug=role,
            ).exists()

    def is_journal_manager(self, journal):
        # this is an explicit check to avoid recursion in check_role.
        return AccountRole.objects.filter(
            user=self,
            journal=journal,
            role__slug="journal-manager",
        ).exists()

    def is_editor(self, request, journal=None):
        if not journal:
            return self.check_role(request.journal, "editor")
        else:
            return self.check_role(journal, "editor")

    def is_section_editor(self, request):
        return self.check_role(request.journal, "section-editor")

    def has_an_editor_role(self, request):
        editor = self.is_editor(request)
        section_editor = self.is_section_editor(request)

        if editor or section_editor:
            return True

        return False

    def is_reviewer(self, request):
        return self.check_role(request.journal, "reviewer")

    def is_author(self, request):
        return self.check_role(request.journal, "author")

    def is_proofreader(self, request):
        return self.check_role(request.journal, "proofreader")

    def is_production(self, request):
        return self.check_role(request.journal, "production")

    def is_copyeditor(self, request):
        return self.check_role(request.journal, "copyeditor")

    def is_typesetter(self, request):
        return self.check_role(request.journal, "typesetter")

    def is_proofing_manager(self, request):
        return self.check_role(request.journal, "proofing-manager")

    def is_repository_manager(self, repository):
        if self in repository.managers.all():
            return True

        return False

    def is_preprint_editor(self, request):
        if self in request.press.preprint_editors():
            return True

        return False

    def is_reader(self, request):
        return self.check_role(request.journal, "reader", staff_override=False)

    def snapshot_affiliations(self, frozen_author):
        """
        Delete any outdated affiliations on the frozen author and then
        assign copies of account affiliations to the frozen author.
        """
        frozen_author.affiliations.delete()
        for affiliation in self.affiliations:
            affiliation.pk = None
            affiliation.account = None
            affiliation.frozen_author = frozen_author
            affiliation.save()

    def snapshot_self(self, article, force_update=True):
        """
        Old function name for snapshot_as_author.
        """
        raise DeprecationWarning("Use snapshot_as_author instead.")
        return self.snapshot_as_author(article, force_update)

    def snapshot_as_author(self, article, force_update=True):
        """
        Create a submission.models.FrozenAuthor using the name fields
        and other details from this Account.
        article: submission.models.Article
        force_update: whether to overwrite fields if a FrozenAuthor exists
        """
        self.add_account_role("author", article.journal)

        frozen_dict = {
            "first_name": self.first_name,
            "middle_name": self.middle_name,
            "last_name": self.last_name,
            "name_suffix": self.suffix,
            "display_email": True if self == article.correspondence_author else False,
            "order": article.next_frozen_author_order(),
        }

        frozen_author, created = submission_models.FrozenAuthor.objects.get_or_create(
            author=self,
            article=article,
            defaults=frozen_dict,
        )
        if created or force_update:
            self.snapshot_affiliations(frozen_author)

        if not created and force_update:
            for k, v in frozen_dict.items():
                setattr(frozen_author, k, v)
            frozen_author.save()

        return frozen_author

    def frozen_author(self, article):
        try:
            return submission_models.FrozenAuthor.objects.get(
                article=article,
                author=self,
            )
        except submission_models.FrozenAuthor.DoesNotExist:
            return None

    @property
    def average_reviewer_score(self):
        reviewer_ratings = review_models.ReviewerRating.objects.filter(
            assignment__reviewer=self
        )
        ratings = [reviewer_rating.rating for reviewer_rating in reviewer_ratings]

        return statistics.mean(ratings) if ratings else 0

    def articles(self):
        return submission_models.Article.objects.filter(frozenauthor__author=self)

    def published_articles(self):
        articles = submission_models.Article.objects.filter(
            frozenauthor__author=self,
            stage=submission_models.STAGE_PUBLISHED,
            date_published__lte=timezone.now(),
        )
        request = utils_logic.get_current_request()
        if request and request.journal:
            articles.filter(journal=request.journal)

        return articles

    def preprint_subjects(self):
        "Returns a list of preprint subjects this user is an editor for"
        from repository import models as repository_models

        subjects = repository_models.Subject.objects.filter(
            editors__exact=self,
        )
        return subjects

    @property
    def hypothesis_username(self):
        username = "{pk}{first_name}{last_name}".format(
            pk=self.pk, first_name=self.first_name, last_name=self.last_name
        )[:30]
        return username.lower()


def generate_expiry_date():
    return timezone.now() + timedelta(days=1)


class OrcidToken(models.Model):
    token = models.UUIDField(default=uuid.uuid4)
    orcid = models.CharField(max_length=200)
    expiry = models.DateTimeField(
        default=generate_expiry_date, verbose_name=_("Expires on")
    )

    def __str__(self):
        return "ORCiD Token [{0}] - {1}".format(self.orcid, self.token)


class PasswordResetToken(models.Model):
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
    )
    token = models.CharField(max_length=300, default=uuid.uuid4)
    expiry = models.DateTimeField(
        default=generate_expiry_date, verbose_name=_("Expires on")
    )
    expired = models.BooleanField(default=False)

    def __str__(self):
        return "Account: {0}, Expiry: {1}, [{2}]".format(
            self.account.full_name(),
            self.expiry,
            "Expired" if self.expired else "Active",
        )

    def has_expired(self):
        if self.expired:
            return True
        elif self.expiry < timezone.now():
            return True
        else:
            return False

    class Meta:
        ordering = ["-expiry"]


class Role(models.Model):
    name = models.CharField(
        max_length=100,
        help_text="Display name for this role (can include spaces and capital letters)",
    )
    slug = models.CharField(
        max_length=100,
        help_text="Normalized string representing this role "
        "containing only lowercase letters and hyphens.",
    )

    class Meta:
        ordering = ("name", "slug")

    def __str__(self):
        return "%s" % self.name

    def __repr__(self):
        return "%s" % self.name


class AccountRole(models.Model):
    user = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
    )
    journal = models.ForeignKey(
        "journal.Journal",
        on_delete=models.CASCADE,
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = ("journal", "user", "role")
        ordering = ("journal", "role")

    def __str__(self):
        return "{0} {1} {2}".format(self.user, self.journal, self.role.name)


class Interest(models.Model):
    name = models.CharField(max_length=250)

    def __str__(self):
        return "%s" % self.name

    def __repr__(self):
        return "%s" % self.name


setting_types = (
    ("rich-text", "Rich Text"),
    ("mini-html", "Mini HTML"),
    ("text", "Plain Text"),
    ("char", "Characters"),
    ("number", "Number"),
    ("boolean", "Boolean"),
    ("file", "File"),
    ("select", "Select"),
    ("json", "JSON"),
)

privacy_types = (
    ("public", "Public"),
    ("typesetters", "Typesetters"),
    ("proofreaders", "Proofreaders"),
    ("copyeditors", "Copyedtiors"),
    ("editors", "Editors"),
    ("owner", "Owner"),
)


class SettingGroup(models.Model):
    VALIDATORS = {
        "email": (validators.validate_email_setting,),
    }
    name = models.CharField(max_length=100)
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return "%s" % self.name

    def __repr__(self):
        return "%s" % self.name

    def validate(self, value):
        if self.name in self.VALIDATORS:
            for validator in self.VALIDATORS[self.name]:
                validator(value)


class Setting(models.Model):
    VALIDATORS = {}
    name = models.CharField(max_length=100)
    group = models.ForeignKey(
        SettingGroup,
        on_delete=models.CASCADE,
    )
    types = models.CharField(max_length=20, choices=setting_types)
    pretty_name = models.CharField(max_length=100, default="")
    description = models.TextField(null=True, blank=True)

    is_translatable = models.BooleanField(default=False)

    editable_by = models.ManyToManyField(
        Role,
        blank=True,
        help_text="Determines who can edit this setting based on their assigned roles.",
    )

    class Meta:
        ordering = ("group", "name")

    def __str__(self):
        return "%s" % self.name

    def __repr__(self):
        return "%s" % self.name

    @property
    def default_setting_value(self):
        return SettingValue.objects.get(
            setting=self,
            journal=None,
        )

    def validate(self, value):
        if self.types in self.VALIDATORS:
            for validator in self.VALIDATORS[self.name]:
                validator(value)

        self.group.validate(value)


class SettingValue(models.Model):
    journal = models.ForeignKey(
        "journal.Journal",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    setting = models.ForeignKey(
        Setting,
        models.CASCADE,
    )
    value = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = (("journal", "setting"),)

    def __repr__(self):
        if self.journal:
            code = self.journal.code
        else:
            code = "default"
        return "[{0}]: {1}, {2}".format(code, self.setting.name, self.value)

    def __str__(self):
        return "[{0}]: {1}".format(self.journal, self.setting.name)

    @property
    def processed_value(self):
        return self.process_value()

    def process_value(self):
        """Converts string values of settings to proper values

        :return: a value
        """

        if self.setting.types == "boolean" and self.value == "on":
            return True
        elif self.setting.types == "boolean":
            return False
        elif self.setting.types == "number":
            try:
                return int(self.value)
            except BaseException:
                return 0
        elif self.setting.types == "json" and self.value:
            try:
                return json.loads(self.value)
            except json.JSONDecodeError as e:
                logger.error(
                    "Error loading JSON setting {setting_name} on {site_name} site.".format(
                        setting_name=self.setting.name,
                        site_name=self.journal.name if self.journal else "press",
                    )
                )
                return ""
        elif self.setting.types == "rich-text" and self.value == SUMMERNOTE_SENTINEL:
            return ""
        else:
            return self.value

    @property
    def render_value(self):
        """Converts string values of settings to values for rendering

        :return: a value
        """
        if self.setting.types == "boolean" and not self.value:
            return "off"
        elif self.setting.types == "boolean":
            return "on"
        elif self.setting.types == "file":
            if self.journal:
                return self.journal.site_url(reverse("journal_file", self.value))
            else:
                return self.press.site_url(reverse("serve_press_file", self.value))
        else:
            return self.value

    @property
    def press(self):
        if self.journal:
            return self.journal.press
        else:
            from press.models import Press

            return Press.objects.all()[0]

    def validate(self):
        self.setting.validate(self.value)

    @cached_property
    def editable_by(self):
        return {role.slug for role in self.setting.editable_by.all()}

    def save(self, *args, **kwargs):
        self.validate()
        super().save(*args, **kwargs)


class File(AbstractLastModifiedModel):
    article_id = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_("Article PK")
    )

    mime_type = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=1000)
    uuid_filename = models.CharField(max_length=100)
    label = models.CharField(
        max_length=1000, null=True, blank=True, verbose_name=_("Label")
    )
    description = JanewayBleachField(
        null=True, blank=True, verbose_name=_("Description")
    )
    sequence = models.IntegerField(default=1)
    owner = models.ForeignKey(Account, null=True, on_delete=models.SET_NULL)
    privacy = models.CharField(max_length=20, choices=privacy_types, default="owner")

    date_uploaded = models.DateTimeField(auto_now_add=True)

    is_galley = models.BooleanField(default=False)

    # Remote galley handling
    is_remote = models.BooleanField(default=False)
    remote_url = models.URLField(
        blank=True, null=True, verbose_name=_("Remote URL of file")
    )

    history = models.ManyToManyField(
        "FileHistory",
        blank=True,
    )
    text = models.OneToOneField(
        swapper.get_model_name("core", "FileText"),
        blank=True,
        null=True,
        related_name="file",
        on_delete=models.SET_NULL,
    )

    class Meta:
        ordering = ("sequence", "pk")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # for each galley that this file is used for, update the galley.type
        # field to ensure it doesn't become desynced from the file type.
        for galley in self.galley_set.all():
            label, type_ = production_logic.get_galley_label_and_type(self)
            galley.type = type_
            galley.save()

    @property
    def article(self):
        if self.article_id:
            return submission_models.Article.objects.get(pk=self.article_id)

    def delete(self, *args, **kwargs):
        self.unlink_file()
        super(File, self).delete()

    def unlink_file(self, journal=None):
        if self.article_id:
            try:
                path = self.self_article_path()
                os.unlink(path)
            except FileNotFoundError:
                print("file_not_found")
        elif journal:
            try:
                path = self.journal_path(journal)
                os.unlink(path)
            except FileNotFoundError:
                pass

    def unlink_preprint_file(self):
        path = self.preprint_path()
        os.unlink(path)

    def preprint_path(self):
        return os.path.join(
            settings.BASE_DIR, "files", "press", "preprints", str(self.uuid_filename)
        )

    def press_path(self):
        return os.path.join(
            settings.BASE_DIR, "files", "press", str(self.uuid_filename)
        )

    def journal_path(self, journal):
        return os.path.join(
            settings.BASE_DIR,
            "files",
            "journals",
            str(journal.pk),
            str(self.uuid_filename),
        )

    def self_article_path(self):
        if self.article_id:
            return os.path.join(
                settings.BASE_DIR,
                "files",
                "articles",
                str(self.article_id),
                str(self.uuid_filename),
            )

    def url(self):
        from core.middleware import GlobalRequestMiddleware

        request = GlobalRequestMiddleware.get_current_request()
        url_kwargs = {"file_id": self.pk}

        if request.journal and self.article_id:
            raise NotImplementedError
        elif request.journal:
            raise NotImplementedError
        else:
            return reverse(
                "serve_press_file",
                kwargs=url_kwargs,
            )

    def get_file(self, article, as_bytes=False):
        return files.get_file(self, article, as_bytes=as_bytes)

    def get_file_path(self, article):
        return os.path.join(
            settings.BASE_DIR,
            "files",
            "articles",
            str(article.id),
            str(self.uuid_filename),
        )

    def get_file_size(self, article):
        return os.path.getsize(
            os.path.join(
                settings.BASE_DIR,
                "files",
                "articles",
                str(article.id),
                str(self.uuid_filename),
            )
        )

    def next_history_seq(self):
        try:
            last_history_item = self.history.all().reverse()[0]
            return last_history_item.history_seq + 1
        except IndexError:
            return 0

    def checksum(self):
        if self.article_id:
            try:
                return files.checksum(self.self_article_path())
            except FileNotFoundError:
                return "No checksum could be calculated."
        else:
            logger.error(
                "Galley file ({file_id}) found with no article_id.".format(
                    file_id=self.pk
                ),
                extra={"stack": True},
            )
            return "No checksum could be calculated."

    def public_download_name(self):
        article = self.article
        if article:
            file_elements = os.path.splitext(self.original_filename)
            extension = file_elements[-1]

            if article.frozen_authors():
                author_surname = "-{0}".format(
                    article.frozen_authors()[0].last_name,
                )
            elif article.correspondence_author:
                author_surname = "-{0}".format(
                    article.correspondence_author.last_name,
                )
            else:
                logger.warning(
                    "Article {pk} has no author records".format(pk=article.pk)
                )
                author_surname = ""

            file_name = "{code}-{pk}{surname}{extension}".format(
                code=article.journal.code,
                pk=article.pk,
                surname=author_surname,
                extension=extension,
            )
            return file_name.lower()
        else:
            return self.original_filename

    def index_full_text(self, save=True):
        """Extracts text from the File and stores it into an indexed model

        Depending on the database backend, preprocessing ahead of indexing varies;
        As an example, for Postgresql, instead of storing the text as a LOB, a
        tsvector of the text is generated which is used for indexing. There is no
        such approach for MySQL, so the text is stored in full and then indexed,
        which takes significantly more disk space.

        Custom indexing routines can be provided with the swappable model under
        settings.py `CORE_FILETEXT_MODEL`
        :return: A bool indicating if the file has been succesfully indexed
        """
        indexed = False
        try:
            # TODO: Only aricle files are supported at the moment since File
            # objects don't know the path to the actual file unless you also
            # know the context (article/preprint/journal...) of the file
            path = self.self_article_path()
            if not path:
                return indexed
            text_parser = files.MIME_TO_TEXT_PARSER[self.mime_type]
        except KeyError:
            # We have no support for indexing files of this type yet
            return indexed
        parsed_text = text_parser(path)
        FileTextModel = swapper.load_model("core", "FileText")
        preprocessed_text = FileTextModel.preprocess_contents(parsed_text)
        if self.text:
            self.text.update_contents(preprocessed_text)
            indexed = True
        else:
            file_text_obj = FileTextModel.objects.create(
                contents=preprocessed_text,
                file=self,
            )
            self.text = file_text_obj
            if save:
                self.save()
            indexed = True

        return indexed

    @property
    def date_modified(self):
        warnings.warn(
            "'date_modified' is deprecated and will be removed, use last_modified instead."
        )
        return self.last_modified

    def __str__(self):
        return "%s" % self.original_filename

    def __repr__(self):
        return "%s" % self.original_filename


class AbstractFileText(models.Model):
    contents = models.TextField(blank=True, null=True)
    date_populated = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True

    @staticmethod
    def preprocess_contents(text, lang=None):
        return text

    def update_contents(self, text, lang=None):
        self.contents = self.preprocess_contents(text)
        self.save()

    def save(self, *args, **kwargs):
        self.date_populated = timezone.now()
        super().save(*args, **kwargs)


class FileText(AbstractFileText):
    class Meta:
        swappable = swapper.swappable_setting("core", "FileText")

    pass


class PGFileText(AbstractFileText):
    contents = SearchVectorField(blank=True, null=True, editable=False)

    class Meta:
        required_db_vendor = "postgresql"

    @staticmethod
    def preprocess_contents(text, lang=None):
        """Casts the given text into a postgres TSVector

        The result can be cached so that there is no need to store the original
        text and also speed up the search queries.
        The drawback is that the cached TSVector needs to be regenerated
        whenever the underlying field changes.

        Postgres `to_tsvector()` function normalises the input before handing it
        over to `tsvector()`.
        """
        cursor = connection.cursor()
        # Remove NULL characters before vectorising
        text = text.replace("\x00", "\ufffd")
        result = cursor.execute("SELECT to_tsvector(%s) as vector", [text])
        return cursor.fetchone()[0]


@receiver(models.signals.pre_save, sender=File)
def update_file_index(sender, instance, **kwargs):
    """Updates the indexed contents in the database"""
    if not instance.pk:
        return False

    if settings.ENABLE_FULL_TEXT_SEARCH and instance.text:
        instance.index_full_text(save=False)


class FileHistory(models.Model):
    article_id = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_("Article PK")
    )

    mime_type = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=1000)
    uuid_filename = models.CharField(max_length=100)
    label = models.CharField(
        max_length=200, null=True, blank=True, verbose_name=_("Label")
    )
    description = JanewayBleachField(
        null=True, blank=True, verbose_name=_("Description")
    )
    sequence = models.IntegerField(default=1)
    owner = models.ForeignKey(Account, null=True, on_delete=models.SET_NULL)
    privacy = models.CharField(max_length=20, choices=privacy_types, default="owner")

    history_seq = models.PositiveIntegerField(default=0)

    def __str__(self):
        return "Iteration {0}: {1}".format(self.history_seq, self.original_filename)

    class Meta:
        ordering = ("history_seq",)
        verbose_name_plural = "file histories"


def galley_type_choices():
    return (
        ("pdf", "PDF"),
        ("epub", "EPUB"),
        ("html", "HTML"),
        ("xml", "XML"),
        ("doc", "Word (Doc)"),
        ("docx", "Word (DOCX)"),
        ("odt", "OpenDocument Text Document"),
        ("tex", "LaTeX"),
        ("rtf", "RTF"),
        ("other", _("Other")),
        ("image", _("Image")),
    )


class Galley(AbstractLastModifiedModel):
    # Local Galley
    article = models.ForeignKey(
        "submission.Article",
        null=True,
        on_delete=models.CASCADE,
    )
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    css_file = models.ForeignKey(
        File, related_name="css_file", null=True, blank=True, on_delete=models.SET_NULL
    )
    images = models.ManyToManyField(File, related_name="images", null=True, blank=True)
    xsl_file = models.ForeignKey(
        "core.XSLFile",
        related_name="xsl_file",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    public = models.BooleanField(
        default=True,
        help_text="Uncheck if the typeset file should not be publicly available after the article is published.",
    )

    # Remote Galley
    is_remote = models.BooleanField(default=False)
    remote_file = models.URLField(blank=True, null=True)

    # All Galleys
    label = models.CharField(
        max_length=400,
        help_text='Typeset file labels are displayed in download links and have the format "Download Label" eg. if '
        "you set the label to be PDF the link will be Download PDF. If you want Janeway to set a label for "
        "you, leave it blank.",
    )
    type = models.CharField(max_length=100, choices=galley_type_choices())
    sequence = models.IntegerField(default=0)

    def unlink_files(self):
        if self.file and self.file.article_id:
            self.file.unlink_file()
        for image_file in self.images.all():
            if not image_file.images.exclude(galley=self).exists():
                image_file.unlink_file()

    def __str__(self):
        return "{0} ({1})".format(self.id, self.label)

    def detail(self):
        return format_html(
            '{} galley linked to <a href="#file_{}">file {}: {}</a>',
            self.label,
            self.file.pk,
            self.file.pk,
            self.file.original_filename,
        )

    def render(self, recover=False):
        return files.render_xml(
            self.file,
            self.article,
            xsl_path=self.xsl_file.file.path,
            recover=recover,
        )

    def render_crossref(self):
        xsl_path = os.path.join(
            settings.BASE_DIR, "transform", "xsl", files.CROSSREF_XSL
        )
        return files.render_xml(self.file, self.article, xsl_path=xsl_path)

    def has_missing_image_files(self, show_all=False):
        if not self.file.mime_type in files.MIMETYPES_WITH_FIGURES:
            return []

        xml_file_contents = self.file.get_file(self.article)

        souped_xml = BeautifulSoup(xml_file_contents, "lxml")

        elements = {
            "img": "src",
            "graphic": "xlink:href",
            "inline-graphic": "xlink:href",
        }

        missing_elements = []

        # iterate over all found elements
        for element, attribute in elements.items():
            images = souped_xml.findAll(element)

            # iterate over all found elements of each type in the elements dictionary
            for idx, val in enumerate(images):
                # attempt to pull a URL from the specified attribute
                url = os.path.basename(val.get(attribute, None))

                if show_all:
                    missing_elements.append(url)
                else:
                    if not self.images.filter(original_filename=url).first():
                        missing_elements.append(url)

        if not missing_elements:
            return []
        else:
            return missing_elements

    def all_images(self):
        """
        Returns all images/figures in a galley file.
        :return: A list of image paths found in the galley
        """
        return self.has_missing_image_files(show_all=True)

    def file_content(self, dont_render=False, recover=False):
        if self.file.mime_type == "text/html" or dont_render:
            return self.file.get_file(self.article)
        elif self.file.mime_type in files.XML_MIMETYPES:
            return self.render(recover=recover)
        elif self.file.mime_type in files.IMAGE_MIMETYPES:
            url = reverse(
                "article_download_galley",
                kwargs={"article_id": self.article.id, "galley_id": self.id},
            )
            contents = IMAGE_GALLEY_TEMPLATE.format(
                url=url,
                alt=self.label,
            )
            return contents

    def path(self):
        url = reverse(
            "article_download_galley",
            kwargs={"article_id": self.article.pk, "galley_id": self.pk},
        )
        return self.article.journal.site_url(path=url)

    @staticmethod
    def mimetypes_with_figures():
        return files.MIMETYPES_WITH_FIGURES

    def save(self, *args, **kwargs):
        if self.type == "xml" and not self.xsl_file:
            if self.article.journal:
                self.xsl_file = self.article.journal.xsl
            else:
                # Articles might not be part of any journals (e.g.: preprints)
                self.xsl_file = default_xsl()
        super().save(*args, **kwargs)


def upload_to_journal(instance, filename):
    instance.original_filename = filename
    if instance.journal:
        return "journals/%d/%s" % (instance.journal.pk, filename)
    else:
        return filename


class XSLFile(models.Model):
    file = models.FileField(
        upload_to=upload_to_journal,
        storage=JanewayFileSystemStorage("files/xsl"),
    )
    journal = models.ForeignKey(
        "journal.Journal", on_delete=models.CASCADE, blank=True, null=True
    )
    date_uploaded = models.DateTimeField(default=timezone.now)
    label = models.CharField(
        max_length=255,
        help_text="A label to help recognise this stylesheet",
        unique=True,
    )
    comments = JanewayBleachField(blank=True, null=True)
    original_filename = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return "%s(%s@%s)" % (self.__class__.__name__, self.label, self.file.path)


def default_xsl():
    return XSLFile.objects.get(label=settings.DEFAULT_XSL_FILE_LABEL).pk


class SupplementaryFile(models.Model):
    file = models.ForeignKey(
        File,
        on_delete=models.CASCADE,
    )
    doi = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.file.label

    @property
    def label(self):
        return self.file.label

    def path(self):
        return self.file.self_article_path()

    def mime_type(self):
        return files.file_path_mime(self.path())

    def url(self):
        path = reverse(
            "article_download_supp_file",
            kwargs={
                "article_id": self.file.article.pk,
                "supp_file_id": self.pk,
            },
        )

        return self.file.article.journal.site_url(path=path)


class Task(models.Model):
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="task_content_type",
        null=True,
    )
    object_id = models.PositiveIntegerField(blank=True, null=True)
    object = GenericForeignKey("content_type", "object_id")

    title = models.CharField(max_length=300)
    description = JanewayBleachField()
    complete_events = models.ManyToManyField("core.TaskCompleteEvents")
    link = models.TextField(
        null=True,
        blank=True,
        help_text="A url name, where the action of this task can undertaken",
    )
    assignees = models.ManyToManyField(Account)
    completed_by = models.ForeignKey(
        Account,
        blank=True,
        null=True,
        related_name="completed_by",
        on_delete=models.SET_NULL,
    )

    created = models.DateTimeField(default=timezone.now)
    due = models.DateTimeField(blank=True, null=True)
    completed = models.DateTimeField(blank=True, null=True)

    @property
    def is_late(self):
        if timezone.now().date() >= self.due.date():
            return True

        return False

    @staticmethod
    def destroyer(**kwargs):
        """
        Destroys tasks where the kwargs matches an entry in complete_events
        :param kwargs: a dictionary containing an event_name key and a task_obj object that points to an object stored
        inside a task.
        :return: None
        """

        # Important safety note:

        # This function does a lookup from tasks based on the task_obj field that is passed. The type of object that
        # is passed could, therefore, lead to arbitrary task deletion. This occurs when, for instance, there is an
        # Article with ID 1 and a ReviewerAssignment with ID 1 that both subscribe to the same event for teardown. If
        # one event fires with an Article and the other fires with a ReviewerAssignment it is the object that is passed
        # that will be used to lookup the task for deletion.

        # To militate against this risk, we recommend that task_obj is _always_ set to an article and that, likewise,
        # task.object is always an article. All other workflow components can be looked up from this point.

        tasks_to_destroy = Task.objects.filter(
            complete_events__event_name=kwargs["event"],
            content_type=ContentType.objects.get_for_model(kwargs["task_obj"]),
            object_id=kwargs["task_obj"].pk,
        )

        for task in tasks_to_destroy:
            task.completed = timezone.now()
            task.save()

    def __str__(self):
        return "Task for {0} #{1}: {2}".format(
            self.content_type, self.object_id, self.title
        )


class TaskCompleteEvents(models.Model):
    event_name = models.CharField(max_length=300)

    def __str__(self):
        return self.event_name

    class Meta:
        verbose_name_plural = "task complete events"


class EditorialGroup(models.Model):
    name = models.CharField(max_length=500)
    press = models.ForeignKey(
        "press.Press",
        on_delete=models.CASCADE,
        default=default_press_id,
    )
    description = JanewayBleachField(blank=True, null=True)
    journal = models.ForeignKey(
        "journal.Journal",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    sequence = models.PositiveIntegerField()
    display_profile_images = models.BooleanField(
        default=False,
        help_text="Enable to display profile images for this group.",
    )

    class Meta:
        ordering = ("sequence",)

    def next_member_sequence(self):
        orderings = [member.sequence for member in self.editorialgroupmember_set.all()]
        return max(orderings) + 1 if orderings else 0

    def members(self):
        return self.editorialgroupmember_set.all()

    def __str__(self):
        if self.journal:
            return f"{self.name} ({self.journal.code})"
        else:
            return f"{self.name} ({self.press})"


class EditorialGroupMember(models.Model):
    group = models.ForeignKey(
        EditorialGroup,
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
    )
    sequence = models.PositiveIntegerField()
    statement = models.TextField(
        blank=True,
        help_text="A statement of interest or purpose",
    )

    class Meta:
        ordering = ("sequence",)

    def __str__(self):
        return f"{self.user} in {self.group}"


class Contacts(models.Model):
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="contact_content_type",
        null=True,
    )
    object_id = models.PositiveIntegerField(blank=True, null=True)
    object = GenericForeignKey("content_type", "object_id")

    name = models.CharField(max_length=300)
    email = models.EmailField()
    role = models.CharField(max_length=200)
    sequence = models.PositiveIntegerField(default=999)

    class Meta:
        # This verbose name will hopefully more clearly
        # distinguish this model from the below model `Contact`
        # in the admin area.
        verbose_name_plural = "contacts"
        ordering = ("sequence", "name")

    def __str__(self):
        return "{0}, {1} - {2}".format(self.name, self.object, self.role)


class Contact(models.Model):
    recipient = models.EmailField(
        max_length=200, verbose_name=_("Who would you like to contact?")
    )
    sender = models.EmailField(
        max_length=200, verbose_name=_("Your contact email address")
    )
    subject = models.CharField(max_length=300, verbose_name=_("Subject"))
    body = JanewayBleachField(verbose_name=_("Your message"))
    client_ip = models.GenericIPAddressField(blank=True, null=True)
    date_sent = models.DateField(auto_now_add=True)

    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="contact_c_t", null=True
    )
    object_id = models.PositiveIntegerField(blank=True, null=True)
    object = GenericForeignKey("content_type", "object_id")

    class Meta:
        # This verbose name will hopefully more clearly
        # distinguish this model from the above model `Contacts`
        # in the admin area.
        verbose_name_plural = "contact messages"


class DomainAlias(AbstractSiteModel):
    redirect = models.BooleanField(
        default=True,
        verbose_name="301",
        help_text="If enabled, the site will throw a 301 redirect to the "
        "master domain.",
    )
    journal = models.ForeignKey(
        "journal.Journal",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    press = models.ForeignKey(
        "press.Press",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    @property
    def site_object(self):
        return self.journal or self.press

    @property
    def redirect_url(self):
        return self.site_object.site_url()

    def build_redirect_url(self, path=None):
        return self.site_object.site_url(path=path)

    def save(self, *args, **kwargs):
        if not bool(self.journal) ^ bool(self.press):
            raise ValidationError(" One and only one of press or journal must be set")
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "domain aliases"


BASE_ELEMENTS = [
    {
        "name": "review",
        "handshake_url": "review_home",
        "jump_url": "review_in_review",
        "stage": submission_models.STAGE_UNASSIGNED,
        "article_url": True,
    },
    {
        "name": "copyediting",
        "handshake_url": "copyediting",
        "jump_url": "article_copyediting",
        "stage": submission_models.STAGE_EDITOR_COPYEDITING,
        "article_url": True,
    },
    {
        "name": "typesetting",
        "handshake_url": "typesetting_articles",
        "jump_url": "typesetting_article",
        "stage": submission_models.STAGE_TYPESETTING_PLUGIN,
        "article_url": True,
    },
    {
        "name": "prepublication",
        "handshake_url": "publish",
        "jump_url": "publish_article",
        "stage": submission_models.STAGE_READY_FOR_PUBLICATION,
        "article_url": True,
    },
    {
        "name": "production",
        "handshake_url": "production_list",
        "jump_url": "production_article",
        "stage": submission_models.STAGE_TYPESETTING,
        "article_url": False,
    },
    {
        "name": "proofing",
        "handshake_url": "proofing_list",
        "jump_url": "proofing_article",
        "stage": submission_models.STAGE_PROOFING,
        "article_url": False,
    },
]

BASE_ELEMENT_NAMES = [element.get("name") for element in BASE_ELEMENTS]


class Workflow(models.Model):
    journal = models.ForeignKey(
        "journal.Journal",
        on_delete=models.CASCADE,
    )
    elements = models.ManyToManyField("WorkflowElement")


class WorkflowElement(models.Model):
    journal = models.ForeignKey(
        "journal.Journal",
        on_delete=models.CASCADE,
    )
    element_name = models.CharField(max_length=255)
    handshake_url = models.CharField(max_length=255)
    jump_url = models.CharField(max_length=255)
    stage = models.CharField(
        max_length=255,
        default=submission_models.STAGE_UNASSIGNED,
    )
    article_url = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=20)

    class Meta:
        ordering = ("order", "element_name")

    @property
    def stages(self):
        from core import workflow

        try:
            return workflow.ELEMENT_STAGES[self.element_name]
        except KeyError:
            return [self.stage]

    @property
    def articles(self):
        return submission_models.Article.objects.filter(
            stage__in=self.stages,
            journal=self.journal,
        )

    @property
    def settings(self):
        from core import workflow

        return workflow.workflow_plugin_settings(self)

    def __str__(self):
        return self.element_name


class WorkflowLog(models.Model):
    article = models.ForeignKey(
        "submission.Article",
        on_delete=models.CASCADE,
    )
    element = models.ForeignKey(
        WorkflowElement,
        on_delete=models.CASCADE,
    )
    timestamp = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(
        "core.Account",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("timestamp",)

    def __str__(self):
        return "{0} {1}".format(self.element.element_name, self.timestamp)


class HomepageElement(models.Model):
    # the URL to configure this homepage element, or null/blank if no configuration is needed
    configure_url = models.CharField(max_length=200, blank=True, null=True)

    # The name of this homepage element. This should be unique.
    name = models.CharField(max_length=200, blank=False, null=False)

    # the template path to include
    template_path = models.CharField(max_length=500, blank=False, null=False)

    # the ordering
    sequence = models.PositiveIntegerField(default=999)

    # the associated object
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="element_content_type",
        null=True,
    )

    object_id = models.PositiveIntegerField(blank=True, null=True)
    object = GenericForeignKey("content_type", "object_id")

    available_to_press = models.BooleanField(
        default=False,
        help_text="Determines if this element is available for the press.",
    )

    # whether or not this item is active
    active = models.BooleanField(default=False)

    # whether or not this item has a configuration
    has_config = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Homepage Elements"
        ordering = ("sequence", "name")
        unique_together = ("name", "content_type", "object_id")

    def __str__(self):
        return self.name


class LoginAttempt(models.Model):
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)


class AccessRequest(models.Model):
    journal = models.ForeignKey(
        "journal.Journal",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    repository = models.ForeignKey(
        "repository.Repository",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        "core.Account",
        on_delete=models.CASCADE,
    )
    role = models.ForeignKey(
        "core.Role",
        on_delete=models.CASCADE,
    )
    requested = models.DateTimeField(
        default=timezone.now,
    )
    processed = models.BooleanField(
        default=False,
    )
    text = JanewayBleachField(
        blank=True,
        null=True,
    )
    evaluation_note = JanewayBleachField(
        null=True,
        help_text="This note will be sent to the requester when you approve or decline their request.",
    )

    def __str__(self):
        return "User {} requested {} permission for {}".format(
            self.user.full_name(),
            self.journal.name if self.journal else self.repository.name,
            self.role.name,
        )


@receiver(post_save, sender=Account)
def setup_user_signature(sender, instance, created, **kwargs):
    if created and not instance.signature:
        instance.signature = instance.full_name()
        instance.save()


# This model is vestigial and will be removed in v1.5


class SettingValueTranslation(models.Model):
    hvad_value = models.TextField(
        blank=True,
        null=True,
    )
    language_code = models.CharField(
        max_length=15,
        db_index=True,
    )

    class Meta:
        managed = False
        db_table = "core_settingvalue_translation"


def log_hijack_started(sender, hijacker, hijacked, request, **kwargs):
    from utils import models as utils_models

    action = "{} ({}) has hijacked {} ({})".format(
        hijacker.full_name(),
        hijacker.pk,
        hijacked.full_name(),
        hijacked.pk,
    )

    utils_models.LogEntry.add_entry(
        types="Hijack Start",
        description=action,
        level="Info",
        actor=hijacker,
        request=request,
        target=hijacked,
    )


def log_hijack_ended(sender, hijacker, hijacked, request, **kwargs):
    from utils import models as utils_models

    action = "{} ({}) has released {} ({})".format(
        hijacker.full_name(),
        hijacker.pk,
        hijacked.full_name(),
        hijacked.pk,
    )

    utils_models.LogEntry.add_entry(
        types="Hijack Release",
        description=action,
        level="Info",
        actor=hijacker,
        request=request,
        target=hijacked,
    )


hijack_started.connect(log_hijack_started)
hijack_ended.connect(log_hijack_ended)


class OrganizationNameManager(models.Manager):
    def bulk_create_from_ror(self, ror_records):
        organizations_by_ror_id = {
            org.ror_id: org
            for org in Organization.objects.filter(~models.Q(ror_id__exact=""))
        }
        organization_names = []
        logger.debug(f"Importing organization names")
        for record in ror_records:
            ror_id = os.path.split(record.get("id", ""))[-1]
            organization = organizations_by_ror_id[ror_id]
            for name in record.get("names"):
                kwargs = {}
                kwargs["value"] = name.get("value", "")

                if name.get("lang"):
                    kwargs["language"] = name.get("language", "")

                if "ror_display" in name.get("types"):
                    kwargs["ror_display_for"] = organization
                if "label" in name.get("types"):
                    kwargs["label_for"] = organization
                if "alias" in name.get("types"):
                    kwargs["alias_for"] = organization
                if "acronym" in name.get("types"):
                    kwargs["acronym_for"] = organization
                organization_names.append(OrganizationName(**kwargs))
        return OrganizationName.objects.bulk_create(organization_names)

    @transaction.atomic
    def bulk_update_from_ror(self, ror_records):
        """
        Finds records where the names have changed,
        deletes those names in Janeway,
        and sends those records through OrganizationName.bulk_create_from_ror
        """
        organizations_by_ror_id = {
            org.ror_id: org
            for org in Organization.objects.filter(~models.Q(ror_id__exact=""))
            .prefetch_related("labels")
            .prefetch_related("aliases")
            .prefetch_related("acronyms")
        }

        ror_records_with_updated_names = []
        org_name_pks_to_delete = set()
        logger.debug(f"Updating names")
        for record in ror_records:
            ror_id = os.path.split(record.get("id", ""))[-1]
            organization = organizations_by_ror_id[ror_id]

            # Note that this set does not need to include ror_display
            # because all ror_display values are also labels in the
            # ROR schema
            janeway_names = set()
            for name in organization.labels.all():
                janeway_names.add(name)
            for name in organization.aliases.all():
                janeway_names.add(name)
            for name in organization.acronyms.all():
                janeway_names.add(name)

            janeway_name_values = set([name.value for name in janeway_names])

            ror_name_values = set(
                [name.get("value") for name in record.get("names", [])]
            )

            # Delete and recreate all authority-controlled names
            # when the names differ between Janeway and ROR.
            if janeway_name_values.difference(ror_name_values):
                org_name_pks_to_delete.update([name.pk for name in janeway_names])
                ror_records_with_updated_names.append(record)

        self.filter(pk__in=org_name_pks_to_delete).delete()

        if ror_records_with_updated_names:
            return self.bulk_create_from_ror(ror_records_with_updated_names)
        else:
            return []


class OrganizationName(models.Model):
    value = models.CharField(
        max_length=1000,
        verbose_name="Organization name",
    )
    ror_display_for = models.OneToOneField(
        "Organization",
        on_delete=models.CASCADE,
        related_name="ror_display",
        blank=True,
        null=True,
        help_text="This name is a preferred ROR-provided display name.",
    )
    label_for = models.ForeignKey(
        "Organization",
        on_delete=models.CASCADE,
        related_name="labels",
        blank=True,
        null=True,
        help_text="This name is a preferred ROR-provided alternative, "
        "often in a different language from the ROR display name.",
    )
    custom_label_for = models.OneToOneField(
        "Organization",
        on_delete=models.CASCADE,
        related_name="custom_label",
        blank=True,
        null=True,
        help_text="This name is a custom label entered by the end user. "
        "Only exists in Janeway, independent of ROR.",
    )
    alias_for = models.ForeignKey(
        "Organization",
        on_delete=models.CASCADE,
        related_name="aliases",
        blank=True,
        null=True,
        help_text="This name is a less preferred ROR-provided alternative.",
    )
    acronym_for = models.ForeignKey(
        "Organization",
        on_delete=models.CASCADE,
        related_name="acronyms",
        blank=True,
        null=True,
        help_text="This name is a ROR-provided acronym.",
    )
    language = models.CharField(
        max_length=10,
        blank=True,
        choices=submission_models.LANGUAGE_CHOICES,
    )
    objects = OrganizationNameManager()

    def __str__(self):
        return self.value


class OrganizationQueryset(models.query.QuerySet):
    @transaction.atomic
    def deduplicate_to_ror(self, limit=None):
        """
        Attempts to matching unstructured organization names to ROR names
        and IDs, and then bulk update related affiliations.
        Conservative, in that it only tolerates exact matches
        between normalized (lowercased) strings, and does not
        use country or other data to disambiguate globally ambigous names
        like "Musuem of Modern Art".
        This routine was about 33% effective in testing on live data.
        """

        # Identify names to deduplicate
        uncontrolled_organizations = self.filter(
            ror_id="",
            custom_label__isnull=False,
            controlledaffiliation__isnull=False,
        ).prefetch_related("custom_label")
        num_before = uncontrolled_organizations.count()
        logger.debug(f"Trying to match {num_before} organization names to ROR data.")
        if limit:
            uncontrolled_organizations = uncontrolled_organizations[:limit]

        # Create mapping from unique canonical names to org objects
        orgs_by_name = {}
        ambiguous_names_in_ror = set()
        ambiguous_names_in_db = set()
        labels = (
            OrganizationName.objects.filter(label_for__isnull=False)
            .prefetch_related("ror_display_for")
            .prefetch_related("label_for")
        )
        for name in labels:
            norm_name = name.value.lower()
            org = name.ror_display_for or name.label_for
            if norm_name in orgs_by_name:
                ambiguous_names_in_ror.add(norm_name)
            else:
                orgs_by_name[norm_name] = org

        for name in ambiguous_names_in_ror:
            orgs_by_name.pop(name)

        # Identify the affiliations to update
        affils_by_org_id = {}
        for affil in ControlledAffiliation.objects.filter(
            organization__isnull=False
        ).prefetch_related("organization"):
            org_id = affil.organization.pk
            if org_id not in affils_by_org_id:
                affils_by_org_id[org_id] = set()
            affils_by_org_id[org_id].add(affil)

        affiliations_to_update = []
        orgs_to_delete = set()
        for old_org in uncontrolled_organizations:
            norm_name = old_org.custom_label.value.lower()
            if norm_name in orgs_by_name:
                orgs_to_delete.add(old_org.pk)
                new_org = orgs_by_name[norm_name]
                for affil in affils_by_org_id[old_org.pk]:
                    affil.organization = new_org
                    affiliations_to_update.append(affil)
            elif norm_name in ambiguous_names_in_ror:
                ambiguous_names_in_db.add(norm_name)

        # Run the update and delete operations
        ControlledAffiliation.objects.bulk_update(
            affiliations_to_update, ["organization"], batch_size=3600
        )
        Organization.objects.filter(pk__in=orgs_to_delete).delete()

        # Report back to user
        num_after = self.filter(
            ror_id="",
            custom_label__isnull=False,
        ).count()
        deduplicated = num_before - num_after
        percent_matched = round(100 * deduplicated / num_before)
        logger.debug(
            f"Matched {deduplicated} organizations ({percent_matched}%) to ROR records."
        )
        logger.debug(f"{num_after} uncontrolled organizations remain.")
        if ambiguous_names_in_db:
            logger.debug(
                f"Some ambiguous names ({len(ambiguous_names_in_db)}) could "
                f"nearly be matched but were not globally unique. "
            )
            # logger.debug(f'Ambiguous names: {ambiguous_names_in_db}')

        total_affils_with_org = ControlledAffiliation.objects.filter(
            organization__isnull=False,
        ).count()
        affils_with_controlled_org = ControlledAffiliation.objects.filter(
            models.Q(organization__isnull=False) & ~models.Q(organization__ror_id=""),
        ).count()
        ror_controlled_affils_percent = round(
            100 * affils_with_controlled_org / total_affils_with_org
        )
        logger.debug(
            f"{affils_with_controlled_org} ({ror_controlled_affils_percent}%) of the "
            f"affiliations in this Janeway instance are now linked to ROR data."
        )


class OrganizationManager(models.Manager):
    def get_queryset(self):
        return OrganizationQueryset(self.model)

    def ror_ids_and_timestamps(self):
        ror_ids_and_timestamps = {}
        organizations = self.exclude(ror_id="")
        for ror_id, ts in organizations.values_list("ror_id", "ror_record_timestamp"):
            ror_ids_and_timestamps[ror_id] = ts
        return ror_ids_and_timestamps

    def bulk_link_locations_from_ror(self, ror_records):
        locations_by_geonames_id = {
            loc.geonames_id: loc
            for loc in Location.objects.filter(
                geonames_id__isnull=False,
            )
        }
        organizations_by_ror_id = {
            org.ror_id: org
            for org in self.filter(~models.Q(ror_id__exact="")).prefetch_related(
                "locations"
            )
        }
        organization_location_links = []
        logger.debug(f"Linking locations")
        for record in ror_records:
            ror_id = os.path.split(record.get("id", ""))[-1]
            organization = organizations_by_ror_id[ror_id]
            janeway_geonames_ids = set(
                [loc.geonames_id for loc in organization.locations.all()]
            )
            ror_geonames_ids = set(
                [loc.get("geonames_id") for loc in record.get("locations", [])]
            )

            # Unlink locations that have been removed from the record.
            # Do this without a bulk operation because it is likely to be uncommon.
            for geonames_id in janeway_geonames_ids - ror_geonames_ids:
                location = locations_by_geonames_id[geonames_id]
                organization.locations.remove(location)

            # Link locations that have been added to the record.
            for geonames_id in ror_geonames_ids - janeway_geonames_ids:
                location = locations_by_geonames_id[geonames_id]
                organization_location_links.append(
                    Organization.locations.through(
                        organization_id=organization.pk,
                        location_id=location.pk,
                    )
                )

        Organization.locations.through.objects.bulk_create(organization_location_links)

    def bulk_create_from_ror(self, ror_records):
        new_organizations = []
        logger.debug(f"Importing organizations")
        for record in ror_records:
            ror_id = os.path.split(record.get("id", ""))[-1]
            last_modified = record.get("admin", {}).get("last_modified", {})
            website = ""
            for link in record.get("links", []):
                if link.get("type") == "website":
                    website = link.get("value", "")
                    break
            ror_status = record.get("status", Organization.RORStatus.UNKNOWN)
            new_organizations.append(
                Organization(
                    ror_id=ror_id,
                    ror_status=ror_status,
                    ror_record_timestamp=last_modified.get("date", ""),
                    website=website,
                )
            )
        return self.bulk_create(new_organizations)

    @transaction.atomic
    def bulk_update_from_ror(self, ror_records):
        """
        Bulk updates organizations from ROR records.
        """
        organizations_by_ror_id = {
            org.ror_id: org for org in self.filter(~models.Q(ror_id__exact=""))
        }
        organizations_to_update = []
        fields_to_update = set()
        logger.debug(f"Updating organizations")
        for record in ror_records:
            ror_id = os.path.split(record.get("id", ""))[-1]
            organization = organizations_by_ror_id[ror_id]

            last_modified = record.get("admin", {}).get("last_modified", {})
            timestamp = last_modified.get("date", "")
            if organization.ror_record_timestamp != timestamp:
                organization.ror_record_timestamp = timestamp
                fields_to_update.add("ror_record_timestamp")

            website = ""
            for link in record.get("links", []):
                if link.get("type") == "website":
                    website = link.get("value", "")
                    break
            if organization.website != website:
                organization.website = website
                fields_to_update.add("website")

            ror_status = record.get("status", Organization.RORStatus.UNKNOWN)
            if organization.ror_status != ror_status:
                organization.ror_status = ror_status
                fields_to_update.add("ror_status")

            organizations_to_update.append(organization)

        if organizations_to_update and fields_to_update:
            return Organization.objects.bulk_update(
                organizations_to_update,
                fields_to_update,
            )
        else:
            return []

    def manage_ror_import(self, ror_import, limit=0):
        """
        Opens a previously downloaded data dump from
        ROR's Zenodo endpoint, processes the records,
        and records errors for exceptions raised during creation.
        https://ror.readme.io/v2/docs/data-dump
        """
        logger.debug(f"Running ROR import with limit={limit}")
        num_errors_before = RORImportError.objects.count()
        with zipfile.ZipFile(ror_import.zip_path, mode="r") as zip_ref:
            for file_info in zip_ref.infolist():
                if file_info.filename.endswith("v2.json"):
                    string = zip_ref.read(file_info).decode()
                    if limit:
                        records = json.loads(string)[:limit]
                    else:
                        records = json.loads(string)
                    break

        new_records = ror_import.filter_new_records(
            records,
            self.ror_ids_and_timestamps(),
        )
        if new_records:
            try:
                Location.objects.bulk_create_from_ror(new_records)
                Organization.objects.bulk_create_from_ror(new_records)
                Organization.objects.bulk_link_locations_from_ror(new_records)
                OrganizationName.objects.bulk_create_from_ror(new_records)
            except Exception as error:
                message = f"{type(error)}: {error}"
                RORImportError.objects.create(
                    ror_import=ror_import,
                    message=message,
                )

        # Update modified records
        updated_records = ror_import.filter_updated_records(
            records,
            self.ror_ids_and_timestamps(),
        )
        if updated_records:
            try:
                with transaction.atomic():
                    Location.objects.bulk_update_from_ror(updated_records)
                    Organization.objects.bulk_update_from_ror(updated_records)
                    Organization.objects.bulk_link_locations_from_ror(updated_records)
                    OrganizationName.objects.bulk_update_from_ror(updated_records)
            except Exception as error:
                message = f"{type(error)}: {error}"
                RORImportError.objects.create(
                    ror_import=ror_import,
                    message=message,
                )

        if not new_records and not updated_records:
            ror_import.status = ror_import.RORImportStatus.IS_UNNECESSARY
        else:
            ror_import.status = ror_import.RORImportStatus.IS_SUCCESSFUL
        ror_import.stopped = timezone.now()
        ror_import.save()

        num_errors_after = RORImportError.objects.count()
        if num_errors_after > num_errors_before:
            logger.warn(
                f"ROR import errors logged: {num_errors_after - num_errors_before}"
            )


def validate_ror_id(ror_id):
    ror_regex = r"^0[a-hj-km-np-tv-z|0-9]{6}[0-9]{2}$"
    prog = re.compile(ror_regex)
    if not prog.match(ror_id):
        raise ValidationError(f"{ror_id} is not a valid ROR identifier")


class Organization(models.Model):
    class RORStatus(models.TextChoices):
        ACTIVE = "active", _("Active")
        INACTIVE = "inactive", _("Inactive")
        WITHDRAWN = "withdrawn", _("Withdrawn")
        UNKNOWN = "unknown", _("Unknown")

    ror_id = models.CharField(
        blank=True,
        max_length=10,
        validators=[validate_ror_id],
        verbose_name="ROR ID",
        help_text="Non-URI form of Research Organization Registry identifier",
    )
    ror_status = models.CharField(
        blank=True,
        max_length=10,
        choices=RORStatus.choices,
        default=RORStatus.UNKNOWN,
    )
    ror_record_timestamp = models.CharField(
        max_length=10,
        blank=True,
        help_text="The admin.last_modified.date string from ROR data",
    )
    website = models.CharField(
        blank=True,
        max_length=2000,
    )
    locations = models.ManyToManyField(
        "Location",
        blank=True,
        null=True,
    )
    objects = OrganizationManager()

    class Meta:
        ordering = ("ror_display__value", "custom_label__value")
        constraints = [
            models.UniqueConstraint(
                fields=["ror_id"],
                condition=~models.Q(ror_id__exact=""),
                name="filled_unique",
            )
        ]

    @property
    def name_location(self):
        elements = [
            str(self.name) if self.name else "",
            str(self.location) if self.location else "",
        ]
        return ", ".join([element for element in elements if element])

    def __str__(self):
        return str(self.name) if self.name else ""

    @property
    def uri(self):
        return f"https://ror.org/{self.ror_id}" if self.ror_id else ""

    @property
    def name(self):
        """
        Return the OrganizationName that ROR uses for display, or if none,
        the first one that was manually entered, or if none,
        the first one designated by ROR as a label.
        Can be expanded in future to support choosing a label by language.
        """
        try:
            return self.ror_display
        except Organization.ror_display.RelatedObjectDoesNotExist:
            try:
                return self.custom_label
            except Organization.custom_label.RelatedObjectDoesNotExist:
                return self.labels.first()

    @property
    def location(self):
        """
        Return the first location.
        """
        return self.locations.first() if self.locations else None

    @property
    def country(self):
        """
        Return the country of the first location.
        """
        return self.location.country if self.location else None

    @property
    def names(self):
        """
        All names.
        """
        return OrganizationName.objects.filter(
            models.Q(ror_display_for=self)
            | models.Q(custom_label_for=self)
            | models.Q(label_for=self)
            | models.Q(alias_for=self)
            | models.Q(acronym_for=self),
        )

    @property
    def also_known_as(self):
        """
        All names excluding the ROR display name.
        """
        return self.names.exclude(ror_display_for=self)

    @classmethod
    def get_or_create_without_ror(
        cls,
        institution="",
        country="",
        account=None,
        frozen_author=None,
        preprint_author=None,
    ):
        """
        Backwards-compatible API for finding a matching organization,
        or creating one along with a location that just records country.
        Intended for use in batch importers where ROR data is not available
        in the data being imported.
        Does not support ROR ids, ROR name types, or geonames locations.

        :type institution: str
        :param country: ISO-3166-1 alpha-2 country code or Janeway Country object
        :type country: str or core.models.Country
        :type account: core.models.Account
        :type frozen_author: submission.models.FrozenAuthor
        :type preprint_author: repository.models.PreprintAuthor
        """

        created = False
        # Is there a single exact match in the
        # canonical name data from ROR (e.g. labels)?
        try:
            organization = cls.objects.get(labels__value=institution)
        except (cls.DoesNotExist, cls.MultipleObjectsReturned):
            # Or maybe one in the alternate name data
            # from ROR (e.g. aliases)?
            try:
                organization = cls.objects.get(aliases__value=institution)
            except (cls.DoesNotExist, cls.MultipleObjectsReturned):
                # Or maybe a primary affiliation has already been
                # entered without a ROR for this
                # account / frozen author / preprint author?
                try:
                    # If there is no `institution`, this method is being used to update
                    # the department or country in isolation, so we want the primary
                    # affiliation's org regardless of what its custom label is.
                    query = models.Q(
                        controlledaffiliation__is_primary=True,
                        controlledaffiliation__account=account,
                        controlledaffiliation__frozen_author=frozen_author,
                        controlledaffiliation__preprint_author=preprint_author,
                        ror_id__exact="",
                    )
                    # If there is an institution name, we should only match organizations
                    # with that as a custom label.
                    if institution:
                        query &= models.Q(custom_label__value=institution)
                    organization = cls.objects.get(query)
                except (cls.DoesNotExist, cls.MultipleObjectsReturned):
                    # Otherwise, create a new, disconnected record.
                    organization = cls.objects.create()
                    created = True

        # Set custom label if organization is not controlled by ROR
        if institution and not organization.ror_id:
            organization_name, _created = OrganizationName.objects.update_or_create(
                defaults={"value": institution},
                custom_label_for=organization,
            )

        # Prep the country
        if country and not isinstance(country, Country):
            try:
                country = Country.objects.get(code=country)
            except Country.DoesNotExist:
                country = ""

        # Set country data if organization is not controlled by ROR
        if country and not organization.ror_id:
            location, _created = Location.objects.get_or_create(
                name="",
                country=country,
            )
            organization.locations.clear()
            organization.locations.add(location)

        return organization, created


class ControlledAffiliation(models.Model):
    """
    A model to record affiliations for authors and other actors in Janeway.
    This model has authority control via the Organization model and its ties
    to the Research Organization Registry.
    Named ControlledAffiliation to avoid a name clash
    with an old field named 'affiliation'.
    """

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    frozen_author = models.ForeignKey(
        submission_models.FrozenAuthor,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    preprint_author = models.ForeignKey(
        repository_models.PreprintAuthor,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    title = models.CharField(
        blank=True,
        max_length=300,
        verbose_name=_("Title, position, or role"),
    )
    department = models.CharField(
        blank=True,
        max_length=300,
        verbose_name=_("Department, unit, or team"),
    )
    organization = models.ForeignKey(
        "Organization",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Each author or user can have one primary affiliation",
    )
    start = models.DateField(
        blank=True,
        null=True,
        verbose_name="Start date",
    )
    end = models.DateField(
        blank=True,
        null=True,
        verbose_name="End date",
        help_text="Leave empty for a current affiliation",
    )

    class Meta:
        constraints = [
            check_exclusive_fields_constraint(
                "controlled_affiliation",
                ["account", "frozen_author", "preprint_author"],
            )
        ]
        ordering = ["-is_primary", "-pk"]

    def title_department(self):
        elements = [
            self.title,
            self.department,
        ]
        return ", ".join([element for element in elements if element])

    def __str__(self):
        elements = [
            self.title,
            self.department,
            str(self.organization.name) if self.organization else "",
        ]
        return ", ".join([element for element in elements if element])

    @property
    def is_current(self):
        if self.start and self.start > timezone.now():
            return False
        if self.end and self.end < timezone.now():
            return False
        return True

    @classmethod
    def set_primary_if_first(cls, obj):
        other_affiliations = (
            cls.objects.filter(
                account=obj.account,
                frozen_author=obj.frozen_author,
                preprint_author=obj.preprint_author,
            )
            .exclude(pk=obj.pk)
            .exists()
        )
        if not other_affiliations:
            obj.is_primary = True

    @classmethod
    def keep_is_primary_unique(cls, obj):
        if obj.is_primary:
            cls.objects.filter(
                is_primary=True,
                account=obj.account,
                frozen_author=obj.frozen_author,
                preprint_author=obj.preprint_author,
            ).exclude(pk=obj.pk).update(
                is_primary=False,
            )

    @classmethod
    def get_primary(
        cls,
        affiliated_object,
        as_object=True,
    ):
        """
        Get the primary affiliation, or if none,
        the affiliation with the highest pk, or if none,
        an empty string.
        :param affiliated_object: Account, FrozenAuthor, PreprintAuthor
        :param as_object: whether to return a Python object
        """
        if not affiliated_object.affiliations.exists():
            return None if as_object else ""
        try:
            affil = affiliated_object.affiliations.get(is_primary=True)
        except ControlledAffiliation.DoesNotExist:
            affil = affiliated_object.affiliations.first()
        return affil if as_object else str(affil)

    @classmethod
    def get_or_create_without_ror(
        cls,
        institution="",
        department="",
        title="",
        country="",
        account=None,
        frozen_author=None,
        preprint_author=None,
        defaults=None,
    ):
        """
        Backwards-compatible API for setting affiliation from unstructured text.
        Intended for use in batch importers where ROR data is not available.
        Does not support ROR ids, multiple affiliations, or start or end dates.
        When possible, include department and country to create unified records.
        Only include one of author, frozen_author, or preprint_author.

        :param institution: the uncontrolled organization name as a string
        :type institution: str
        :type department: str
        :param country: ISO-3166-1 alpha-2 country code or Janeway Country object
        :type country: str or core.models.Country
        :type account: core.models.Account
        :type frozen_author: submission.models.FrozenAuthor
        :type preprint_author: repository.models.PreprintAuthor
        :param defaults: default dict passed to ControlledAffiliation.get_or_create:
        :type defaults: dict:
        """
        organization, _created = Organization.get_or_create_without_ror(
            institution=institution,
            country=country,
            account=account,
            frozen_author=frozen_author,
            preprint_author=preprint_author,
        )
        if not defaults:
            defaults = {}

        defaults.update(
            {
                "organization": organization,
            }
        )
        if department:
            defaults["department"] = department
        if title:
            defaults["title"] = title
        kwargs = {
            "is_primary": True,
            "account": account,
            "frozen_author": frozen_author,
            "preprint_author": preprint_author,
        }

        # Create or update the actual affiliation if the associated
        # account / frozen author / preprint author has been saved already
        try:
            affiliation, created = ControlledAffiliation.objects.update_or_create(
                defaults=defaults,
                **kwargs,
            )
        except (ValueError, IntegrityError):
            logger.warning(
                f"The affiliation could not be created "
                f"with defaults {defaults} and kwargs {kwargs}."
            )
            affiliation = None
            created = False
        return affiliation, created

    def save(self, *args, **kwargs):
        self.set_primary_if_first(self)
        self.keep_is_primary_unique(self)
        super().save(*args, **kwargs)


class LocationManager(models.Manager):
    def bulk_create_from_ror(self, ror_records):
        """
        Bulk creates location objects for which a matching Geonames ID
        is not found in Janeway.
        Guards against duplicate locations because the input
        ror_records will only have been filtered
        at the organization level, not the location level.
        """
        current_geonames_ids = set(
            loc.geonames_id for loc in self.all() if loc.geonames_id
        )
        countries_by_code = {country.code: country for country in Country.objects.all()}
        new_locations = []
        logger.debug(f"Importing locations")
        for record in ror_records:
            for record_location in record.get("locations"):
                geonames_id = record_location.get("geonames_id")
                if geonames_id and geonames_id not in current_geonames_ids:
                    details = record_location.get("geonames_details", {})
                    new_locations.append(
                        Location(
                            geonames_id=geonames_id,
                            name=details.get("name", ""),
                            country=countries_by_code.get(
                                details.get("country_code", "")
                            ),
                        )
                    )
                    current_geonames_ids.add(geonames_id)
        return Location.objects.bulk_create(new_locations)

    @transaction.atomic
    def bulk_update_from_ror(self, ror_records):
        """
        Bulk updates location objects for which a matching Geonames ID
        is found in Janeway.
        Also handles new location objects by calling Location.bulk_create_from_ror;
        this is needed when a ROR record has been modified by the addition of
        new locations.
        """
        locations_by_geonames_id = {
            loc.geonames_id: loc for loc in self.all() if loc.geonames_id
        }
        countries_by_code = {country.code: country for country in Country.objects.all()}
        locations_to_update = []
        ror_records_with_new_loc = []
        fields_to_update = set()
        logger.debug(f"Updating locations")
        for record in ror_records:
            for record_location in record.get("locations"):
                geonames_id = record_location.get("geonames_id")
                if not geonames_id:
                    break
                if geonames_id in locations_by_geonames_id:
                    details = record_location.get("geonames_details", {})
                    location = locations_by_geonames_id[geonames_id]
                    country = countries_by_code.get(details.get("country_code", ""))
                    if location.name != details.get("name", ""):
                        location.name = details.get("name", "")
                        fields_to_update.add("name")
                    if location.country != country:
                        location.country = country
                        fields_to_update.add("country")
                    locations_to_update.append(location)
                elif geonames_id not in locations_by_geonames_id:
                    ror_records_with_new_loc.append(record)
        if ror_records_with_new_loc:
            Location.objects.bulk_create_from_ror(ror_records_with_new_loc)
        if locations_to_update and fields_to_update:
            return Location.objects.bulk_update(
                locations_to_update,
                fields_to_update,
            )
        else:
            return []


class Location(models.Model):
    name = models.CharField(
        max_length=200,
        help_text="City or place name",
        blank=True,
    )
    country = models.ForeignKey(
        Country,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    geonames_id = models.IntegerField(
        blank=True,
        null=True,
    )
    objects = LocationManager()

    def __str__(self):
        elements = [
            self.name if self.name else "",
            str(self.country) if self.country else "",
        ]
        return ", ".join([element for element in elements if element])
