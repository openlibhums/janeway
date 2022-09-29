__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import os
import uuid
import statistics
import json
from datetime import timedelta
import pytz
from hijack.signals import hijack_started, hijack_ended
import warnings

from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import (
    connection,
    models,
    transaction,
)
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
import swapper

from core import files, validators
from core.file_system import JanewayFileSystemStorage
from core.model_utils import (
    AbstractLastModifiedModel,
    AbstractSiteModel,
    PGCaseInsensitiveEmailField,
    SearchLookup,
)
from review import models as review_models
from copyediting import models as copyediting_models
from submission import models as submission_models
from utils.logger import get_logger
from utils import logic as utils_logic

fs = JanewayFileSystemStorage()
logger = get_logger(__name__)

IMAGE_GALLEY_TEMPLATE = """
    <img class="responsive-img" src={url} alt="{alt}">
"""

def profile_images_upload_path(instance, filename):
    try:
        filename = str(uuid.uuid4()) + '.' + str(filename.split('.')[1])
    except IndexError:
        filename = str(uuid.uuid4())

    path = "profile_images/"
    return os.path.join(path, filename)


SALUTATION_CHOICES = (
    ('Miss', 'Miss'),
    ('Ms', 'Ms'),
    ('Mrs', 'Mrs'),
    ('Mr', 'Mr'),
    ('Mx', 'Mx'),
    ('Dr', 'Dr'),
    ('Prof.', 'Prof.'),
)

COUNTRY_CHOICES = [(u'AF', u'Afghanistan'), (u'AX', u'\xc5land Islands'), (u'AL', u'Albania'),
                   (u'DZ', u'Algeria'), (u'AS', u'American Samoa'), (u'AD', u'Andorra'), (u'AO', u'Angola'),
                   (u'AI', u'Anguilla'), (u'AQ', u'Antarctica'), (u'AG', u'Antigua and Barbuda'), (u'AR', u'Argentina'),
                   (u'AM', u'Armenia'), (u'AW', u'Aruba'), (u'AU', u'Australia'), (u'AT', u'Austria'),
                   (u'AZ', u'Azerbaijan'), (u'BS', u'Bahamas'), (u'BH', u'Bahrain'), (u'BD', u'Bangladesh'),
                   (u'BB', u'Barbados'), (u'BY', u'Belarus'), (u'BE', u'Belgium'), (u'BZ', u'Belize'),
                   (u'BJ', u'Benin'), (u'BM', u'Bermuda'), (u'BT', u'Bhutan'),
                   (u'BO', u'Bolivia, Plurinational State of'), (u'BQ', u'Bonaire, Sint Eustatius and Saba'),
                   (u'BA', u'Bosnia and Herzegovina'), (u'BW', u'Botswana'), (u'BV', u'Bouvet Island'),
                   (u'BR', u'Brazil'), (u'IO', u'British Indian Ocean Territory'), (u'BN', u'Brunei Darussalam'),
                   (u'BG', u'Bulgaria'), (u'BF', u'Burkina Faso'), (u'BI', u'Burundi'), (u'KH', u'Cambodia'),
                   (u'CM', u'Cameroon'), (u'CA', u'Canada'), (u'CV', u'Cape Verde'), (u'KY', u'Cayman Islands'),
                   (u'CF', u'Central African Republic'), (u'TD', u'Chad'), (u'CL', u'Chile'), (u'CN', u'China'),
                   (u'CX', u'Christmas Island'), (u'CC', u'Cocos (Keeling) Islands'), (u'CO', u'Colombia'),
                   (u'KM', u'Comoros'), (u'CG', u'Congo'), (u'CD', u'Congo, The Democratic Republic of the'),
                   (u'CK', u'Cook Islands'), (u'CR', u'Costa Rica'), (u'CI', u"C\xf4te d'Ivoire"), (u'HR', u'Croatia'),
                   (u'CU', u'Cuba'), (u'CW', u'Cura\xe7ao'), (u'CY', u'Cyprus'), (u'CZ', u'Czech Republic'),
                   (u'DK', u'Denmark'), (u'DJ', u'Djibouti'), (u'DM', u'Dominica'), (u'DO', u'Dominican Republic'),
                   (u'EC', u'Ecuador'), (u'EG', u'Egypt'), (u'SV', u'El Salvador'), (u'GQ', u'Equatorial Guinea'),
                   (u'ER', u'Eritrea'), (u'EE', u'Estonia'), (u'ET', u'Ethiopia'),
                   (u'FK', u'Falkland Islands (Malvinas)'), (u'FO', u'Faroe Islands'), (u'FJ', u'Fiji'),
                   (u'FI', u'Finland'), (u'FR', u'France'), (u'GF', u'French Guiana'), (u'PF', u'French Polynesia'),
                   (u'TF', u'French Southern Territories'), (u'GA', u'Gabon'), (u'GM', u'Gambia'), (u'GE', u'Georgia'),
                   (u'DE', u'Germany'), (u'GH', u'Ghana'), (u'GI', u'Gibraltar'), (u'GR', u'Greece'),
                   (u'GL', u'Greenland'), (u'GD', u'Grenada'), (u'GP', u'Guadeloupe'), (u'GU', u'Guam'),
                   (u'GT', u'Guatemala'), (u'GG', u'Guernsey'), (u'GN', u'Guinea'), (u'GW', u'Guinea-Bissau'),
                   (u'GY', u'Guyana'), (u'HT', u'Haiti'), (u'HM', u'Heard Island and McDonald Islands'),
                   (u'VA', u'Holy See (Vatican City State)'), (u'HN', u'Honduras'), (u'HK', u'Hong Kong'),
                   (u'HU', u'Hungary'), (u'IS', u'Iceland'), (u'IN', u'India'), (u'ID', u'Indonesia'),
                   (u'IR', u'Iran, Islamic Republic of'), (u'IQ', u'Iraq'), (u'IE', u'Ireland'),
                   (u'IM', u'Isle of Man'), (u'IL', u'Israel'), (u'IT', u'Italy'), (u'JM', u'Jamaica'),
                   (u'JP', u'Japan'), (u'JE', u'Jersey'), (u'JO', u'Jordan'), (u'KZ', u'Kazakhstan'), (u'KE', u'Kenya'),
                   (u'KI', u'Kiribati'), (u'KP', u"Korea, Democratic People's Republic of"),
                   (u'KR', u'Korea, Republic of'), (u'KW', u'Kuwait'), (u'KG', u'Kyrgyzstan'),
                   (u'LA', u"Lao People's Democratic Republic"), (u'LV', u'Latvia'), (u'LB', u'Lebanon'),
                   (u'LS', u'Lesotho'), (u'LR', u'Liberia'), (u'LY', u'Libya'), (u'LI', u'Liechtenstein'),
                   (u'LT', u'Lithuania'), (u'LU', u'Luxembourg'), (u'MO', u'Macao'), (u'MK', u'Macedonia, Republic of'),
                   (u'MG', u'Madagascar'), (u'MW', u'Malawi'), (u'MY', u'Malaysia'), (u'MV', u'Maldives'),
                   (u'ML', u'Mali'), (u'MT', u'Malta'), (u'MH', u'Marshall Islands'), (u'MQ', u'Martinique'),
                   (u'MR', u'Mauritania'), (u'MU', u'Mauritius'), (u'YT', u'Mayotte'), (u'MX', u'Mexico'),
                   (u'FM', u'Micronesia, Federated States of'), (u'MD', u'Moldova, Republic of'), (u'MC', u'Monaco'),
                   (u'MN', u'Mongolia'), (u'ME', u'Montenegro'), (u'MS', u'Montserrat'), (u'MA', u'Morocco'),
                   (u'MZ', u'Mozambique'), (u'MM', u'Myanmar'), (u'NA', u'Namibia'), (u'NR', u'Nauru'),
                   (u'NP', u'Nepal'), (u'NL', u'Netherlands'), (u'NC', u'New Caledonia'), (u'NZ', u'New Zealand'),
                   (u'NI', u'Nicaragua'), (u'NE', u'Niger'), (u'NG', u'Nigeria'), (u'NU', u'Niue'),
                   (u'NF', u'Norfolk Island'), (u'MP', u'Northern Mariana Islands'), (u'NO', u'Norway'),
                   (u'OM', u'Oman'), (u'PK', u'Pakistan'), (u'PW', u'Palau'), (u'PS', u'Palestine, State of'),
                   (u'PA', u'Panama'), (u'PG', u'Papua New Guinea'), (u'PY', u'Paraguay'), (u'PE', u'Peru'),
                   (u'PH', u'Philippines'), (u'PN', u'Pitcairn'), (u'PL', u'Poland'), (u'PT', u'Portugal'),
                   (u'PR', u'Puerto Rico'), (u'QA', u'Qatar'), (u'RE', u'R\xe9union'), (u'RO', u'Romania'),
                   (u'RU', u'Russian Federation'), (u'RW', u'Rwanda'), (u'BL', u'Saint Barth\xe9lemy'),
                   (u'SH', u'Saint Helena, Ascension and Tristan da Cunha'), (u'KN', u'Saint Kitts and Nevis'),
                   (u'LC', u'Saint Lucia'), (u'MF', u'Saint Martin (French part)'),
                   (u'PM', u'Saint Pierre and Miquelon'), (u'VC', u'Saint Vincent and the Grenadines'),
                   (u'WS', u'Samoa'), (u'SM', u'San Marino'), (u'ST', u'Sao Tome and Principe'),
                   (u'SA', u'Saudi Arabia'), (u'SN', u'Senegal'), (u'RS', u'Serbia'), (u'SC', u'Seychelles'),
                   (u'SL', u'Sierra Leone'), (u'SG', u'Singapore'), (u'SX', u'Sint Maarten (Dutch part)'),
                   (u'SK', u'Slovakia'), (u'SI', u'Slovenia'), (u'SB', u'Solomon Islands'), (u'SO', u'Somalia'),
                   (u'ZA', u'South Africa'), (u'GS', u'South Georgia and the South Sandwich Islands'),
                   (u'ES', u'Spain'), (u'LK', u'Sri Lanka'), (u'SD', u'Sudan'), (u'SR', u'Suriname'),
                   (u'SS', u'South Sudan'), (u'SJ', u'Svalbard and Jan Mayen'), (u'SZ', u'Swaziland'),
                   (u'SE', u'Sweden'), (u'CH', u'Switzerland'), (u'SY', u'Syrian Arab Republic'),
                   (u'TW', u'Taiwan, Province of China'), (u'TJ', u'Tajikistan'),
                   (u'TZ', u'Tanzania, United Republic of'), (u'TH', u'Thailand'), (u'TL', u'Timor-Leste'),
                   (u'TG', u'Togo'), (u'TK', u'Tokelau'), (u'TO', u'Tonga'), (u'TT', u'Trinidad and Tobago'),
                   (u'TN', u'Tunisia'), (u'TR', u'Turkey'), (u'TM', u'Turkmenistan'),
                   (u'TC', u'Turks and Caicos Islands'), (u'TV', u'Tuvalu'), (u'UG', u'Uganda'), (u'UA', u'Ukraine'),
                   (u'AE', u'United Arab Emirates'), (u'GB', u'United Kingdom'), (u'US', u'United States'),
                   (u'UM', u'United States Minor Outlying Islands'), (u'UY', u'Uruguay'), (u'UZ', u'Uzbekistan'),
                   (u'VU', u'Vanuatu'), (u'VE', u'Venezuela, Bolivarian Republic of'), (u'VN', u'Viet Nam'),
                   (u'VG', u'Virgin Islands, British'), (u'VI', u'Virgin Islands, U.S.'), (u'WF', u'Wallis and Futuna'),
                   (u'EH', u'Western Sahara'), (u'YE', u'Yemen'), (u'ZM', u'Zambia'), (u'ZW', u'Zimbabwe')]

TIMEZONE_CHOICES = tuple(zip(pytz.all_timezones, pytz.all_timezones))

SUMMERNOTE_SENTINEL = '<p><br></p>'


class Country(models.Model):
    code = models.TextField(max_length=5)
    name = models.TextField(max_length=255)

    class Meta:
        ordering = ('name', 'code')
        verbose_name_plural = 'countries'

    def __str__(self):
        return self.name


class AccountQuerySet(models.query.QuerySet):
    def create(self, **kwargs):
        obj = self.model(**kwargs)
        obj.clean()
        self._for_write = True
        obj.save(force_insert=True, using=self.db)
        return obj


class AccountManager(BaseUserManager):
    def create_user(self, email, password=None, **kwargs):
        if not email:
            raise ValueError('Users must have a valid email address.')

        account = self.model(
            email=self.normalize_email(email),
            username=email.lower(),
        )

        account.set_password(password)
        account.save()

        return account

    def create_superuser(self, email, password, **kwargs):
        account = self.create_user(email, password, **kwargs)

        account.is_staff = True
        account.is_admin = True
        account.is_active = True
        account.is_superuser = True
        account.save()

        return account

    def get_queryset(self):
        return AccountQuerySet(self.model)


class Account(AbstractBaseUser, PermissionsMixin):
    email = PGCaseInsensitiveEmailField(unique=True, verbose_name=_('Email'))
    username = models.CharField(max_length=254, unique=True, verbose_name=_('Username'))

    first_name = models.CharField(max_length=300, null=True, blank=False, verbose_name=_('First name'))
    middle_name = models.CharField(max_length=300, null=True, blank=True, verbose_name=_('Middle name'))
    last_name = models.CharField(max_length=300, null=True, blank=False, verbose_name=_('Last name'))

    activation_code = models.CharField(max_length=100, null=True, blank=True)
    salutation = models.CharField(max_length=10, choices=SALUTATION_CHOICES, null=True, blank=True,
                                  verbose_name=_('Salutation'))
    suffix = models.CharField(
        max_length=300,
        null=True,
        blank=True,
        help_text=_('Name suffix eg. jr'),
    )
    biography = models.TextField(null=True, blank=True, verbose_name=_('Biography'))
    orcid = models.CharField(max_length=40, null=True, blank=True, verbose_name=_('ORCiD'))
    institution = models.CharField(max_length=1000, null=True, blank=True, verbose_name=_('Institution'))
    department = models.CharField(max_length=300, null=True, blank=True, verbose_name=_('Department'))
    twitter = models.CharField(max_length=300, null=True, blank=True, verbose_name="Twitter Handle")
    facebook = models.CharField(max_length=300, null=True, blank=True, verbose_name="Facebook Handle")
    linkedin = models.CharField(max_length=300, null=True, blank=True, verbose_name="Linkedin Profile")
    website = models.URLField(max_length=300, null=True, blank=True, verbose_name="Website")
    github = models.CharField(max_length=300, null=True, blank=True, verbose_name="Github Username")
    profile_image = models.ImageField(upload_to=profile_images_upload_path, null=True, blank=True, storage=fs)
    email_sent = models.DateTimeField(blank=True, null=True)
    date_confirmed = models.DateTimeField(blank=True, null=True)
    confirmation_code = models.CharField(max_length=200, blank=True, null=True)
    signature = models.TextField(null=True, blank=True)
    interest = models.ManyToManyField('Interest', null=True, blank=True)
    country = models.ForeignKey(Country, null=True, blank=True, verbose_name=_('Country'))
    preferred_timezone = models.CharField(max_length=300, null=True, blank=True, choices=TIMEZONE_CHOICES)

    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    enable_digest = models.BooleanField(default=False)
    enable_public_profile = models.BooleanField(default=False, help_text='If enabled, your basic profile will be '
                                                'available to the public.')

    date_joined = models.DateTimeField(default=timezone.now)

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    objects = AccountManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        ordering = ('first_name', 'last_name', 'username')
        unique_together = ('email', 'username')

    def clean(self, *args, **kwargs):
        """ Normalizes the email address

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
        rules = [
            lambda s: len(password) >= request.press.password_length or 'length'
        ]

        if request.press.password_upper:
            rules.append(lambda password: any(x.isupper() for x in password) or 'upper')

        if request.press.password_number:
            rules.append(lambda password: any(x.isdigit() for x in password) or 'digit')

        problems = [p for p in [r(password) for r in rules] if p != True]

        return problems

    def string_id(self):
        return str(self.id)

    def get_full_name(self):
        return '{0} {1}{2}{3}'.format(self.first_name, self.middle_name, ' ' if self.middle_name != "" else "",
                                      self.last_name)

    def get_short_name(self):
        return self.first_name

    @property
    def first_names(self):
        return '{0}{1}{2}'.format(self.first_name, ' ' if self.middle_name is not None else '',
                                  self.middle_name if self.middle_name is not None else '')

    def full_name(self):
        name_elements = [
            self.first_name,
            self.middle_name,
            self.last_name
        ]
        return " ".join([name for name in name_elements if name])

    def salutation_name(self):
        if self.salutation:
            return u"%s %s" % (self.salutation, self.last_name)
        else:
            return u"%s %s" % (self.first_name, self.last_name)

    def initials(self):
        if self.first_name and self.last_name:
            if self.middle_name:
                return u"%s%s%s" % (self.first_name[:1], self.middle_name[:1], self.last_name[:1])
            else:
                return u"%s%s" % (self.first_name[:1], self.last_name[:1])
        else:
            return 'N/A'

    def affiliation(self):
        if self.institution and self.department:
            return "{}, {}".format(self.department, self.institution)
        elif self.institution:
            return self.institution
        else:
            return ''

    def active_reviews(self):
        return review_models.ReviewAssignment.objects.filter(
            reviewer=self,
            is_complete=False,
        )

    def active_copyedits(self):
        return copyediting_models.CopyeditAssignment.objects.filter(copyeditor=self, copyedit_acknowledged=False)

    def active_typesets(self):
        """
        Gathers typesetting tasks a user account has and returns a list of them.
        :return: List of objects
        """
        from production import models as production_models
        from proofing import models as proofing_models
        task_list = list()
        typeset_tasks = production_models.TypesetTask.objects.filter(typesetter=self, completed__isnull=True)
        proofing_tasks = proofing_models.TypesetterProofingTask.objects.filter(typesetter=self, completed__isnull=True)

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

    def check_role(self, journal, role):
        return AccountRole.objects.filter(
            user=self,
            journal=journal,
            role__slug=role
        ).exists() or self.is_staff

    def is_editor(self, request, journal=None):
        if not journal:
            return self.check_role(request.journal, 'editor')
        else:
            return self.check_role(journal, 'editor')

    def is_section_editor(self, request):
        return self.check_role(request.journal, 'section-editor')

    def has_an_editor_role(self, request):
        editor = self.is_editor(request)
        section_editor = self.is_section_editor(request)

        if editor or section_editor:
            return True

        return False

    def is_reviewer(self, request):
        return self.check_role(request.journal, 'reviewer')

    def is_author(self, request):
        return self.check_role(request.journal, 'author')

    def is_proofreader(self, request):
        return self.check_role(request.journal, 'proofreader')

    def is_production(self, request):
        return self.check_role(request.journal, 'production')

    def is_copyeditor(self, request):
        return self.check_role(request.journal, 'copyeditor')

    def is_typesetter(self, request):
        return self.check_role(request.journal, 'typesetter')

    def is_proofing_manager(self, request):
        return self.check_role(request.journal, 'proofing-manager')

    def is_repository_manager(self, repository):
        if self in repository.managers.all():
            return True

        return False

    def is_preprint_editor(self, request):
        if self in request.press.preprint_editors():
            return True

        return False

    def snapshot_self(self, article, force_update=True):
        frozen_dict = {
            'first_name': self.first_name,
            'middle_name': self.middle_name,
            'last_name': self.last_name,
            'institution': self.institution,
            'department': self.department,
            'display_email': True if self == article.correspondence_author else False,
            'name_suffix': self.suffix,
        }

        frozen_author = self.frozen_author(article)

        if frozen_author and force_update:
            for k, v in frozen_dict.items():
                setattr(frozen_author, k, v)
            frozen_author.save()

        else:
            try:
                order_object = article.articleauthororder_set.get(author=self)
            except submission_models.ArticleAuthorOrder.DoesNotExist:
                order_integer = article.next_author_sort()
                order_object, c = submission_models.ArticleAuthorOrder.objects.get_or_create(
                    article=article,
                    author=self,
                    defaults={'order': order_integer}
                )

            submission_models.FrozenAuthor.objects.get_or_create(
                author=self,
                article=article,
                defaults=dict(order=order_object.order, **frozen_dict)
            )

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
        reviewer_ratings = review_models.ReviewerRating.objects.filter(assignment__reviewer=self)
        ratings = [reviewer_rating.rating for reviewer_rating in reviewer_ratings]

        return statistics.mean(ratings) if ratings else 0

    def articles(self):
        return submission_models.Article.objects.filter(authors__in=[self])

    def published_articles(self):
        articles = submission_models.Article.objects.filter(
            authors=self,
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
        username = '{pk}{first_name}{last_name}'.format(pk=self.pk,
                                                        first_name=self.first_name,
                                                        last_name=self.last_name)[:30]
        return username.lower()


def generate_expiry_date():
    return timezone.now() + timedelta(days=1)


class OrcidToken(models.Model):
    token = models.UUIDField(default=uuid.uuid4)
    orcid = models.CharField(max_length=200)
    expiry = models.DateTimeField(default=generate_expiry_date, verbose_name='Expires on')

    def __str__(self):
        return "ORCiD Token [{0}] - {1}".format(self.orcid, self.token)


class PasswordResetToken(models.Model):
    account = models.ForeignKey(Account)
    token = models.CharField(max_length=300, default=uuid.uuid4)
    expiry = models.DateTimeField(default=generate_expiry_date, verbose_name='Expires on')
    expired = models.BooleanField(default=False)

    def __str__(self):
        return "Account: {0}, Expiry: {1}, [{2}]".format(self.account.full_name(),
                                                         self.expiry,
                                                         'Expired' if self.expired else 'Active')

    def has_expired(self):
        if self.expired:
            return True
        elif self.expiry < timezone.now():
            return True
        else:
            return False


class Role(models.Model):
    name = models.CharField(
        max_length=100,
        help_text='Display name for this role '
                  '(can include spaces and capital letters)',
    )
    slug = models.CharField(
        max_length=100,
        help_text='Normalized string representing this role '
                  'containing only lowercase letters and hyphens.',
    )

    class Meta:
        ordering = ('name', 'slug')

    def __str__(self):
        return u'%s' % self.name

    def __repr__(self):
        return u'%s' % self.name


class AccountRole(models.Model):
    user = models.ForeignKey(Account)
    journal = models.ForeignKey('journal.Journal')
    role = models.ForeignKey(Role)

    class Meta:
        unique_together = ('journal', 'user', 'role')

    def __str__(self):
        return "{0} {1} {2}".format(self.user, self.journal, self.role.name)


class Interest(models.Model):
    name = models.CharField(max_length=250)

    def __str__(self):
        return u'%s' % self.name

    def __repr__(self):
        return u'%s' % self.name


setting_types = (
    ('rich-text', 'Rich Text'),
    ('text', 'Text'),
    ('char', 'Characters'),
    ('number', 'Number'),
    ('boolean', 'Boolean'),
    ('file', 'File'),
    ('select', 'Select'),
    ('json', 'JSON'),
)

privacy_types = (
    ('public', 'Public'),
    ('typesetters', 'Typesetters'),
    ('proofreaders', 'Proofreaders'),
    ('copyeditors', 'Copyedtiors'),
    ('editors', 'Editors'),
    ('owner', 'Owner'),
)


class SettingGroup(models.Model):
    VALIDATORS = {
        "email": (validators.validate_email_setting,),
    }
    name = models.CharField(max_length=100)
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return u'%s' % self.name

    def __repr__(self):
        return u'%s' % self.name

    def validate(self, value):
        if self.name in self.VALIDATORS:
            for validator in self.VALIDATORS[self.name]:
                validator(value)


class Setting(models.Model):
    VALIDATORS = {}
    name = models.CharField(max_length=100)
    group = models.ForeignKey(SettingGroup)
    types = models.CharField(max_length=20, choices=setting_types)
    pretty_name = models.CharField(max_length=100, default='')
    description = models.TextField(null=True, blank=True)

    is_translatable = models.BooleanField(default=False)

    class Meta:
        ordering = ('group', 'name')

    def __str__(self):
        return u'%s' % self.name

    def __repr__(self):
        return u'%s' % self.name

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
    journal = models.ForeignKey('journal.Journal', null=True, blank=True)
    setting = models.ForeignKey(Setting)
    value = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = (
                ("journal", "setting"),
        )

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
        """ Converts string values of settings to proper values

        :return: a value
        """

        if self.setting.types == 'boolean' and self.value == 'on':
            return True
        elif self.setting.types == 'boolean':
            return False
        elif self.setting.types == 'number':
            try:
                return int(self.value)
            except BaseException:
                return 0
        elif self.setting.types == 'json' and self.value:
            return json.loads(self.value)
        elif self.setting.types == 'rich-text' and self.value == SUMMERNOTE_SENTINEL:
            return ''
        else:
            return self.value

    @property
    def render_value(self):
        """ Converts string values of settings to values for rendering

        :return: a value
        """
        if self.setting.types == 'boolean' and not self.value:
            return "off"
        elif self.setting.types == 'boolean':
            return "on"
        elif self.setting.types == 'file':
            if self.journal:
                return self.journal.site_url(
                        reverse("journal_file",self.value))
            else:
                return self.press.site_url(
                        reverse("serve_press_file", self.value))
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

    def save(self, *args, **kwargs):
        self.validate()
        super().save(*args, **kwargs)


class File(AbstractLastModifiedModel):
    article_id = models.PositiveIntegerField(blank=True, null=True, verbose_name="Article PK")

    mime_type = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=1000)
    uuid_filename = models.CharField(max_length=100)
    label = models.CharField(max_length=1000, null=True, blank=True, verbose_name=_('Label'))
    description = models.TextField(null=True, blank=True, verbose_name=_('Description'))
    sequence = models.IntegerField(default=1)
    owner = models.ForeignKey(Account, null=True, on_delete=models.SET_NULL)
    privacy = models.CharField(max_length=20, choices=privacy_types, default="owner")

    date_uploaded = models.DateTimeField(auto_now_add=True)

    is_galley = models.BooleanField(default=False)

    # Remote galley handling
    is_remote = models.BooleanField(default=False)
    remote_url = models.URLField(blank=True, null=True, verbose_name="Remote URL of file")

    history = models.ManyToManyField(
        'FileHistory',
        blank=True,
    )
    text = models.OneToOneField(swapper.get_model_name('core', 'FileText'),
        blank=True, null=True,
        related_name="file",
        on_delete=models.SET_NULL,
    )

    class Meta:
        ordering = ('sequence', 'pk')

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
                print('file_not_found')
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
        return os.path.join(settings.BASE_DIR, 'files', 'press', 'preprints', str(self.uuid_filename))

    def press_path(self):
        return os.path.join(settings.BASE_DIR, 'files', 'press', str(self.uuid_filename))

    def journal_path(self, journal):
        return os.path.join(settings.BASE_DIR, 'files', 'journals', str(journal.pk), str(self.uuid_filename))
    
    def self_article_path(self):
        if self.article_id:
            return os.path.join(settings.BASE_DIR, 'files', 'articles', str(self.article_id), str(self.uuid_filename))

    def url(self):
        from core.middleware import GlobalRequestMiddleware
        request = GlobalRequestMiddleware.get_current_request()
        url_kwargs = {'file_id': self.pk}

        if request.journal and self.article_id:
            raise NotImplementedError
        elif request.journal:
            raise NotImplementedError
        else:
            return reverse(
                'serve_press_file',
                kwargs=url_kwargs,
            )

    def get_file(self, article):
        return files.get_file(self, article)

    def get_file_path(self, article):
        return os.path.join(settings.BASE_DIR, 'files', 'articles', str(article.id), str(self.uuid_filename))

    def get_file_size(self, article):
        return os.path.getsize(os.path.join(settings.BASE_DIR, 'files', 'articles', str(article.id),
                                            str(self.uuid_filename)))

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
                return 'No checksum could be calculated.'
        else:
            logger.error(
                'Galley file ({file_id}) found with no article_id.'.format(
                    file_id=self.pk
                ), extra={'stack': True}
            )
            return 'No checksum could be calculated.'

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
                    'Article {pk} has no author records'.format(
                        pk=article.pk
                    )
                )
                author_surname = ''

            file_name = '{code}-{pk}{surname}{extension}'.format(
                code=article.journal.code,
                pk=article.pk,
                surname=author_surname,
                extension=extension
            )
            return file_name.lower()
        else:
            return self.original_filename

    def index_full_text(self, save=True):
        """ Extracts text from the File and stores it into an indexed model

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
        warnings.warn("'date_modified' is deprecated and will be removed, use last_modified instead.")
        return self.last_modified

    def __str__(self):
        return u'%s' % self.original_filename

    def __repr__(self):
        return u'%s' % self.original_filename


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
        swappable = swapper.swappable_setting('core', 'FileText')
    pass


class PGFileText(AbstractFileText):
    contents = SearchVectorField(blank=True, null=True, editable=False)

    class Meta:
        required_db_vendor = "postgresql"


    @staticmethod
    def preprocess_contents(text, lang=None):
        """ Casts the given text into a postgres TSVector

        The result can be cached so that there is no need to store the original
        text and also speed up the search queries.
        The drawback is that the cached TSVector needs to be regenerated
        whenever the underlying field changes.

        Postgres `to_tsvector()` function normalises the input before handing it
        over to `tsvector()`.
        """
        cursor = connection.cursor()
        # Remove NULL characters before vectorising
        text = text.replace("\x00", "\uFFFD")
        result = cursor.execute("SELECT to_tsvector(%s) as vector", [text])
        return cursor.fetchone()[0]


@receiver(models.signals.pre_save, sender=File)
def update_file_index(sender, instance, **kwargs):
    """ Updates the indexed contents in the database """
    if not instance.pk:
        return False

    if settings.ENABLE_FULL_TEXT_SEARCH and instance.text:
        instance.index_full_text(save=False)


class FileHistory(models.Model):
    article_id = models.PositiveIntegerField(blank=True, null=True, verbose_name="Article PK")

    mime_type = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=1000)
    uuid_filename = models.CharField(max_length=100)
    label = models.CharField(max_length=200, null=True, blank=True, verbose_name=_('Label'))
    description = models.TextField(null=True, blank=True, verbose_name=_('Description'))
    sequence = models.IntegerField(default=1)
    owner = models.ForeignKey(Account, null=True, on_delete=models.SET_NULL)
    privacy = models.CharField(max_length=20, choices=privacy_types, default="owner")

    history_seq = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('history_seq',)


def galley_type_choices():
    return (
        ('pdf', 'PDF'),
        ('epub', 'EPUB'),
        ('html', 'HTML'),
        ('xml', 'XML'),
        ('doc', 'Word (Doc)'),
        ('docx', 'Word (DOCX)'),
        ('odt', 'OpenDocument Text Document'),
        ('tex', 'LaTeX'),
        ('rtf', 'RTF'),
        ('other', _('Other')),
        ('image', _('Image')),
    )


class Galley(AbstractLastModifiedModel):
    # Local Galley
    article = models.ForeignKey('submission.Article', null=True)
    file = models.ForeignKey(File)
    css_file = models.ForeignKey(File, related_name='css_file', null=True, blank=True, on_delete=models.SET_NULL)
    images = models.ManyToManyField(File, related_name='images', null=True, blank=True)
    xsl_file = models.ForeignKey('core.XSLFile', related_name='xsl_file', null=True, blank=True, on_delete=models.SET_NULL)
    public = models.BooleanField(
        default=True,
        help_text='Uncheck if the typeset file should not be publicly available after the article is published.'
    )

    # Remote Galley
    is_remote = models.BooleanField(default=False)
    remote_file = models.URLField(blank=True, null=True)

    # All Galleys
    label = models.CharField(
        max_length=400,
        help_text='Typeset file labels are displayed in download links and have the format "Download Label" eg. if '
                  'you set the label to be PDF the link will be Download PDF. If you want Janeway to set a label for '
                  'you, leave it blank.',
    )
    type = models.CharField(max_length=100, choices=galley_type_choices())
    sequence = models.IntegerField(default=0)

    def unlink_files(self):
        if self.file and self.file.article_id:
            self.file.unlink_file()
        for image_file in self.images.all():
            if  not image_file.images.exclude(galley=self).exists():
                image_file.unlink_file()

    def __str__(self):
        return "{0} ({1})".format(self.id, self.label)

    def render(self, recover=False):
        return files.render_xml(
            self.file, self.article,
            xsl_path=self.xsl_file.file.path,
            recover=recover,
        )

    def render_crossref(self):
        xsl_path = os.path.join(
                settings.BASE_DIR, 'transform', 'xsl',  files.CROSSREF_XSL)
        return files.render_xml(
                self.file, self.article,
                xsl_path=xsl_path
        )

    def has_missing_image_files(self, show_all=False):
        if not self.file.mime_type in files.MIMETYPES_WITH_FIGURES:
            return []

        xml_file_contents = self.file.get_file(self.article)

        souped_xml = BeautifulSoup(xml_file_contents, 'lxml')

        elements = {
            'img': 'src',
            'graphic': 'xlink:href',
            'inline-graphic': 'xlink:href',
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
                'article_download_galley',
                kwargs={"article_id": self.article.id, "galley_id": self.id}
            )
            contents = IMAGE_GALLEY_TEMPLATE.format(
                url=url,
                alt=self.label,
            )
            return contents

    def path(self):
        url = reverse('article_download_galley',
                      kwargs={'article_id': self.article.pk,
                              'galley_id': self.pk})
        return self.article.journal.site_url(path=url)

    @staticmethod
    def mimetypes_with_figures():
        return files.MIMETYPES_WITH_FIGURES

    def save(self, *args, **kwargs):
        if self.type == 'xml' and not self.xsl_file:
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
        storage=JanewayFileSystemStorage('files/xsl'))
    journal = models.ForeignKey("journal.Journal", on_delete=models.CASCADE,
                                blank=True, null=True)
    date_uploaded = models.DateTimeField(default=timezone.now)
    label = models.CharField(max_length=255,
        help_text="A label to help recognise this stylesheet",
        unique=True,
    )
    comments = models.TextField(blank=True, null=True)
    original_filename = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return "%s(%s@%s)" % (
            self.__class__.__name__, self.label, self.file.path)


def default_xsl():
    return XSLFile.objects.get(
            label=settings.DEFAULT_XSL_FILE_LABEL).pk


class SupplementaryFile(models.Model):
    file = models.ForeignKey(File)
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
            'article_download_supp_file',
            kwargs={
                'article_id': self.file.article.pk,
                'supp_file_id': self.pk,
            },
        )

        return self.file.article.journal.site_url(path=path)


class Task(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='task_content_type', null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    object = GenericForeignKey('content_type', 'object_id')

    title = models.CharField(max_length=300)
    description = models.TextField()
    complete_events = models.ManyToManyField('core.TaskCompleteEvents')
    link = models.TextField(null=True, blank=True, help_text='A url name, where the action of this task can undertaken')
    assignees = models.ManyToManyField(Account)
    completed_by = models.ForeignKey(Account, blank=True, null=True, related_name='completed_by')

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

        tasks_to_destroy = Task.objects.filter(complete_events__event_name=kwargs['event'],
                                               content_type=ContentType.objects.get_for_model(kwargs['task_obj']),
                                               object_id=kwargs['task_obj'].pk)

        for task in tasks_to_destroy:
            task.completed = timezone.now()
            task.save()

    def __str__(self):
        return "Task for {0} #{1}: {2}".format(self.content_type, self.object_id, self.title)


class TaskCompleteEvents(models.Model):
    event_name = models.CharField(max_length=300)

    def __str__(self):
        return self.event_name


class EditorialGroup(models.Model):
    name = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    journal = models.ForeignKey('journal.Journal')
    sequence = models.PositiveIntegerField()

    class Meta:
        ordering = ('sequence',)

    def next_member_sequence(self):
        orderings = [member.sequence for member in self.editorialgroupmember_set.all()]
        return max(orderings) + 1 if orderings else 0

    def members(self):
        return [member for member in self.editorialgroupmember_set.all()]


class EditorialGroupMember(models.Model):
    group = models.ForeignKey(EditorialGroup)
    user = models.ForeignKey(Account)
    sequence = models.PositiveIntegerField()

    class Meta:
        ordering = ('sequence',)


class Contacts(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,
                                     related_name='contact_content_type', null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    object = GenericForeignKey('content_type', 'object_id')

    name = models.CharField(max_length=300)
    email = models.EmailField()
    role = models.CharField(max_length=200)
    sequence = models.PositiveIntegerField(default=999)

    class Meta:
        verbose_name_plural = 'Journal Contacts'
        ordering = ('sequence', 'name')

    def __str__(self):
        return "{0}, {1} - {2}".format(self.name, self.object, self.role)


class Contact(models.Model):
    recipient = models.EmailField(max_length=200, verbose_name='Who would you like to contact')
    sender = models.EmailField(max_length=200, verbose_name=_('Your contact email address'))
    subject = models.CharField(max_length=300, verbose_name=_('Subject'))
    body = models.TextField(verbose_name=_('Your message'))
    client_ip = models.GenericIPAddressField()
    date_sent = models.DateField(auto_now_add=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='contact_c_t',
                                     null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    object = GenericForeignKey('content_type', 'object_id')


class DomainAlias(AbstractSiteModel):
    redirect = models.BooleanField(
            default=True,
            verbose_name="301",
            help_text="If enabled, the site will throw a 301 redirect to the "
                "master domain."
    )
    journal = models.ForeignKey('journal.Journal', blank=True, null=True)
    press = models.ForeignKey('press.Press', blank=True, null=True)

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
            raise ValidationError(
                    " One and only one of press or journal must be set")
        return super().save(*args, **kwargs)


BASE_ELEMENTS = [
    {'name': 'review',
     'handshake_url': 'review_home',
     'jump_url': 'review_in_review',
     'stage': submission_models.STAGE_UNASSIGNED,
     'article_url': True},
    {'name': 'copyediting',
     'handshake_url': 'copyediting',
     'jump_url': 'article_copyediting',
     'stage': submission_models.STAGE_EDITOR_COPYEDITING,
     'article_url': True},
    {'name': 'production',
     'handshake_url': 'production_list',
     'jump_url': 'production_article',
     'stage': submission_models.STAGE_TYPESETTING,
     'article_url': False},
    {'name': 'proofing',
     'handshake_url': 'proofing_list',
     'jump_url': 'proofing_article',
     'stage': submission_models.STAGE_PROOFING,
     'article_url': False},
    {'name': 'prepublication',
     'handshake_url': 'publish',
     'jump_url': 'publish_article',
     'stage': submission_models.STAGE_READY_FOR_PUBLICATION,
     'article_url': True}
]

BASE_ELEMENT_NAMES = [
    element.get('name') for element in BASE_ELEMENTS
]


class Workflow(models.Model):
    journal = models.ForeignKey('journal.Journal')
    elements = models.ManyToManyField('WorkflowElement')


class WorkflowElement(models.Model):
    journal = models.ForeignKey('journal.Journal')
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
        ordering = ('order', 'element_name')

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
    article = models.ForeignKey('submission.Article')
    element = models.ForeignKey(WorkflowElement)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ('timestamp',)

    def __str__(self):
        return '{0} {1}'.format(self.element.element_name, self.timestamp)


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
    content_type = models.ForeignKey(ContentType,
                                     on_delete=models.CASCADE,
                                     related_name='element_content_type',
                                     null=True)

    object_id = models.PositiveIntegerField(blank=True, null=True)
    object = GenericForeignKey('content_type', 'object_id')

    available_to_press = models.BooleanField(default=False, help_text='Determines if this element is '
                                                                      'available for the press.')

    # whether or not this item is active
    active = models.BooleanField(default=False)

    # whether or not this item has a configuration
    has_config = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Homepage Elements'
        ordering = ('sequence', 'name')
        unique_together = ('name', 'content_type', 'object_id')

    def __str__(self):
        return self.name


class LoginAttempt(models.Model):
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)


class AccessRequest(models.Model):
    journal = models.ForeignKey(
        'journal.Journal',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    repository = models.ForeignKey(
        'repository.Repository',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        'core.Account',
        on_delete=models.CASCADE,
    )
    role = models.ForeignKey(
        'core.Role',
        on_delete=models.CASCADE,
    )
    requested = models.DateTimeField(
        default=timezone.now,
    )
    processed = models.BooleanField(
        default=False,
    )
    text = models.TextField(
        blank=True,
        null=True,
    )
    evaluation_note = models.TextField(
        null=True,
        help_text='This note will be sent to the requester when you approve or decline their request.',
    )

    def __str__(self):
        return 'User {} requested {} permission for {}'.format(
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
        db_table = 'core_settingvalue_translation'


def log_hijack_started(sender, hijacker_id, hijacked_id, request, **kwargs):
    from utils import models as utils_models
    hijacker = Account.objects.get(pk=hijacker_id)
    hijacked = Account.objects.get(pk=hijacked_id)
    action = '{} ({}) has hijacked {} ({})'.format(
        hijacker.full_name(),
        hijacker.pk,
        hijacked.full_name(),
        hijacked.pk,
    )

    utils_models.LogEntry.add_entry(
        types='Hijack Start',
        description=action,
        level='Info',
        actor=hijacker,
        request=request,
        target=hijacked
    )


def log_hijack_ended(sender, hijacker_id, hijacked_id, request, **kwargs):
    from utils import models as utils_models
    hijacker = Account.objects.get(pk=hijacker_id)
    hijacked = Account.objects.get(pk=hijacked_id)
    action = '{} ({}) has released {} ({})'.format(
        hijacker.full_name(),
        hijacker.pk,
        hijacked.full_name(),
        hijacked.pk,
    )

    utils_models.LogEntry.add_entry(
        types='Hijack Release',
        description=action,
        level='Info',
        actor=hijacker,
        request=request,
        target=hijacked
    )


hijack_started.connect(log_hijack_started)
hijack_ended.connect(log_hijack_ended)
